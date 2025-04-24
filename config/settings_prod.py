import os

import dj_database_url
import environ

from .settings import *  # noqa  # Importe toutes les configurations de base depuis le fichier settings.py

# Initialisation de l'objet pour lire les variables d'environnement
env = environ.Env(
    DEBUG=(bool, False)  # Par défaut, DEBUG est défini comme un booléen et désactivé (False)
)

# Définition du répertoire de base du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Lecture des variables d'environnement à partir du fichier .env
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Clé secrète pour sécuriser Django
SECRET_KEY = env("SECRET_KEY")

# Mode DEBUG (désactivé en production pour des raisons de sécurité)
DEBUG = env("DEBUG")

# Hôtes autorisés à accéder à l'application
ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")

# Configuration de la base de données
DATABASES = {"default": dj_database_url.config(conn_health_checks=True)}

# Pour DigitalOcean Spaces
AWS_ACCESS_KEY_ID = "VOTRE_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY = "VOTRE_SECRET_KEY"
AWS_STORAGE_BUCKET_NAME = "proevent"
AWS_S3_ENDPOINT_URL = "https://fra1.digitaloceanspaces.com"
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
AWS_LOCATION = "media"
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False

MEDIAFILES_LOCATION = "proevent/media"

MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.fra1.digitaloceanspaces.com/{MEDIAFILES_LOCATION}/"

AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

AWS_S3_FILE_OVERWRITE = False

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

STORAGES = {
    "default": {
        "BACKEND": "config.storages.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
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


# Pour Backblaze B2
# AWS_ACCESS_KEY_ID = 'VOTRE_KEY_ID'
# AWS_SECRET_ACCESS_KEY = 'VOTRE_APPLICATION_KEY'
# AWS_STORAGE_BUCKET_NAME = 'proevent-bucket'
# AWS_S3_ENDPOINT_URL = 'https://s3.us-west-002.backblazeb2.com'
# AWS_S3_REGION_NAME = 'us-west-002'

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
