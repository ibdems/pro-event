from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.defaults import page_not_found, server_error


# Configuration des gestionnaires d'erreurs personnalisés
def custom_404(request, exception=None):
    return page_not_found(request, exception, template_name="404.html")


def custom_500(request):
    return server_error(request, template_name="500.html")


urlpatterns = [
    path("proevent/", admin.site.urls),
    path("accounts/", include("users.urls")),
    path("", include("event.urls")),
    path("", include("demande.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("ckeditor/", include("ckeditor_uploader.urls")),
] + debug_toolbar_urls()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configuration des handlers d'erreurs
handler404 = custom_404
handler500 = custom_500
