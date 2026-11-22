import subprocess
import sys
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from plants.models import Feedback, TrainingRun


def eligible_feedback():
    """Confirmed-correct photos not yet trained on (skips ones the model was already very sure about)."""
    qs = Feedback.objects.filter(
        is_correct=True,
        used_for_training=False,
        plant__isnull=False,
        plant__class_index__isnull=False,
    ).exclude(confidence__gte=settings.RETRAIN_MAX_CONFIDENCE)
    if settings.RETRAIN_REQUIRE_APPROVAL:
        qs = qs.filter(approved=True)
    return qs


def maybe_start_retraining():
    """Starts a background training process if enough new feedback exists. Returns True if started."""
    if not settings.RETRAIN_ENABLED:
        return False
    if eligible_feedback().count() < settings.RETRAIN_MIN_NEW_SAMPLES:
        return False

    now = timezone.now()
    with transaction.atomic():
        busy = TrainingRun.objects.filter(
            status="running", started__gte=now - timedelta(hours=2)).exists()
        recent = TrainingRun.objects.filter(
            started__gte=now - timedelta(minutes=settings.RETRAIN_COOLDOWN_MINUTES)).exists()
        if busy or recent:
            return False
        run = TrainingRun.objects.create()

    log_path = settings.BASE_DIR / "ml_models" / "retrain.log"
    with open(log_path, "a", encoding="utf-8") as log:
        subprocess.Popen(
            [sys.executable, str(settings.BASE_DIR / "manage.py"),
             "retrain_model", "--run-id", str(run.id)],
            cwd=settings.BASE_DIR,
            stdout=log,
            stderr=log,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    return True