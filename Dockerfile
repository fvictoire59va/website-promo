# Image de base Python
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances système nécessaires pour psycopg
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Vérifier que curl est bien installé
RUN curl --version

# Copier le code de l'application
COPY . .

# Exposer le port 8000
EXPOSE 8000

# Commande de démarrage
CMD ["python", "site_commercial.py"]
