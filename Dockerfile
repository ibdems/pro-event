# Image de base
FROM python:3.12-slim

# Installer les dépendances système nécessaires pour WeasyPrint
RUN apt update && apt install -y \
    libgtk-3-0 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev libxml2-dev libxslt-dev python3-dev \
    libgobject-2.0-0 libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier le projet
COPY . /app/

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exposer le port de l'application
EXPOSE 8000

# Commande par défaut
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
