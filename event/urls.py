from django.urls import path

from .views import (
    AboutView,
    ContactView,
    DetailEventView,
    EventAddView,
    EventView,
    HomeView,
    ScanCodeView,
    TicketView,
)

app_name = "event"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("event/", EventView.as_view(), name="event"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("event/detail/<uid>", DetailEventView.as_view(), name="event_detail"),
    path("event/add/", EventAddView.as_view(), name="event_add"),
    path("event/ticket/", TicketView.as_view(), name="ticket"),
    path("event/<str:event_id>/scan/", ScanCodeView.as_view(), name="scan_code"),
]
