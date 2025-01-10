from django.urls import path

from .views import AboutView, ContactView, EventView, HomeView

app_name = "event"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("event/", EventView.as_view(), name="event"),
    path("contact/", ContactView.as_view(), name="contact"),
]
