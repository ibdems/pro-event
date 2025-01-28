# Image de base
FROM python:3.12-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && apt-get clean

# Définir le répertoire de travail
WORKDIR /app

# Copier le projet
COPY . /app/

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exposer le port de l'application
EXPOSE 8000

# Commande par défaut (modifiée par docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
