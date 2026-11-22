from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Plant(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    class_index = models.IntegerField(unique=True, null=True, blank=True)
    scientific_name = models.CharField(max_length=200)
    common_name = models.CharField(max_length=200, blank=True)
    local_name = models.CharField(max_length=200, blank=True)
    family = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    ayurvedic_uses = models.TextField(blank=True, help_text="One use per line")
    parts_used = models.TextField(blank=True, help_text="One part per line (or comma-separated)")
    properties = models.TextField(blank=True)
    habitat = models.TextField(blank=True)
    precautions = models.TextField(blank=True)
    reference_image = models.ImageField(upload_to="plants/", blank=True)

    class Meta:
        ordering = ["scientific_name"]

    def __str__(self):
        return f"{self.slug} - {self.scientific_name}"


class Identification(models.Model):
    """One uploaded photo and what the model predicted for it."""
    image = models.ImageField(upload_to="identifications/")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    predictions = models.JSONField(default=list, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Identification #{self.pk}"


class Feedback(models.Model):
    identification = models.ForeignKey(Identification, on_delete=models.CASCADE, related_name="feedback")
    plant = models.ForeignKey(Plant, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    is_correct = models.BooleanField()
    confidence = models.FloatField(null=True, blank=True,
                                   help_text="Model confidence for this plant when feedback was given")
    approved = models.BooleanField(default=False,
                                   help_text="Reviewed by an admin (used when RETRAIN_REQUIRE_APPROVAL is on)")
    used_for_training = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback #{self.pk} ({'correct' if self.is_correct else 'incorrect'})"


class TrainingRun(models.Model):
    STATUS = [
        ("running", "Running"),
        ("success", "Success - model updated"),
        ("rejected", "Rejected - kept old model"),
        ("failed", "Failed"),
    ]
    status = models.CharField(max_length=10, choices=STATUS, default="running")
    started = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(null=True, blank=True)
    new_samples = models.IntegerField(default=0)
    total_samples = models.IntegerField(default=0)
    acc_before = models.FloatField(null=True, blank=True)
    acc_after = models.FloatField(null=True, blank=True)
    message = models.TextField(blank=True)

    def __str__(self):
        return f"Run #{self.pk} - {self.status}"

@receiver(post_delete, sender=Identification)
def delete_identification_photo(sender, instance, **kwargs):
    """Remove the photo file from disk whenever an Identification row is deleted."""
    if instance.image:
        transaction.on_commit(lambda: instance.image.delete(save=False))