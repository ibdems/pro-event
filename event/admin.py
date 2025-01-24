from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.utils.html import format_html

from .models import Category, Event, Partner, Payement, Ticket


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "event_count")
    search_fields = ("name",)

    def event_count(self, obj):
        return obj.event_set.count()

    event_count.short_description = "Nombre d'événements"


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    list_display = ("name", "partnership_type", "display_logo", "created_at")
    list_filter = ("partnership_type", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "update_at")

    def display_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "Pas de logo"

    display_logo.short_description = "Logo"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "category",
        "start_date",
        "type_event",
        "type_access",
        "total_capacity",
        "prix_normal",
        "prix_vip",
        "prix_vvip",
        "available_capacity",
        "statut",
    )
    list_filter = ("type_event", "type_access", "statut", "category", "start_date")
    search_fields = ("title", "description", "location", "user__email")
    readonly_fields = ("uid", "created_at", "update_at")
    filter_horizontal = ("partner",)
    # form = EventForms
    list_per_page = 10
    fieldsets = (
        (
            "Informations de base",
            {
                "fields": (
                    "category",
                    "title",
                    "description",
                    "image",
                )
            },
        ),
        (
            "Détails de l'événement",
            {"fields": ("start_date", "end_date", "location", "type_event", "type_access")},
        ),
        ("Capacité", {"fields": ("normal_capacity", "vip_capacity", "vvip_capacity")}),
        ("Prix", {"fields": ("prix_normal", "prix_vip", "prix_vvip")}),
        ("Partenaires et statut", {"fields": ("partner", "statut")}),
    )
    actions = ["activate_event", "deactivate_event"]

    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 3, "style": "width: 100%;"})},
    }

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        return super().save_model(request, obj, form, change)

    def activate_event(self, request, queryset):
        queryset.update(statut=True)

    activate_event.short_description = "Activer les événements sélectionnés"

    def deactivate_event(self, request, queryset):
        queryset.update(statut=False)

    deactivate_event.short_description = "Désactiver les événements sélectionnés"


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "code_ticket",
        "event",
        "payement",
        "scan_count",
        "created_at",
        "display_qr_code",
        "type_ticket",
    )
    list_filter = ("created_at", "event")
    search_fields = ("code_ticket", "payement")
    readonly_fields = ("code_ticket", "qr_code", "created_at", "update_at", "scan_count")
    list_per_page = 10

    fieldsets = (
        (
            "Informations du ticket",
            {"fields": ("code_ticket", "event", "type_ticket", "ticket_pdf")},
        ),
    )

    def display_qr_code(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="100" height="100" />', obj.qr_code.url)
        return "Pas de QR Code"

    display_qr_code.short_description = "QR Code"


@admin.register(Payement)
class PayementAdmin(admin.ModelAdmin):
    list_display = (
        "reference_payement",
        "amount",
        "nom_complet",
        "email_reception",
        "telephone_payement",
        "telephone_reception",
        "payment_method",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("reference_payement",)
    readonly_fields = ("reference_payement", "created_at", "update_at")

    # ticket_count.short_description = "Nombre de tickets"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("amount",)
        return self.readonly_fields
