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
    gnupg \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
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
