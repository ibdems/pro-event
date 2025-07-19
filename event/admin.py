from django.contrib import admin

from .models import (
    Category,
    Contact,
    Event,
    EventScanner,
    InfoTicket,
    Invitation,
    Partner,
    Payement,
    Ticket,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "partnership_type", "is_platform_partner", "created_at")
    list_filter = ("partnership_type", "is_platform_partner")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "update_at")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "start_date",
        "end_date",
        "location",
        "statut",
        "type_event",
    )
    list_filter = ("category", "statut", "type_event", "created_at")
    search_fields = ("title", "description", "location")
    readonly_fields = ("uid", "created_at", "updated_at")
    filter_horizontal = ("partner",)


@admin.register(InfoTicket)
class InfoTicketAdmin(admin.ModelAdmin):
    list_display = ("event", "type_access", "total_capacity", "created_at")
    list_filter = ("type_access", "created_at")
    search_fields = ("event__title",)
    readonly_fields = ("uid", "created_at", "updated_at")


@admin.register(Payement)
class PayementAdmin(admin.ModelAdmin):
    list_display = (
        "reference_payement",
        "nom_complet",
        "event",
        "payment_method",
        "statut_payement",
        "amount",
        "created_at",
    )
    list_filter = ("payment_method", "statut_payement", "created_at")
    search_fields = ("reference_payement", "nom_complet", "event__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("code_ticket", "event", "type_ticket", "scan_count", "created_at")
    list_filter = ("type_ticket", "created_at")
    search_fields = ("code_ticket", "event__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at",)
    actions = ["mark_as_read", "mark_as_unread"]

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    mark_as_read.short_description = "Marquer comme lu"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)

    mark_as_unread.short_description = "Marquer comme non lu"


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "event", "ticket_type", "status", "created_at")
    list_filter = ("ticket_type", "status", "created_at")
    search_fields = ("name", "email", "event__title")
    readonly_fields = ("uid", "token", "created_at", "updated_at")


@admin.register(EventScanner)
class EventScannerAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "is_active", "created_by", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name", "event__title")
    readonly_fields = ("created_at",)
    list_editable = ("is_active",)
