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
    bash \
    ca-certificates \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz -o docker.tgz \
    && tar -xzvf docker.tgz --strip 1 -C /usr/local/bin docker/docker \
    && rm docker.tgz \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Vérifier que curl est bien installé
RUN curl --version

# Copier le code de l'application
COPY . .

# Rendre le script bash exécutable
RUN chmod +x /app/create-client-stack.sh

# Exposer le port 8000
EXPOSE 8000

# Commande de démarrage
CMD ["python", "site_commercial.py"]
