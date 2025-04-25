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

# Configuration pour Backblaze B2
AWS_ACCESS_KEY_ID = env("B2_ACCESS_KEY_ID")  # Clé d'accès Backblaze
AWS_SECRET_ACCESS_KEY = env("B2_SECRET_ACCESS_KEY")  # Clé secrète Backblaze
AWS_STORAGE_BUCKET_NAME = env("B2_BUCKET_NAME")  # Nom du bucket

# Endpoint S3 de Backblaze B2 (à adapter selon votre région)
AWS_S3_ENDPOINT_URL = f"https://s3.{env('B2_REGION')}.backblazeb2.com"
AWS_S3_REGION_NAME = env("B2_REGION")  # Par exemple: 'us-west-002'

# Paramètres de cache et comportement
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False  # Désactiver les URLs signées pour les médias publics
AWS_S3_FILE_OVERWRITE = False  # Ne pas écraser les fichiers avec le même nom

# Location des médias dans le bucket
MEDIAFILES_LOCATION = "proevent/media"

# Construction de l'URL pour les médias
# Format Backblaze URL: https://f002.backblazeb2.com/file/nom-bucket/chemin
# ou avec un domaine personnalisé si configuré
B2_CUSTOM_DOMAIN = env("B2_CUSTOM_DOMAIN", default=None)
if B2_CUSTOM_DOMAIN:
    MEDIA_URL = f"https://{B2_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/"
else:
    # URL par défaut de Backblaze
    MEDIA_URL = f"https://f{env('B2_REGION').split('-')[2]}.backblazeb2.com/file/{AWS_STORAGE_BUCKET_NAME}/{MEDIAFILES_LOCATION}/"  # noqa

# Configuration du stockage Django
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

STORAGES = {
    "default": {
        "BACKEND": "config.storages.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Sécurité
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

# Pour les fichiers statiques
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
