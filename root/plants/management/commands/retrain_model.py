import os
import random
import shutil
from datetime import datetime
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms as T
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from api import inference
from api.retrain import eligible_feedback
from plants.models import Feedback, Plant, TrainingRun

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class ImgDS(Dataset):
    def __init__(self, items, tf):
        self.items, self.tf = items, tf

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        # if a photo was deleted mid-training (user marked it wrong), use the next one
        n = len(self.items)
        for j in range(n):
            path, label = self.items[(i + j) % n]
            try:
                return self.tf(Image.open(path).convert("RGB")), label
            except (FileNotFoundError, OSError):
                continue
        raise RuntimeError("No readable training images left")


def readable(path):
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


class Command(BaseCommand):
    help = "Fine-tune the classifier head on confirmed user feedback (safe: keeps the old model if the new one is worse)"

    def add_arguments(self, parser):
        parser.add_argument("--run-id", type=int, default=None)

    def handle(self, *args, **opts):
        run = None
        if opts["run_id"]:
            run = TrainingRun.objects.filter(pk=opts["run_id"]).first()
        run = run or TrainingRun.objects.create()
        try:
            self._train(run)
        except Exception as e:
            run.status = "failed"
            run.message = f"{type(e).__name__}: {e}"
            run.finished = timezone.now()
            run.save()
            raise

    def _finish(self, run, status, message, **fields):
        run.status, run.message, run.finished = status, message, timezone.now()
        for k, v in fields.items():
            setattr(run, k, v)
        run.save()
        self.stdout.write(f"[{status}] {message}")

    @torch.inference_mode()
    def _accuracy(self, model, loader, dev):
        correct = total = 0
        for x, y in loader:
            pred = model(x.to(dev)).argmax(1).cpu()
            correct += (pred == y).sum().item()
            total += len(y)
        return correct / total if total else 0.0

    def _save(self, model, ckpt, tmp):
        state = {k: v.cpu() for k, v in model.state_dict().items()}
        key, _ = inference.extract_state(ckpt)
        if isinstance(ckpt, nn.Module):
            torch.save(model.cpu(), tmp)
        elif key:
            new = dict(ckpt)
            new[key] = state
            torch.save(new, tmp)
        else:
            torch.save(state, tmp)

    def _train(self, run):
        dev = inference.device()
        torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))
        random.seed(42)
        torch.manual_seed(42)
        offset = settings.CLASS_INDEX_OFFSET

        new_fb = list(eligible_feedback().select_related("plant", "identification"))
        if not new_fb:
            return self._finish(run, "rejected", "No new eligible feedback.")
        new_ids = [fb.id for fb in new_fb]

        old_fb = Feedback.objects.filter(
            is_correct=True, used_for_training=True, plant__class_index__isnull=False
        ).select_related("plant", "identification")


        items = []
        for fb in list(new_fb) + list(old_fb):
            items.append((fb.identification.image.path, fb.plant.class_index - offset))

        for p in Plant.objects.exclude(reference_image="").filter(class_index__isnull=False):
            items.append((p.reference_image.path, p.class_index - offset))

        if settings.RETRAIN_REPLAY_DIR:
            for p in Plant.objects.filter(class_index__isnull=False):
                folder = Path(settings.RETRAIN_REPLAY_DIR) / p.slug
                if folder.is_dir():
                    files = [f for f in folder.iterdir() if f.suffix.lower() in EXTS]
                    random.shuffle(files)
                    items += [(str(f), p.class_index - offset)
                              for f in files[:settings.RETRAIN_REPLAY_PER_CLASS]]
        else:
            self.stdout.write(self.style.WARNING(
                "RETRAIN_REPLAY_DIR is not set: the model may forget plants that appear rarely in feedback."))


        model, ckpt = inference.load_checkpoint(settings.MODEL_PATH, dev)
        head = [m for m in model.modules() if isinstance(m, nn.Linear)][-1]
        items = [(p, l) for p, l in items if 0 <= l < head.out_features and readable(p)]

        random.shuffle(items)
        n_hold = max(5, int(len(items) * 0.2))
        hold, train = items[:n_hold], items[n_hold:]
        run.new_samples, run.total_samples = len(new_fb), len(items)
        if len(hold) < 5 or len(train) < 5:
            return self._finish(run, "rejected",
                                f"Only {len(items)} usable images; need at least 10 to train and validate safely.")

        eval_tf = T.Compose([
            T.Resize((settings.IMG_SIZE, settings.IMG_SIZE)), T.ToTensor(),
            T.Normalize(settings.NORM_MEAN, settings.NORM_STD)])
        train_tf = T.Compose([
            T.RandomResizedCrop(settings.IMG_SIZE, scale=(0.7, 1.0)),
            T.RandomHorizontalFlip(), T.ColorJitter(0.2, 0.2, 0.2),
            T.ToTensor(), T.Normalize(settings.NORM_MEAN, settings.NORM_STD)])
        bs = settings.RETRAIN_BATCH_SIZE
        train_loader = DataLoader(ImgDS(train, train_tf), batch_size=bs, shuffle=True)
        hold_loader = DataLoader(ImgDS(hold, eval_tf), batch_size=bs)

        acc_old = self._accuracy(model, hold_loader, dev)
        self.stdout.write(f"Holdout accuracy before: {acc_old:.3f}  ({len(hold)} images)")


        for p in model.parameters():
            p.requires_grad = False
        for p in head.parameters():
            p.requires_grad = True
        model.eval()

        opt = torch.optim.AdamW(head.parameters(), lr=settings.RETRAIN_LR, weight_decay=1e-2)
        loss_fn = nn.CrossEntropyLoss(label_smoothing=0.1)
        for epoch in range(settings.RETRAIN_EPOCHS):
            running = 0.0
            for x, y in train_loader:
                x, y = x.to(dev), y.to(dev)
                opt.zero_grad()
                loss = loss_fn(model(x), y)
                loss.backward()
                opt.step()
                running += loss.item() * len(y)
            self.stdout.write(f"  epoch {epoch + 1}/{settings.RETRAIN_EPOCHS}  loss {running / len(train):.4f}")

        acc_new = self._accuracy(model, hold_loader, dev)
        self.stdout.write(f"Holdout accuracy after:  {acc_new:.3f}")

        if acc_new + settings.RETRAIN_MAX_ACCURACY_DROP < acc_old:
            return self._finish(run, "rejected",
                                f"New model was worse ({acc_new:.3f} vs {acc_old:.3f}); kept the old one.",
                                acc_before=acc_old, acc_after=acc_new)

        path = Path(settings.MODEL_PATH)
        backups = path.parent / "backups"
        backups.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, backups / f"{path.stem}_{stamp}{path.suffix}")

        tmp = path.with_suffix(path.suffix + ".new")
        self._save(model, ckpt, tmp)
        os.replace(tmp, path)

        for old in sorted(backups.glob(f"{path.stem}_*{path.suffix}"))[:-settings.RETRAIN_KEEP_BACKUPS]:
            old.unlink()

        Feedback.objects.filter(id__in=new_ids).update(used_for_training=True)
        self._finish(run, "success",
                     f"Model updated ({acc_old:.3f} -> {acc_new:.3f}) using {len(new_fb)} new photos.",
                     acc_before=acc_old, acc_after=acc_new)