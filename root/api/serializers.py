from rest_framework import serializers
from plants.models import Feedback, Identification, Plant


def _items(text, split_commas=False):
    """Turn a text box into a list: one item per line (optionally also per comma)."""
    text = text or ""
    if split_commas:
        text = text.replace(",", "\n")
    return [line.strip() for line in text.splitlines() if line.strip()]


class PlantSerializer(serializers.ModelSerializer):
    uses = serializers.SerializerMethodField()
    parts_used = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Plant
        fields = ["id", "slug", "scientific_name", "common_name", "local_name", "family",
                  "description", "uses", "parts_used", "properties", "habitat",
                  "precautions", "image"]

    def get_uses(self, obj):
        return _items(obj.ayurvedic_uses)

    def get_parts_used(self, obj):
        return _items(obj.parts_used, split_commas=True)

    def get_image(self, obj):
        if not obj.reference_image:
            return None
        url = obj.reference_image.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class FeedbackSerializer(serializers.ModelSerializer):
    identification_id = serializers.PrimaryKeyRelatedField(
        source="identification", queryset=Identification.objects.all())
    plant_id = serializers.PrimaryKeyRelatedField(
        source="plant", queryset=Plant.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Feedback
        fields = ["identification_id", "plant_id", "is_correct"]