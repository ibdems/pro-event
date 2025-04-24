# Image de base
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings_prod

# Créer un utilisateur non-privilégié
RUN groupadd -r app && useradd -r -g app app

# Installer les dépendances système pour WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgtk-3-0 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev libxml2-dev libxslt-dev \
    libglib2.0-0 libglib2.0-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copier le code source
COPY . .

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Définir les permissions
RUN chown -R app:app /app
USER app

# Exposer le port
EXPOSE 8080

# Exécuter l'application avec Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "3"]