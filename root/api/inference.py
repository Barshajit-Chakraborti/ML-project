import threading
from pathlib import Path

import torch
from torch import nn
from torchvision import models, transforms as T
from django.conf import settings

STATE_KEYS = ("model_state_dict", "model_state", "state_dict", "model")


class ModelNotAvailable(Exception):
    pass


_lock = threading.Lock()
_model = None
_transform = None
_loaded_mtime = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def device():
    return _device


def extract_state(ckpt):
    """Returns (key_holding_the_weights_or_None, state_dict)."""
    if isinstance(ckpt, dict):
        for key in STATE_KEYS:
            if key in ckpt and isinstance(ckpt[key], dict):
                return key, ckpt[key]
    return None, ckpt


def _infer_num_classes(state):
    for key in reversed(list(state.keys())):
        if key.endswith(".weight") and state[key].ndim == 2:
            return state[key].shape[0]
    raise ModelNotAvailable("Could not infer number of classes from checkpoint")


def _build(arch, num_classes):
    m = getattr(models, arch)(weights=None)
    if hasattr(m, "classifier"):
        if isinstance(m.classifier, nn.Sequential):
            i = len(m.classifier) - 1
            m.classifier[i] = nn.Linear(m.classifier[i].in_features, num_classes)
        else:
            m.classifier = nn.Linear(m.classifier.in_features, num_classes)
    elif hasattr(m, "fc"):
        m.fc = nn.Linear(m.fc.in_features, num_classes)
    else:
        raise ModelNotAvailable(f"Don't know how to replace the head of '{arch}'")
    return m


def load_checkpoint(path, dev=None):
    """Returns (model_in_eval_mode, raw_checkpoint). Used by the API and by retrain_model."""
    dev = dev or _device
    path = Path(path)
    if not path.exists():
        raise ModelNotAvailable(f"Model file not found at {path}")

    try:
        ckpt = torch.load(path, map_location=dev, weights_only=True)
    except Exception:
        # only for files you trust (your own training output)
        ckpt = torch.load(path, map_location=dev, weights_only=False)

    if isinstance(ckpt, nn.Module):
        model = ckpt
    else:
        _, state = extract_state(ckpt)
        state = {k.replace("module.", "", 1): v for k, v in state.items()}
        arch = (ckpt.get("arch") if isinstance(ckpt, dict) else None) or settings.MODEL_ARCH
        model = _build(arch, _infer_num_classes(state))
        model.load_state_dict(state)
    return model.to(dev).eval(), ckpt


def _mtime(path):
    return path.stat().st_mtime if path.exists() else None


def get_model():
    """Loads the model once, and reloads it automatically if the weights file changes."""
    global _model, _transform, _loaded_mtime
    path = Path(settings.MODEL_PATH)
    if _model is not None and _mtime(path) == _loaded_mtime:
        return _model

    with _lock:
        mtime = _mtime(path)
        if _model is not None and mtime == _loaded_mtime:
            return _model
        model, _ = load_checkpoint(path)
        _model, _loaded_mtime = model, mtime
        if _transform is None:
            _transform = T.Compose([
                T.Resize((settings.IMG_SIZE, settings.IMG_SIZE)),
                T.ToTensor(),
                T.Normalize(settings.NORM_MEAN, settings.NORM_STD),
            ])
    return _model


def is_loaded():
    return _model is not None


@torch.inference_mode()
def predict_topk(pil_image, k=3):
    """Returns [(class_id, probability), ...] best first."""
    model = get_model()
    x = _transform(pil_image).unsqueeze(0).to(_device)
    probs = torch.softmax(model(x), dim=1)[0]
    top = torch.topk(probs, min(k, probs.numel()))
    return [
        (int(i) + settings.CLASS_INDEX_OFFSET, float(p))
        for p, i in zip(top.values, top.indices)
    ]