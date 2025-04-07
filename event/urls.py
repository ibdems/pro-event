from django.urls import path

from .views import (
    AboutView,
    CheckTicketView,
    ContactView,
    DetailEventView,
    EventAddView,
    EventView,
    HomeView,
    InvitationResponseView,
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
    path("check_ticket/<str:code>/", CheckTicketView.as_view(), name="check_ticket"),
    path(
        "invitation/<str:token>/accept/",
        InvitationResponseView.as_view(),
        {"action": "accept"},
        name="accept_invitation",
    ),
    path(
        "invitation/<str:token>/decline/",
        InvitationResponseView.as_view(),
        {"action": "decline"},
        name="decline_invitation",
    ),
]
