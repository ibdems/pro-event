from django.contrib import admin
from users.models import User
from django.utils.html import format_html

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'contact', 'role','is_active', 'is_staff', 'display_photo')
    list_filter = ('is_active', 'is_staff', 'role', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'contact')
    ordering = ('-created_at',)
    fieldsets = (
        ('Info de la Personne', {'fields': ('email', 'first_name', 'last_name', 'contact', 'adresse', 'photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'role', 'groups', 'user_permissions')}),
    )

    def display_photo(self, obj):
        if obj.photo:
            return format_html('<img src= "{}" width="50" height="50" />', obj.photo.url)
        return "X"
    display_photo.short_description = 'Photo'