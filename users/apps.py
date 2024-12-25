from django.apps import AppConfig


class MyauthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "myauth"

    def ready(self):
        import users.signals  # noqa F401
