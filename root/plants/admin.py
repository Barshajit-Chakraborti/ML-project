from django.contrib import admin
from .models import Plant, Identification, Feedback, TrainingRun


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ("class_index", "slug", "scientific_name", "common_name", "local_name")
    search_fields = ("slug", "scientific_name", "common_name", "local_name")
    ordering = ("class_index",)


@admin.register(Identification)
class IdentificationAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "latitude", "longitude")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "identification", "plant", "is_correct", "confidence",
                    "approved", "used_for_training", "created")
    list_filter = ("is_correct", "approved", "used_for_training")
    list_editable = ("approved",)


@admin.register(TrainingRun)
class TrainingRunAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "started", "finished", "new_samples",
                    "total_samples", "acc_before", "acc_after")
    readonly_fields = [f.name for f in TrainingRun._meta.fields]