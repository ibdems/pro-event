from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    # Vue principale du tableau de bord
    path("", views.dashboard_home, name="home"),
    # Gestion des événements
    path("events/", views.event_list, name="event_list"),
    path("events/add/", views.event_add, name="event_add"),
    path("events/<uuid:uid>/edit/", views.event_edit, name="event_edit"),
    path("events/<uuid:uid>/delete/", views.event_delete, name="event_delete"),
    # Gestion des demandes
    path("demandes/", views.demande_list, name="demande_list"),
    path("demandes/<uuid:uid>/detail/", views.demande_detail, name="demande_detail"),
    path("demandes/<uuid:uid>/accept/", views.demande_accept, name="demande_accept"),
    path("demandes/<uuid:uid>/reject/", views.demande_reject, name="demande_reject"),
    # Gestion des tickets
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/<str:code>/detail/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<str:code>/print/", views.ticket_print, name="ticket_print"),
    # Gestion des contacts
    path("contacts/", views.contact_list, name="contact_list"),
    path("contacts/<int:pk>/detail/", views.contact_detail, name="contact_detail"),
    path("contacts/<int:pk>/mark-read/", views.contact_mark_read, name="contact_mark_read"),
    # Gestion des utilisateurs (organisateurs)
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_add, name="user_add"),
    path("users/<int:pk>/detail/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    # Paramètres du système
    path("settings/general/", views.settings_general, name="settings_general"),
    path("settings/email/", views.settings_email, name="settings_email"),
    path("settings/payment/", views.settings_payment, name="settings_payment"),
    path("settings/seo/", views.settings_seo, name="settings_seo"),
    path("settings/backup/", views.settings_backup, name="settings_backup"),
    path("settings/system/", views.settings_system, name="settings_system"),
    path("settings/reset/", views.settings_reset, name="settings_reset"),
    path(
        "email-templates/<str:template>/edit/",
        views.email_template_edit,
        name="email_template_edit",
    ),
    # Statistiques et rapports
    path("stats/", views.stats_view, name="stats"),
    path("reports/", views.reports_view, name="reports"),
    # Profil de l'utilisateur connecté
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
]
