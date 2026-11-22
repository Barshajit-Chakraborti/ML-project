from django.urls import path
from . import views

urlpatterns = [
    path("identify/", views.IdentifyView.as_view()),
    path("identifications/<int:pk>/", views.IdentificationDetailView.as_view()),
    path("plants/", views.PlantListView.as_view()),
    path("plants/<int:pk>/", views.PlantDetailView.as_view()),
    path("feedback/", views.FeedbackView.as_view()),
    path("health/", views.HealthView.as_view()),
]