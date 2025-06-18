import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = "7d0bsn&@=dyb@v0f)fmtk6esv2(49@sy_11sia&d1=y@9=_!ut"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "debug_toolbar",
    "event",
    "demande",
    "dashboard",
    "ckeditor",
    "ckeditor_uploader",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "config.middleware.SessionTimeoutMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "users" / "templates",
            os.path.join(BASE_DIR, "event", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "db_proevent",
        "USER": "proevent",
        "PASSWORD": "proevent",
        "HOST": "127.0.0.1",
        "PORT": "5460",
        "TEST": {
            "NAME": "task_test",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "fr-Fr"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Configuration CKEditor 6
# Nous gardons certains paramètres pour la compatibilité avec les modèles existants
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_RESTRICT_BY_USER = True
CKEDITOR_IMAGE_BACKEND = "pillow"

# Désactiver complètement toutes les alertes et warnings
CKEDITOR_ALERT_ON_VULNERABILITY = False
CKEDITOR_BASEPATH = "/static/ckeditor6/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "none"
    },  # On n'utilise plus cette config, on utilise CKEditor 6 directement
}

# On ne charge pas le JS de CKEditor 4 automatiquement
CKEDITOR_JQUERY_URL = ""
CKEDITOR_CONFIGS = {}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Pour django debug toolbar
INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

# env mail
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "ibrahima882001@gmail.com"
EMAIL_HOST_PASSWORD = "kgqh dzyc keer zlfv"
DEFAULT_FROM_EMAIL = "ibrahima882001@gmail.com"
EMAIL_USE_TLS = True

# URL de base pour les liens dans les emails
BASE_URL = env("BASE_URL", default="https://proeventgn.com")
DOMAIN_URL = env(
    "DOMAIN_URL", default="proeventgn.com"
)  # Utilisé dans les templates d'activation et de réinitialisation

# Configuration de Celery avec Redis comme broker
CELERY_BROKER_URL = "redis://127.0.0.1:6380/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6380/1"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_EXTENDED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "debug.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
PAYCARD_ECOMMERCE_CODE = "ODc5NjI4MzA"
