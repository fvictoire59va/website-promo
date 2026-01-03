#!/bin/bash
# Script de création automatique d'une stack client dans Portainer
# Usage: ./create-client-stack.sh -c "dupont" -p "motdepasse123" -s "cle-secrete-32-chars"

#set -e

# Valeurs par défaut
PORTAINER_URL="https://host.docker.internal:9443"
PORTAINER_USER="fred"
PORTAINER_PASSWORD="7b5KDg@z@Sno\$NtC"
ENVIRONMENT_ID="2"
BASE_PORT=8080
INITIAL_PASSWORD=""
CLIENT_ID=""

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
    echo "  -d CLIENT_ID           ID du client (évite l'appel API)"
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
while getopts "c:d:p:s:i:u:U:P:e:b:h" opt; do
    case $opt in
        c) CLIENT_NAME="$OPTARG" ;;
        d) CLIENT_ID="$OPTARG" ;;
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

# Fonction pour échapper les caractères spéciaux pour JSON
json_escape() {
    local string="$1"
    # Échapper les caractères spéciaux JSON avec printf pour éviter les problèmes bash
    printf '%s' "$string" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read())[1:-1])'
}

# Générer un mot de passe initial si non fourni
if [ -z "$INITIAL_PASSWORD" ]; then
    # Vérifier si openssl est disponible, sinon utiliser /dev/urandom
    if command -v openssl >/dev/null 2>&1; then
        INITIAL_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)
    else
        INITIAL_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 12 | head -n 1)
    fi
    echo "Mot de passe temporaire genere automatiquement"
fi

# 0. Utiliser l'ID du client fourni ou le récupérer via API
if [ -n "$CLIENT_ID" ]; then
    echo "[0/4] Utilisation de l'ID client fourni: $CLIENT_ID"
else
    echo "[0/4] Recuperation/creation de l'ID du client via l'API..."
    # Utiliser le nom du service Docker au lieu de localhost
    API_HOST=${API_HOST:-api_client}
    API_RESPONSE=$(curl -s -X POST http://${API_HOST}:8000/client-id/ \
        -H "Content-Type: application/json" \
        -d '{"nom":"'$CLIENT_NAME'","entreprise":"'$CLIENT_NAME'"}')

    echo "Reponse API: $API_RESPONSE"

    # Utiliser sed au lieu de grep -o pour compatibilité Debian
    CLIENT_ID=$(echo "$API_RESPONSE" | sed -n 's/.*"id":\([0-9]*\).*/\1/p' | head -n1)

    if [ -z "$CLIENT_ID" ]; then
        echo "Erreur: Impossible de récupérer ou créer l'ID du client via l'API."
        echo "Verifiez que:"
        echo "  - L'API est lancee sur http://${API_HOST}:8000"
        echo "  - La base de donnees erpbtp_clients est accessible"
        exit 1
    fi

    echo "ID du client: $CLIENT_ID"
fi

# 1. Authentification à Portainer
echo "[1/4] Authentification a Portainer..."
AUTH_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/auth" \
    -H "Content-Type: application/json" \
    -d '{"username":"'$PORTAINER_USER'","password":"'$PORTAINER_PASSWORD'"}')

# Utiliser sed au lieu de grep -o pour compatibilité Debian
TOKEN=$(echo "$AUTH_RESPONSE" | sed -n 's/.*"jwt":"\([^"]*\)".*/\1/p' | head -n1)

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

# Utiliser grep -E pour compatibilité Debian
CLIENT_COUNT=$(echo "$STACKS" | grep -o '"Name":"client-'"$CLIENT_NAME"'_[0-9]\+' | wc -l)

# Calculer le prochain numéro de client (base 1)
CLIENT_NUMBER=$((CLIENT_COUNT + 1))

# Récupérer tous les ports utilisés par les stacks existantes
echo "Recuperation des ports utilises..."
USED_PORTS=""
for stack_id in $(echo "$STACKS" | sed -n 's/.*"Id":\([0-9]*\).*/\1/p'); do
    STACK_DETAIL=$(curl -k -s -X GET "$PORTAINER_URL/api/stacks/$stack_id" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json")
    
    PORT=$(echo "$STACK_DETAIL" | sed -n 's/.*"APP_PORT"[^}]*"value":"\([0-9]*\)".*/\1/p' | head -n1)
    if [ -n "$PORT" ]; then
        USED_PORTS="$USED_PORTS $PORT"
    fi
done

# Récupérer aussi les ports utilisés directement par Docker
DOCKER_PORTS=$(docker ps --format "{{.Ports}}" | grep -o '0.0.0.0:[0-9]*' | cut -d':' -f2 | sort -u)
for docker_port in $DOCKER_PORTS; do
    USED_PORTS="$USED_PORTS $docker_port"
done

# Retirer les doublons et trier
USED_PORTS=$(echo $USED_PORTS | tr ' ' '\n' | sort -u | tr '\n' ' ')

# Trouver le premier port disponible
NEXT_PORT=$BASE_PORT
while true; do
    PORT_IN_USE=false
    for used_port in $USED_PORTS; do
        if [ "$NEXT_PORT" = "$used_port" ]; then
            PORT_IN_USE=true
            break
        fi
    done
    
    if [ "$PORT_IN_USE" = false ]; then
        break
    fi
    NEXT_PORT=$((NEXT_PORT + 1))
done

echo "Nombre de clients existants avec ce nom: $CLIENT_COUNT"
echo "Ports actuellement utilises:$USED_PORTS"
echo "Numero de la base pour ce client: $CLIENT_NUMBER"
echo "Port application attribue: $NEXT_PORT"

# 3. Vérifier si la stack existe déjà (vérification améliorée)
# Vérifier si la stack avec cet ID existe déjà
STACK_EXISTS=$(echo "$STACKS" | grep -o '"Name":"client_'"$CLIENT_ID"'"')
if [ -n "$STACK_EXISTS" ]; then
    echo "Erreur: Une stack pour le client ID $CLIENT_ID existe deja!"
    exit 1
fi

# 4. Créer la nouvelle stack
STACK_NAME="client_$CLIENT_ID"
echo "[3/4] Creation de la stack $STACK_NAME..."

# Échapper les valeurs sensibles pour JSON (utilisation de Python pour un échappement parfait)
POSTGRES_PASSWORD_ESCAPED=$(python3 -c "import json; print(json.dumps('$POSTGRES_PASSWORD'))")
SECRET_KEY_ESCAPED=$(python3 -c "import json; print(json.dumps('$SECRET_KEY'))")
INITIAL_PASSWORD_ESCAPED=$(python3 -c "import json; print(json.dumps('$INITIAL_PASSWORD'))")
CLIENT_NAME_ESCAPED=$(python3 -c "import json; print(json.dumps('$CLIENT_NAME'))")

# Créer le contenu du docker-compose inline avec échappement correct
COMPOSE_CONTENT=$(cat <<'COMPOSE_EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: erp_btp
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: __POSTGRES_PASSWORD__
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - erp_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U erp_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: https://github.com/fvictoire59va/ERP-BTP.git
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: erp_btp
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: __POSTGRES_PASSWORD__
      ERP_STORAGE_BACKEND: postgres
      SECRET_KEY: __SECRET_KEY__
      APP_URL: http://localhost:__APP_PORT__
      INITIAL_USERNAME: __INITIAL_USERNAME__
      INITIAL_PASSWORD: __INITIAL_PASSWORD__
      CLIENT_ID: __CLIENT_ID__
      CLIENT_NAME: __CLIENT_NAME__
      CLIENT_NUMBER: __CLIENT_NUMBER__
      NICEGUI_RELOAD: false
    ports:
      - "__APP_PORT__:8080"
    networks:
      - erp_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  postgres_data:
    driver: local

networks:
  erp_network:
    driver: bridge
COMPOSE_EOF
)

# Échapper les $ pour Docker Compose ($ devient $$)
POSTGRES_PASSWORD_COMPOSE="${POSTGRES_PASSWORD//\$/\$\$}"
SECRET_KEY_COMPOSE="${SECRET_KEY//\$/\$\$}"
INITIAL_PASSWORD_COMPOSE="${INITIAL_PASSWORD//\$/\$\$}"
CLIENT_NAME_COMPOSE="${CLIENT_NAME//\$/\$\$}"

# Remplacer les placeholders avec les valeurs échappées pour Docker Compose
COMPOSE_CONTENT="${COMPOSE_CONTENT//__POSTGRES_PASSWORD__/$POSTGRES_PASSWORD_COMPOSE}"
COMPOSE_CONTENT="${COMPOSE_CONTENT//__SECRET_KEY__/$SECRET_KEY_COMPOSE}"
COMPOSE_CONTENT="${COMPOSE_CONTENT//__INITIAL_USERNAME__/$CLIENT_NAME_COMPOSE}"
COMPOSE_CONTENT="${COMPOSE_CONTENT//__INITIAL_PASSWORD__/$INITIAL_PASSWORD_COMPOSE}"
COMPOSE_CONTENT="${COMPOSE_CONTENT//__CLIENT_ID__/$CLIENT_ID}"
COMPOSE_CONTENT="${COMPOSE_CONTENT//__CLIENT_NAME__/$CLIENT_NAME_COMPOSE}"
COMPOSE_CONTENT="${COMPOSE_CONTENT//__CLIENT_NUMBER__/$CLIENT_NUMBER}"
COMPOSE_CONTENT="${COMPOSE_CONTENT//__APP_PORT__/$NEXT_PORT}"

# Échapper le contenu du compose pour JSON (avec Python pour gérer tous les caractères spéciaux)
COMPOSE_CONTENT_ESCAPED=$(python3 -c "import json, sys; print(json.dumps(sys.stdin.read()))" <<< "$COMPOSE_CONTENT")

# Créer le JSON de la stack avec le contenu inline
STACK_JSON=$(cat <<EOF
{
    "name": "$STACK_NAME",
    "stackFileContent": $COMPOSE_CONTENT_ESCAPED
}
EOF
)

CREATE_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/stacks?type=2&method=string&endpointId=$ENVIRONMENT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$STACK_JSON")

STACK_ID=$(echo "$CREATE_RESPONSE" | sed -n 's/.*"Id":\([0-9]*\).*/\1/p' | head -n1)

if [ -z "$STACK_ID" ]; then
    echo "Erreur: Impossible de creer la stack"
    echo "$CREATE_RESPONSE"
    exit 1
fi

echo "Stack creee avec succes (ID: $STACK_ID)"

# 6. Afficher le résumé
echo ""
echo "[4/4] Resume de la configuration:"
echo "================================="
echo "Nom du client    : $CLIENT_NAME"
echo "Numero client    : $CLIENT_NUMBER"
echo "Nom de la stack  : $STACK_NAME"
echo "Port application : $NEXT_PORT"
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
