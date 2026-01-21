#!/bin/bash
# Script de création automatique d'une stack client dans Portainer
# Supporte les abonnements via base de données externe
# Usage: ./create-client-stack.sh -c "dupont" -p "motdepasse123" -s "cle-secrete-32-chars" --sub-pass "password-abonnements"

#set -e

# Valeurs par défaut
PORTAINER_URL="https://host.docker.internal:9443"
PORTAINER_USER="fred"
PORTAINER_PASSWORD="7b5KDg@z@Sno\$NtC"
ENVIRONMENT_ID="2"
BASE_PORT=8080
INITIAL_PASSWORD=""
CLIENT_ID=""

# Valeurs par défaut pour les abonnements
SUBSCRIPTION_DB_HOST="176.131.66.167"
SUBSCRIPTION_DB_PORT="5433"
SUBSCRIPTION_DB_NAME="erpbtp_clients"
SUBSCRIPTION_DB_USER="fred"
SUBSCRIPTION_DB_PASSWORD=""

# Valeurs par défaut pour Stripe (vides par défaut, seront lues depuis .env)
STRIPE_API_KEY=""
STRIPE_PUBLISHABLE_KEY=""
STRIPE_WEBHOOK_SECRET=""
STRIPE_PRICE_ID_STARTER=""
STRIPE_PRICE_ID_PROFESSIONAL=""
STRIPE_PRICE_ID_ENTERPRISE=""

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
    echo ""
    echo "Options abonnements:"
    echo "  --sub-host HOST        Hôte DB abonnements (défaut: 176.131.66.167)"
    echo "  --sub-port PORT        Port DB abonnements (défaut: 5433)"
    echo "  --sub-db DB            Base données abonnements (défaut: erpbtp_clients)"
    echo "  --sub-user USER        Utilisateur DB abonnements (défaut: fred)"
    echo "  --sub-pass PASSWORD    Mot de passe DB abonnements (OBLIGATOIRE)"
    echo ""
    echo "Options Stripe:"
    echo "  --stripe-key KEY       Clé API Stripe (sk_test_... ou sk_live_...)"
    echo "  --stripe-pub KEY       Clé publique Stripe (pk_test_... ou pk_live_...)"
    echo "  --stripe-webhook SEC   Secret webhook Stripe (whsec_...)"
    echo "  --stripe-starter ID    Price ID Starter (price_...)"
    echo "  --stripe-pro ID        Price ID Professionnel (price_...)"
    echo "  --stripe-enterprise ID Price ID Entreprise (price_...)"
    echo ""
    echo "Note: Les variables Stripe sont lues depuis .env si présentes et non fourni en paramètre"
    echo ""
    echo "  -h                     Afficher cette aide"
    exit 1
}

# Parser les arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c) CLIENT_NAME="$2"; shift 2 ;;
        -d) CLIENT_ID="$2"; shift 2 ;;
        -p) POSTGRES_PASSWORD="$2"; shift 2 ;;
        -s) SECRET_KEY="$2"; shift 2 ;;
        -i) INITIAL_PASSWORD="$2"; shift 2 ;;
        -u) PORTAINER_URL="$2"; shift 2 ;;
        -U) PORTAINER_USER="$2"; shift 2 ;;
        -P) PORTAINER_PASSWORD="$2"; shift 2 ;;
        -e) ENVIRONMENT_ID="$2"; shift 2 ;;
        -b) BASE_PORT="$2"; shift 2 ;;
        --sub-host) SUBSCRIPTION_DB_HOST="$2"; shift 2 ;;
        --sub-port) SUBSCRIPTION_DB_PORT="$2"; shift 2 ;;
        --sub-db) SUBSCRIPTION_DB_NAME="$2"; shift 2 ;;
        --sub-user) SUBSCRIPTION_DB_USER="$2"; shift 2 ;;
        --sub-pass) SUBSCRIPTION_DB_PASSWORD="$2"; shift 2 ;;
        --stripe-key) STRIPE_API_KEY="$2"; shift 2 ;;
        --stripe-pub) STRIPE_PUBLISHABLE_KEY="$2"; shift 2 ;;
        --stripe-webhook) STRIPE_WEBHOOK_SECRET="$2"; shift 2 ;;
        --stripe-starter) STRIPE_PRICE_ID_STARTER="$2"; shift 2 ;;
        --stripe-pro) STRIPE_PRICE_ID_PROFESSIONAL="$2"; shift 2 ;;
        --stripe-enterprise) STRIPE_PRICE_ID_ENTERPRISE="$2"; shift 2 ;;
        -h) usage ;;
        *) echo "Option inconnue: $1"; usage ;;
    esac
done

# Vérifier les paramètres requis
if [ -z "$CLIENT_NAME" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$SECRET_KEY" ]; then
    echo "Erreur: Paramètres CLIENT_NAME, POSTGRES_PASSWORD et SECRET_KEY requis"
    usage
fi

# Vérifier que le mot de passe d'abonnement est fourni
if [ -z "$SUBSCRIPTION_DB_PASSWORD" ]; then
    echo "⚠️  ATTENTION: SUBSCRIPTION_DB_PASSWORD non configuré!"
    echo "Les vérifications d'abonnement ne fonctionneront pas."
    echo ""
    read -p "Entrez le mot de passe pour la base d'abonnements (ou Ctrl+C pour annuler): " SUBSCRIPTION_DB_PASSWORD
    if [ -z "$SUBSCRIPTION_DB_PASSWORD" ]; then
        echo "Erreur: Mot de passe d'abonnement requis"
        exit 1
    fi
fi

echo "========================================"
echo "Creation d'une stack client Portainer"
echo "========================================"
echo ""

# Lire les variables Stripe depuis .env si présentes et non fournies en paramètre
if [ -f ".env" ]; then
    echo "📝 Lecture des variables Stripe depuis .env..."
    if [ -z "$STRIPE_API_KEY" ]; then
        STRIPE_API_KEY=$(grep "^STRIPE_API_KEY=" .env | cut -d'=' -f2)
    fi
    if [ -z "$STRIPE_PUBLISHABLE_KEY" ]; then
        STRIPE_PUBLISHABLE_KEY=$(grep "^STRIPE_PUBLISHABLE_KEY=" .env | cut -d'=' -f2)
    fi
    if [ -z "$STRIPE_WEBHOOK_SECRET" ]; then
        STRIPE_WEBHOOK_SECRET=$(grep "^STRIPE_WEBHOOK_SECRET=" .env | cut -d'=' -f2)
    fi
    if [ -z "$STRIPE_PRICE_ID_STARTER" ]; then
        STRIPE_PRICE_ID_STARTER=$(grep "^STRIPE_PRICE_ID_STARTER=" .env | cut -d'=' -f2)
    fi
    if [ -z "$STRIPE_PRICE_ID_PROFESSIONAL" ]; then
        STRIPE_PRICE_ID_PROFESSIONAL=$(grep "^STRIPE_PRICE_ID_PROFESSIONAL=" .env | cut -d'=' -f2)
    fi
    if [ -z "$STRIPE_PRICE_ID_ENTERPRISE" ]; then
        STRIPE_PRICE_ID_ENTERPRISE=$(grep "^STRIPE_PRICE_ID_ENTERPRISE=" .env | cut -d'=' -f2)
    fi
    echo "✓ Variables Stripe chargées"
fi

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

# Debug: vérifier le mot de passe reçu
echo "DEBUG - Mot de passe reçu (length ${#INITIAL_PASSWORD}): [$INITIAL_PASSWORD]"
echo "DEBUG - Mot de passe avec od: $(printf '%s' "$INITIAL_PASSWORD" | od -c)"

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

echo "Ports actuellement utilises:$USED_PORTS"
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

# Échapper les valeurs sensibles pour JSON
# Fonction pour échapper correctement une chaîne pour JSON
json_escape() {
    local string="$1"
    # Utiliser Python pour un échappement fiable de JSON
    printf '%s' "$string" | python3 -c "import json, sys; print(json.dumps(sys.stdin.read().rstrip('\n\r')))"
}

POSTGRES_PASSWORD_ESCAPED=$(json_escape "$POSTGRES_PASSWORD")
SECRET_KEY_ESCAPED=$(json_escape "$SECRET_KEY")
INITIAL_PASSWORD_ESCAPED=$(json_escape "$INITIAL_PASSWORD")
CLIENT_NAME_ESCAPED=$(json_escape "$CLIENT_NAME")
SUBSCRIPTION_DB_PASSWORD_ESCAPED=$(json_escape "$SUBSCRIPTION_DB_PASSWORD")
STRIPE_API_KEY_ESCAPED=$(json_escape "$STRIPE_API_KEY")
STRIPE_PUBLISHABLE_KEY_ESCAPED=$(json_escape "$STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET_ESCAPED=$(json_escape "$STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID_STARTER_ESCAPED=$(json_escape "$STRIPE_PRICE_ID_STARTER")
STRIPE_PRICE_ID_PROFESSIONAL_ESCAPED=$(json_escape "$STRIPE_PRICE_ID_PROFESSIONAL")
STRIPE_PRICE_ID_ENTERPRISE_ESCAPED=$(json_escape "$STRIPE_PRICE_ID_ENTERPRISE")

# Debug: afficher les valeurs échappées
echo "DEBUG - INITIAL_PASSWORD_ESCAPED: $INITIAL_PASSWORD_ESCAPED"

# Créer le JSON de la stack avec Git repository
STACK_JSON=$(cat <<EOF
{
    "name": "$STACK_NAME",
    "repositoryURL": "https://github.com/fvictoire59va/ERP-BTP",
    "repositoryReferenceName": "refs/heads/main",
    "composeFile": "docker-compose.portainer.yml",
    "env": [
        {"name": "POSTGRES_PASSWORD", "value": $POSTGRES_PASSWORD_ESCAPED},
        {"name": "SECRET_KEY", "value": $SECRET_KEY_ESCAPED},
        {"name": "INITIAL_USERNAME", "value": $CLIENT_NAME_ESCAPED},
        {"name": "INITIAL_PASSWORD", "value": $INITIAL_PASSWORD_ESCAPED},
        {"name": "CLIENT_ID", "value": "$CLIENT_ID"},
        {"name": "CLIENT_NAME", "value": $CLIENT_NAME_ESCAPED},
        {"name": "APP_PORT", "value": "$NEXT_PORT"},
        {"name": "SUBSCRIPTION_DB_HOST", "value": "$SUBSCRIPTION_DB_HOST"},
        {"name": "SUBSCRIPTION_DB_PORT", "value": "$SUBSCRIPTION_DB_PORT"},
        {"name": "SUBSCRIPTION_DB_NAME", "value": "$SUBSCRIPTION_DB_NAME"},
        {"name": "SUBSCRIPTION_DB_USER", "value": "$SUBSCRIPTION_DB_USER"},
        {"name": "SUBSCRIPTION_DB_PASSWORD", "value": $SUBSCRIPTION_DB_PASSWORD_ESCAPED},
        {"name": "STRIPE_API_KEY", "value": $STRIPE_API_KEY_ESCAPED},
        {"name": "STRIPE_PUBLISHABLE_KEY", "value": $STRIPE_PUBLISHABLE_KEY_ESCAPED},
        {"name": "STRIPE_WEBHOOK_SECRET", "value": $STRIPE_WEBHOOK_SECRET_ESCAPED},
        {"name": "STRIPE_PRICE_ID_STARTER", "value": $STRIPE_PRICE_ID_STARTER_ESCAPED},
        {"name": "STRIPE_PRICE_ID_PROFESSIONAL", "value": $STRIPE_PRICE_ID_PROFESSIONAL_ESCAPED},
        {"name": "STRIPE_PRICE_ID_ENTERPRISE", "value": $STRIPE_PRICE_ID_ENTERPRISE_ESCAPED},
        {"name": "NICEGUI_RELOAD", "value": "true"},
        {"name": "LOG_LEVEL", "value": "DEBUG"}
    ]
}
EOF
)

CREATE_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/stacks?type=2&method=repository&endpointId=$ENVIRONMENT_ID" \
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

# 5. Afficher le résumé
echo ""
echo "[4/4] Resume de la configuration:"
echo "================================="
echo "Nom du client              : $CLIENT_NAME"
echo "Nom de la stack            : $STACK_NAME"
echo "Port application           : $NEXT_PORT"
echo "URL acces                  : http://votre-serveur:$NEXT_PORT"
echo ""
echo "Base de donnees ERP:"
echo "  Base                     : erp_btp"
echo "  Utilisateur              : erp_user"
echo ""
echo "Base de donnees Abonnements:"
echo "  Hôte                     : $SUBSCRIPTION_DB_HOST"
echo "  Port                     : $SUBSCRIPTION_DB_PORT"
echo "  Base                     : $SUBSCRIPTION_DB_NAME"
echo "  Utilisateur              : $SUBSCRIPTION_DB_USER"
echo ""
if [ -n "$STRIPE_API_KEY" ]; then
    echo "Configuration Stripe:"
    echo "  API Key                  : $(echo $STRIPE_API_KEY | head -c 20)..."
    echo "  Publishable Key          : $(echo $STRIPE_PUBLISHABLE_KEY | head -c 20)..."
    if [ -n "$STRIPE_PRICE_ID_STARTER" ]; then
        echo "  Price Starter            : $STRIPE_PRICE_ID_STARTER"
        echo "  Price Professionnel      : $STRIPE_PRICE_ID_PROFESSIONAL"
        echo "  Price Entreprise         : $STRIPE_PRICE_ID_ENTERPRISE"
    fi
    echo ""
fi
echo "Identifiants de connexion temporaires:"
echo "  Nom d'utilisateur        : $CLIENT_NAME"
echo "  Mot de passe             : $INITIAL_PASSWORD"
echo "  (A changer lors de la premiere connexion)"
echo "================================="
echo ""
echo "Stack deployee avec succes!"
echo "  Accedez a Portainer pour surveiller le deploiement."
