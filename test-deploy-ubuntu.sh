#!/bin/bash
# Script de test du déploiement du site commercial sur Ubuntu
# Sans passer par Portainer

#set -e

echo "========================================"
echo "Test de déploiement - Site Commercial"
echo "========================================"
echo ""

# Variables
REPO_URL="https://github.com/fvictoire59va/website-promo.git"
WORK_DIR="/tmp/test-site-commercial"
BRANCH="main"

# Nettoyer le répertoire de travail s'il existe
if [ -d "$WORK_DIR" ]; then
    echo "🗑️  Nettoyage du répertoire de travail..."
    rm -rf "$WORK_DIR"
fi

# Cloner le repository
echo "📥 Clonage du repository..."
git clone -b "$BRANCH" "$REPO_URL" "$WORK_DIR"
cd "$WORK_DIR"

# Créer le fichier .env si nécessaire
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cat > .env << 'EOF'
# Configuration PostgreSQL
POSTGRES_USER=fred
POSTGRES_PASSWORD=Jbvf2023@
POSTGRES_DB=erpbtp_clients

# Configuration Application
DB_USER=fred
DB_PASSWORD=Jbvf2023@
DB_NAME=erpbtp_clients
DB_HOST=postgres
DB_PORT=5432

# Ports exposés
POSTGRES_PORT=5433
APP_PORT=8100

# Configuration SMTP Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=frederic.victoire@gmail.com
SMTP_PASSWORD=rmcx bdzy vdxg tpry
FROM_EMAIL=frederic.victoire@gmail.com

# Cache bust
CACHE_BUST=1
EOF
fi

echo "✅ Fichier .env créé"
echo ""

# Afficher les services disponibles
echo "📋 Services dans docker-compose.yml :"
docker-compose config --services
echo ""

# Option: build seulement ou build + run
echo "Que voulez-vous faire ?"
echo "  1) Builder les images uniquement (pour tester)"
echo "  2) Builder et lancer les services"
echo "  3) Lancer sans rebuild (si images déjà construites)"
echo "  4) Nettoyer et tout reconstruire"
read -p "Choix [1-4] : " choice

case $choice in
    1)
        echo ""
        echo "🔨 Construction des images..."
        docker-compose build --no-cache
        echo ""
        echo "✅ Images construites avec succès !"
        echo "Les images sont prêtes mais les services ne sont pas lancés."
        ;;
    2)
        echo ""
        echo "🔨 Construction des images..."
        docker-compose build --no-cache
        echo ""
        echo "🚀 Lancement des services..."
        docker-compose up -d
        echo ""
        echo "✅ Services lancés !"
        echo ""
        echo "📊 État des conteneurs :"
        docker-compose ps
        echo ""
        echo "📝 Pour voir les logs :"
        echo "  docker-compose -f $WORK_DIR/docker-compose.yml logs -f"
        echo ""
        echo "🌐 URLs d'accès :"
        echo "  - Site commercial : http://localhost:8100"
        echo "  - API Client      : http://localhost:9100"
        echo ""
        echo "🛑 Pour arrêter :"
        echo "  docker-compose -f $WORK_DIR/docker-compose.yml down"
        ;;
    3)
        echo ""
        echo "🚀 Lancement des services (sans rebuild)..."
        docker-compose up -d
        echo ""
        echo "✅ Services lancés !"
        echo ""
        echo "📊 État des conteneurs :"
        docker-compose ps
        echo ""
        echo "📝 Pour voir les logs :"
        echo "  docker-compose -f $WORK_DIR/docker-compose.yml logs -f"
        ;;
    4)
        echo ""
        echo "🧹 Nettoyage complet..."
        docker-compose down -v
        docker system prune -f
        echo ""
        echo "🔨 Reconstruction des images..."
        docker-compose build --no-cache
        echo ""
        echo "🚀 Lancement des services..."
        docker-compose up -d
        echo ""
        echo "✅ Services lancés !"
        echo ""
        echo "📊 État des conteneurs :"
        docker-compose ps
        ;;
    *)
        echo "Choix invalide"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "📁 Répertoire de travail : $WORK_DIR"
echo "========================================"
