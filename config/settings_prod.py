import os

import dj_database_url
import environ

from .settings import *  # noqa

env = environ.Env(DEBUG=(bool, False))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")

DATABASES = {"default": dj_database_url.config(conn_health_checks=True)}

AWS_ACCESS_KEY_ID = env("B2_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("B2_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("B2_BUCKET_NAME")

AWS_S3_ENDPOINT_URL = f"https://s3.{env('B2_REGION')}.backblazeb2.com"
AWS_S3_REGION_NAME = env("B2_REGION")

AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False

MEDIAFILES_LOCATION = "proevent-media"

STATICFILES_LOCATION = "proevent-static"

B2_CUSTOM_DOMAIN = env("B2_CUSTOM_DOMAIN", default=None)

if B2_CUSTOM_DOMAIN:
    MEDIA_URL = f"https://{B2_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/"
    STATIC_URL = f"https://{B2_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/"
else:
    region_parts = env("B2_REGION").split("-")
    bucket_region_code = region_parts[-1] if len(region_parts) > 1 else "003"
    media_url_base = f"https://f{bucket_region_code}.backblazeb2.com/file/{AWS_STORAGE_BUCKET_NAME}"
    MEDIA_URL = f"{media_url_base}/{MEDIAFILES_LOCATION}/"
    STATIC_URL = f"{media_url_base}/{STATICFILES_LOCATION}/"

DEFAULT_FILE_STORAGE = "config.storages.MediaStorage"

STORAGES = {
    "default": {
        "BACKEND": "config.storages.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "config.storages.StaticStorage",
    },
}

CSRF_TRUSTED_ORIGINS = env("TRUSTED_ORIGINS").split(",")

SESSION_COOKIE_SECURE = True
CSRF_COOKIES_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

ADMINS = [("Ibrahima", "ibrahima882001@gmail.com")]

# Configuration de la journalisation en production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "config": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "event": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "demande": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "users": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "dashboard": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
