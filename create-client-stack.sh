#!/bin/bash
# Script de création automatique d'une stack client dans Portainer
# Usage: ./create-client-stack.sh -c "dupont" -p "motdepasse123" -s "cle-secrete-32-chars"

#set -e

# Valeurs par défaut
PORTAINER_URL="https://localhost:9443"
PORTAINER_USER="fred"
PORTAINER_PASSWORD="7b5KDg@z@Sno\$NtC"
ENVIRONMENT_ID="2"
BASE_PORT=8080
INITIAL_PASSWORD=""

# Fonction d'aide
usage() {
    echo "Usage: $0 -c CLIENT_NAME -p POSTGRES_PASSWORD -s SECRET_KEY [OPTIONS]"
    echo ""
    echo "Options requises:"
    echo "  -c CLIENT_NAME         Nom du client"
    echo "  -p POSTGRES_PASSWORD   Mot de passe PostgreSQL"
    echo "  -s SECRET_KEY          Clé secrète (32 caractères)"
    echo ""
    echo "Options:"
    echo "  -i INITIAL_PASSWORD    Mot de passe initial (généré si omis)"
    echo "  -u PORTAINER_URL       URL Portainer (défaut: https://localhost:9443)"
    echo "  -U PORTAINER_USER      Utilisateur Portainer (défaut: fred)"
    echo "  -P PORTAINER_PASSWORD  Mot de passe Portainer"
    echo "  -e ENVIRONMENT_ID      ID environnement (défaut: 2)"
    echo "  -b BASE_PORT           Port de base (défaut: 8080)"
    echo "  -h                     Afficher cette aide"
    exit 1
}

# Parser les arguments
while getopts "c:p:s:i:u:U:P:e:b:h" opt; do
    case $opt in
        c) CLIENT_NAME="$OPTARG" ;;
        p) POSTGRES_PASSWORD="$OPTARG" ;;
        s) SECRET_KEY="$OPTARG" ;;
        i) INITIAL_PASSWORD="$OPTARG" ;;
        u) PORTAINER_URL="$OPTARG" ;;
        U) PORTAINER_USER="$OPTARG" ;;
        P) PORTAINER_PASSWORD="$OPTARG" ;;
        e) ENVIRONMENT_ID="$OPTARG" ;;
        b) BASE_PORT="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Vérifier les paramètres requis
if [ -z "$CLIENT_NAME" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$SECRET_KEY" ]; then
    echo "Erreur: Paramètres CLIENT_NAME, POSTGRES_PASSWORD et SECRET_KEY requis"
    usage
fi

echo "========================================"
echo "Creation d'une stack client Portainer"
echo "========================================"
echo ""

# Générer un mot de passe initial si non fourni
if [ -z "$INITIAL_PASSWORD" ]; then
    INITIAL_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)
    echo "Mot de passe temporaire genere automatiquement"
fi

# 0. Récupérer l'ID du client via l'API FastAPI
echo "[0/4] Recuperation de l'ID du client via l'API..."
API_RESPONSE=$(curl -s -X POST http://localhost:9100/client-id/ \
    -H "Content-Type: application/json" \
    -d '{"nom":"'$CLIENT_NAME'"}')

echo "Reponse API: $API_RESPONSE"

CLIENT_ID=$(echo "$API_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$CLIENT_ID" ]; then
    echo "Erreur: Impossible de récupérer l'ID du client via l'API."
    echo "Verifiez que:"
    echo "  - L'API est lancee sur http://localhost:9100"
    echo "  - Le client '$CLIENT_NAME' existe dans la base erpbtp_clients"
    echo "  - La table clients contient des donnees"
    exit 1
fi

echo "ID du client recupere: $CLIENT_ID"

# 1. Authentification à Portainer
echo "[1/4] Authentification a Portainer..."
AUTH_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/auth" \
    -H "Content-Type: application/json" \
    -d '{"username":"'$PORTAINER_USER'","password":"'$PORTAINER_PASSWORD'"}')

TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"jwt":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Erreur: Impossible de s'authentifier a Portainer"
    echo "$AUTH_RESPONSE"
    exit 1
fi

echo "Authentification reussie"

# 2. Récupérer la liste des stacks existantes
echo "[2/4] Recuperation des stacks existantes..."
STACKS=$(curl -k -s -X GET "$PORTAINER_URL/api/stacks" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

# Compter les stacks qui commencent par "client-<CLIENT_NAME>_"
CLIENT_COUNT=$(echo "$STACKS" | grep -o '"Name":"client-'"$CLIENT_NAME"'_[0-9]\+' | wc -l)

# Calculer le prochain numéro de client (base 1)
CLIENT_NUMBER=$((CLIENT_COUNT + 1))

# Compter TOUTES les stacks client pour calculer les ports
TOTAL_CLIENT_COUNT=$(echo "$STACKS" | grep -o '"Name":"client-[^"]*' | wc -l)

# Calculer le prochain port disponible (basé sur le nombre total de clients)
NEXT_PORT=$((BASE_PORT + TOTAL_CLIENT_COUNT))
POSTGRES_PORT=$((5432 + TOTAL_CLIENT_COUNT))

echo "Nombre de clients existants avec ce nom: $CLIENT_COUNT"
echo "Nombre total de clients: $TOTAL_CLIENT_COUNT"
echo "Numero de la base pour ce client: $CLIENT_NUMBER"
echo "Port attribue: $NEXT_PORT"
echo "Port PostgreSQL attribue: $POSTGRES_PORT"

# 3. Vérifier si la stack existe déjà (vérification améliorée)
# Vérifier si la stack avec ce nom et ce numéro existe déjà
STACK_EXISTS=$(echo "$STACKS" | grep -o '"Name":"client-'"$CLIENT_NAME"'_'"$CLIENT_NUMBER"'"')
if [ -n "$STACK_EXISTS" ]; then
    echo "Erreur: Une stack pour le client '$CLIENT_NAME' avec le numéro $CLIENT_NUMBER existe deja! (détection améliorée)"
    exit 1
fi

# 4. Créer la nouvelle stack
STACK_NAME="client-${CLIENT_NAME}_$CLIENT_ID"
echo "[3/4] Creation de la stack $STACK_NAME..."

STACK_JSON=$(cat <<EOF
{
    "name": "$STACK_NAME",
    "repositoryURL": "https://github.com/fvictoire59va/ERP-BTP",
    "repositoryReferenceName": "refs/heads/main",
    "composeFile": "docker-compose.portainer.yml",
    "repositoryAuthentication": false,
    "env": [
        {"name": "CLIENT_NAME", "value": "$CLIENT_NAME"},
        {"name": "CLIENT_NUMBER", "value": "$CLIENT_NUMBER"},
        {"name": "POSTGRES_PASSWORD", "value": "$POSTGRES_PASSWORD"},
        {"name": "SECRET_KEY", "value": "$SECRET_KEY"},
        {"name": "APP_PORT", "value": "$NEXT_PORT"},
        {"name": "POSTGRES_DB", "value": "erp_btp"},
        {"name": "POSTGRES_USER", "value": "erp_user"},
        {"name": "POSTGRES_PORT", "value": "$POSTGRES_PORT"},
        {"name": "INITIAL_USERNAME", "value": "$CLIENT_NAME"},
        {"name": "INITIAL_PASSWORD", "value": "$INITIAL_PASSWORD"}
    ]
}
EOF
)

CREATE_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/stacks?type=2&method=repository&endpointId=$ENVIRONMENT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$STACK_JSON")

STACK_ID=$(echo "$CREATE_RESPONSE" | grep -o '"Id":[0-9]*' | cut -d':' -f2)

if [ -z "$STACK_ID" ]; then
    echo "Erreur: Impossible de creer la stack"
    echo "$CREATE_RESPONSE"
    exit 1
fi

echo "Stack creee avec succes (ID: $STACK_ID)"

# 5. Attendre que PostgreSQL soit prêt
echo "[4/6] Attente du demarrage de PostgreSQL..."
        POSTGRES_READY=true
        echo "PostgreSQL est pret"
    fi
done

if [ "$POSTGRES_READY" != "true" ]; then
    echo "Timeout: PostgreSQL n'est pas pret apres $MAX_RETRIES tentatives"
    echo "  L'utilisateur devra etre cree manuellement"
fi

# 6. Créer les tables dans la base de données
if [ "$POSTGRES_READY" = "true" ]; then
    echo "[5/6] Creation des tables dans la base de donnees..."
    
    # Script SQL pour créer les tables clients, abonnements et demo_requests
    SQL_CREATE_TABLES=$(cat <<'EOSQL'
-- Table clients
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100),
    email VARCHAR(100) NOT NULL UNIQUE,
    entreprise VARCHAR(100) NOT NULL,
    telephone VARCHAR(30),
    adresse VARCHAR(500),
    ville VARCHAR(100),
    code_postal VARCHAR(10),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table abonnements
CREATE TABLE IF NOT EXISTS abonnements (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    plan VARCHAR(50) NOT NULL,
    prix_mensuel NUMERIC(10, 2) NOT NULL,
    date_debut TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_fin TIMESTAMP,
    statut VARCHAR(20) DEFAULT 'actif',
    periode_essai BOOLEAN DEFAULT TRUE,
    date_fin_essai TIMESTAMP
);

-- Table demo_requests
CREATE TABLE IF NOT EXISTS demo_requests (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    entreprise VARCHAR(100) NOT NULL,
    telephone VARCHAR(30) NOT NULL,
    effectif VARCHAR(20),
    plan_choisi VARCHAR(50),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_abonnements_client_id ON abonnements(client_id);
CREATE INDEX IF NOT EXISTS idx_abonnements_statut ON abonnements(statut);
EOSQL
)
    
    if docker exec "$CONTAINER_NAME" psql -U erp_user -d erp_btp -c "$SQL_CREATE_TABLES" >/dev/null 2>&1; then
        echo "✅ Tables creees avec succes (clients, abonnements, demo_requests)"
    else
        echo "⚠️ Avertissement: Impossible de creer les tables automatiquement"
        echo "   Les tables seront creees au premier demarrage de l'application"
    fi
fi

# 7. Afficher le résumé
echo ""
echo "[6/6] Resume de la configuration:"
echo "================================="
echo "Nom du client    : $CLIENT_NAME"
echo "Numero client    : $CLIENT_NUMBER"
echo "Nom de la stack  : $STACK_NAME"
echo "Port application : $NEXT_PORT"
echo "Port PostgreSQL  : $POSTGRES_PORT"
echo "URL acces        : http://votre-serveur:$NEXT_PORT"
echo "Base de donnees  : erp_btp"
echo "Utilisateur DB   : erp_user"
echo ""
echo "Identifiants de connexion temporaires:"
echo "  Nom d'utilisateur : $CLIENT_NAME"
echo "  Mot de passe      : $INITIAL_PASSWORD"
echo "  (A changer lors de la premiere connexion)"
echo "================================="
echo ""
echo "Stack deployee avec succes!"
echo "  Accedez a Portainer pour surveiller le deploiement."
