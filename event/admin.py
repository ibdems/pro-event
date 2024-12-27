from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import Category, Partner, Event, Ticket, Payement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_count')
    search_fields = ('name',)

    def event_count(self, obj):
        return obj.event_set.count
    event_count.short_description = "Nombre d'évenements"

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
     list_display = ('name', 'partnership_type', 'display_logo', 'created_at')
     list_filter = ('partnership_type', 'created_at')
     search_fields = ('name', 'description')
     readonly_fields = ('created_at', 'update_at')

     def display_logo(self, obj):
        if obj.logo:
             return format_html('<img src= "{}" width="50" height="50" />', obj.logo.url)
        return 'No logo'
     display_logo.short_desacription = 'Logo'

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display =  ('title', 'user', 'category', 'start_date', 'type_event', 'type_access', 'total_capacity', 'available_capacity', 'statut')
    list_filter = ('type_event', 'type_access', 'statut', 'category', 'start_date')
    search_fields = ('title', 'description', 'location', 'user__email')
    readonly_fields = ('uid', 'created_at', 'update_at')
    filter_horizontal = ('partner',)
    fieldsets = (
        ('Information Basique', {
            'fields': ('title', 'description', 'image', 'user', 'category')
        }),
        ("Detail de l'evenement", {
            'fields': ('start_date', 'end_date', 'location', 'type_event', 'type_access')
        }),
        ('Capacité', {
            'fields': ('normal_capacity', 'vip_capacity', 'vvip_capacity')
        }),
        ('Partners & Status', {
            'fields': ('partner', 'statut')
        }),
    )
    actions = ['activate_event', 'deactivate_event']

    def activate_event(self, request, queryset):
        queryset.update(statut=True)
    activate_event.short_description = 'Evenements activés!'

    def deactivate_event(self, request, queryset):
        queryset.update(statut=False)
    deactivate_event.short_description = 'Evenements desactivés'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('code_ticket', 'event', 'email_reception', 'telephone_payement', 'statut_payement', 'scan_count', 'created_at')
    list_filter = ('statut_payement', 'created_at', 'event')
    search_fields = ('code_ticket', 'email_reception', 'telephone_payement', 'telephone_reception')
    readonly_fields = ('code_ticket', 'qr_code', 'created_at', 'update_at', 'scan_count')

    fieldsets = (
        ('Information du ticket', {
            'fields': ('code_ticket', 'event', 'qr_code')
        }),
        ('Information du contact', {
            'fields': ('email_reception', 'telephone_payement', 'telephone_reception')
        }),
        ('Prix', {
            'fields': ('prix_normal', 'prix_vip', 'prix_vvip')
        }),
        ('Status', {
            'fields': ('statut_payement', 'scan_count')
        })
    )

    def display_qr_code(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="100" height="100" />', obj.qr_code.url)
        return "No QR Code"
    display_qr_code.short_description = 'QR Code'


@admin.register(Payement)
class PayementAdmin(admin.ModelAdmin):
    list_display = ('reference_payement', 'amount', 'ticket_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('reference_payement',)
    readonly_fields = ('reference_payement', 'created_at', 'update_at')
    filter_horizontal = ('tickets',)

    def ticket_count(self, obj):
        return obj.tickets.count()
    ticket_count.short_description = 'Nombre de tickets'

    def get_readonly_fields(self, request, obj=None):
        if obj: 
            return self.readonly_fields + ('amount',)
        return self.readonly_fields
