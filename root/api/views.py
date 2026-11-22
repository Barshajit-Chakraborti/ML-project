from PIL import Image, UnidentifiedImageError
from django.conf import settings
from rest_framework import filters, generics
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from plants.models import Feedback, Identification, Plant
from .retrain import maybe_start_retraining
from .inference import ModelNotAvailable, get_model, is_loaded, predict_topk
from .serializers import FeedbackSerializer, PlantSerializer

DISCLAIMER = ("Prototype for learning only. Never eat or use a plant "
              "based on this result.")


def _coord(value, limit):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if -limit <= v <= limit else None


class IdentifyView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        f = request.FILES.get("image")
        if not f:
            return Response({"detail": "No image provided (field name must be 'image')."}, status=400)
        if f.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
            return Response({"detail": f"Image too large (max {settings.MAX_UPLOAD_MB}MB)."}, status=400)

        try:
            img = Image.open(f).convert("RGB")
        except (UnidentifiedImageError, OSError):
            return Response({"detail": "That file is not a valid image."}, status=400)
        f.seek(0)  # rewind so the file can be saved below

        try:
            preds = predict_topk(img, k=settings.TOP_K)
        except ModelNotAvailable as e:
            return Response({"detail": str(e)}, status=503)

        plants = Plant.objects.in_bulk([cid for cid, _ in preds], field_name="class_index")
        predictions = [
            {
                "plant_id": plants[cid].id,
                "scientific_name": plants[cid].scientific_name,
                "common_name": plants[cid].common_name,
                "confidence": round(prob, 4),
            }
            for cid, prob in preds if cid in plants
        ]
        if not predictions:
            return Response(
                {"detail": "The prediction has no matching plant in the database. "
                           "Did you run load_class_map?"}, status=404)

        ident = Identification.objects.create(
            image=f,
            latitude=_coord(request.data.get("latitude"), 90),
            longitude=_coord(request.data.get("longitude"), 180),
            predictions=predictions,
        )
        return Response({
            "id": ident.id,
            "predictions": predictions,
            "matched": predictions[0]["confidence"] >= settings.CONFIDENCE_THRESHOLD,
            "disclaimer": DISCLAIMER,
        })


class IdentificationDetailView(APIView):
    def get(self, request, pk):
        try:
            ident = Identification.objects.get(pk=pk)
        except Identification.DoesNotExist:
            return Response({"detail": "Identification not found."}, status=404)
        return Response({
            "id": ident.id,
            "predictions": ident.predictions,
            "image": request.build_absolute_uri(ident.image.url),
            "created": ident.created,
            "disclaimer": DISCLAIMER,
        })


class PlantListView(generics.ListAPIView):
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["scientific_name", "common_name", "local_name", "slug"]


class PlantDetailView(generics.RetrieveAPIView):
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer


class FeedbackView(APIView):
    """POST /api/feedback/  json: {identification_id, plant_id, is_correct}"""
    parser_classes = [JSONParser]

    def post(self, request):
        ser = FeedbackSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {"detail": "Could not record feedback. The photo may already have been removed.",
                 "errors": ser.errors},
                status=400,
            )

        ident = ser.validated_data["identification"]
        plant = ser.validated_data.get("plant")
        is_correct = ser.validated_data["is_correct"]

        # Wrong prediction: delete everything about this upload (photo, prediction, feedback)
        if not is_correct:
            ident.delete()
            return Response({"ok": True, "deleted": True})

        # Correct prediction: keep it, remember the model's confidence for the confirmed plant
        confidence = next(
            (p["confidence"] for p in ident.predictions if plant and p["plant_id"] == plant.id),
            None,
        )
        fb = Feedback.objects.filter(identification=ident).order_by("-id").first()
        if fb is None:
            fb = Feedback(identification=ident)
        fb.plant, fb.is_correct, fb.confidence = plant, True, confidence
        fb.save()

        started = maybe_start_retraining()
        return Response({"ok": True, "deleted": False, "retraining_started": started}, status=201)
    

class HealthView(APIView):
    """GET /api/health/"""
    def get(self, request):
        try:
            get_model()
        except ModelNotAvailable as e:
            return Response({"status": "degraded", "model_loaded": False, "detail": str(e)})
        return Response({
            "status": "ok",
            "model_loaded": is_loaded(),
            "plants_in_db": Plant.objects.count(),
        })