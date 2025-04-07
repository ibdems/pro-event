from django.urls import path

from dashboard.views.contact_views import (
    ContactDetailView,
    ContactListView,
    ContactMarkReadView,
)
from dashboard.views.demande_views import (
    DemandeAcceptView,
    DemandeDetailView,
    DemandeListView,
    DemandeRejectView,
)
from dashboard.views.event_views import (
    CategoryAddView,
    CategoryDeleteView,
    CategoryEditView,
    CategoryListView,
    EventActivateView,
    EventAddView,
    EventDeactivateView,
    EventDeleteView,
    EventDetailView,
    EventDownloadInvitationTemplateView,
    EventEditView,
    EventImportInvitationsView,
    EventListView,
    EventSendInvitationView,
    PartnerAddView,
    PartnerDeleteView,
    PartnerEditView,
    PartnerListView,
)
from dashboard.views.home_views import DashboardHomeView
from dashboard.views.misc_views import EmailTemplateEditView, ReportsView, StatsView
from dashboard.views.profile_views import ProfileEditView, ProfileView
from dashboard.views.ticket_views import (
    TicketDetailView,
    TicketListView,
    TicketMarkPaidView,
    TicketPrintView,
    TicketSendEmailView,
)
from dashboard.views.user_views import (
    UserAddView,
    UserDeleteView,
    UserDetailView,
    UserEditView,
    UserListView,
)

app_name = "dashboard"

urlpatterns = [
    # Vue principale du tableau de bord
    path("", DashboardHomeView.as_view(), name="home"),
    # Gestion des événements
    path("events/", EventListView.as_view(), name="event_list"),
    path("events/add/", EventAddView.as_view(), name="event_add"),
    path("events/<uuid:uid>/edit/", EventEditView.as_view(), name="event_edit"),
    path("events/<uuid:uid>/delete/", EventDeleteView.as_view(), name="event_delete"),
    path("events/<uuid:uid>/detail/", EventDetailView.as_view(), name="event_detail"),
    path("events/<uuid:uid>/activate/", EventActivateView.as_view(), name="event_activate"),
    path("events/<uuid:uid>/deactivate/", EventDeactivateView.as_view(), name="event_deactivate"),
    # Gestion des invitations pour les événements privés
    path(
        "events/<uuid:uid>/invitations/",
        EventDetailView.as_view(template_name="dashboard/events/invitations.html"),
        name="event_invitations",
    ),
    path(
        "events/<uuid:uid>/send-invitation/",
        EventSendInvitationView.as_view(),
        name="event_send_invitation",
    ),
    path(
        "events/<uuid:uid>/import-invitations/",
        EventImportInvitationsView.as_view(),
        name="event_import_invitations",
    ),
    path(
        "invitations/download-template/",
        EventDownloadInvitationTemplateView.as_view(),
        name="event_download_invitation_template",
    ),
    # Gestion des catégories
    path("events/categories/", CategoryListView.as_view(), name="category_list"),
    path("events/categories/add/", CategoryAddView.as_view(), name="category_add"),
    path("events/categories/<int:pk>/edit/", CategoryEditView.as_view(), name="category_edit"),
    path(
        "events/categories/<int:pk>/delete/", CategoryDeleteView.as_view(), name="category_delete"
    ),
    # Gestion des partenaires
    path("events/partners/", PartnerListView.as_view(), name="partner_list"),
    path("events/partners/add/", PartnerAddView.as_view(), name="partner_add"),
    path("events/partners/<int:pk>/edit/", PartnerEditView.as_view(), name="partner_edit"),
    path("events/partners/<int:pk>/delete/", PartnerDeleteView.as_view(), name="partner_delete"),
    # Gestion des demandes
    path("demandes/", DemandeListView.as_view(), name="demande_list"),
    path("demandes/<uuid:uid>/detail/", DemandeDetailView.as_view(), name="demande_detail"),
    path("demandes/<uuid:uid>/accept/", DemandeAcceptView.as_view(), name="demande_accept"),
    path("demandes/<uuid:uid>/reject/", DemandeRejectView.as_view(), name="demande_reject"),
    # Gestion des tickets
    path("tickets/", TicketListView.as_view(), name="ticket_list"),
    path("tickets/<str:code>/detail/", TicketDetailView.as_view(), name="ticket_detail"),
    path("tickets/<str:code>/print/", TicketPrintView.as_view(), name="ticket_print"),
    path("tickets/<str:code>/mark-paid/", TicketMarkPaidView.as_view(), name="ticket_mark_paid"),
    path(
        "tickets/<int:ticket_id>/send-email/",
        TicketSendEmailView.as_view(),
        name="ticket_send_email",
    ),
    path(
        "tickets/payment/<int:payement_id>/send-email/",
        TicketSendEmailView.as_view(),
        name="ticket_send_email_payment",
    ),
    # Gestion des contacts
    path("contacts/", ContactListView.as_view(), name="contact_list"),
    path("contacts/<int:pk>/detail/", ContactDetailView.as_view(), name="contact_detail"),
    path("contacts/<int:pk>/mark-read/", ContactMarkReadView.as_view(), name="contact_mark_read"),
    # Gestion des utilisateurs (organisateurs)
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/add/", UserAddView.as_view(), name="user_add"),
    path("users/<int:pk>/detail/", UserDetailView.as_view(), name="user_detail"),
    path("users/<int:pk>/edit/", UserEditView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),
    # Paramètres du système
    # path("settings/general/", views.settings_general, name="settings_general"),
    # path("settings/email/", views.settings_email, name="settings_email"),
    # path("settings/payment/", views.settings_payment, name="settings_payment"),
    # path("settings/seo/", views.settings_seo, name="settings_seo"),
    # path("settings/backup/", views.settings_backup, name="settings_backup"),
    # path("settings/system/", views.settings_system, name="settings_system"),
    # path("settings/reset/", views.settings_reset, name="settings_reset"),
    path(
        "email-templates/<str:template>/edit/",
        EmailTemplateEditView.as_view(),
        name="email_template_edit",
    ),
    # Statistiques et rapports
    path("stats/", StatsView.as_view(), name="stats"),
    path("reports/", ReportsView.as_view(), name="reports"),
    # Profil de l'utilisateur connecté
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
]
