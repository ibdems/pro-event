from django.urls import path

from event.views.contact import ContactView
from event.views.event import DetailEventView, EventView
from event.views.invitation import InvitationResponseView
from event.views.payments import paycard_callback
from event.views.public import (
    ConditionsUtilisationView,
    HomeView,
    MentionsLegalesView,
    PolitiqueConfidentialiteView,
)
from event.views.scan import (
    CheckTicketView,
    EventScannerAddView,
    EventScannerListView,
    EventScannerRemoveView,
    ScanCodeView,
)

app_name = "event"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("event/", EventView.as_view(), name="event"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("event/detail/<uid>", DetailEventView.as_view(), name="event_detail"),
    path("event/<str:event_id>/scan/", ScanCodeView.as_view(), name="scan_code"),
    path("check_ticket/<str:code>/", CheckTicketView.as_view(), name="check_ticket"),
    # URLs pour la gestion des scanners
    path("event/<str:event_id>/scanners/", EventScannerListView.as_view(), name="scanner_list"),
    path("event/<str:event_id>/scanners/add/", EventScannerAddView.as_view(), name="scanner_add"),
    path(
        "event/<str:event_id>/scanners/remove/",
        EventScannerRemoveView.as_view(),
        name="scanner_remove",
    ),
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
    path("mentions-legales/", MentionsLegalesView.as_view(), name="mentions_legales"),
    path(
        "conditions-utilisation/",
        ConditionsUtilisationView.as_view(),
        name="conditions_utilisation",
    ),
    path(
        "politique-confidentialite/",
        PolitiqueConfidentialiteView.as_view(),
        name="politique_confidentialite",
    ),
    path("paycard/return/<str:reference>/", paycard_callback, name="paycard_callback"),
]
