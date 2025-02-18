from django.urls import path

from .views import DemandeView

urlpatterns = [
    path("event/demande/", DemandeView.as_view(), name="demande"),
]
