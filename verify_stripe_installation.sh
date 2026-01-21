#!/bin/bash
# Script de vérification de l'installation Stripe

echo "═══════════════════════════════════════════════════════════"
echo "🔍 VÉRIFICATION DE L'INSTALLATION STRIPE"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_status=0

# 1. Vérifier les fichiers créés
echo "1️⃣  Vérification des fichiers..."
echo ""

files_to_check=(
    "stripe_integration/__init__.py"
    "stripe_integration/stripe_config.py"
    "stripe_integration/payment_service.py"
    "stripe_integration/endpoints.py"
    "test/__init__.py"
    "test/test_payment.py"
    "test/README.md"
    "STRIPE_SETUP_GUIDE.md"
    "STRIPE_INDEX.md"
    "MONETISATION_SUMMARY.md"
    "PAYMENT_INTEGRATION_EXAMPLE.py"
    "GIT_WORKFLOW.md"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (MANQUANT)"
        check_status=1
    fi
done

echo ""

# 2. Vérifier les dépendances
echo "2️⃣  Vérification des dépendances dans requirements.txt..."
echo ""

if grep -q "stripe>=7.0.0" requirements.txt; then
    echo -e "${GREEN}✓${NC} stripe>=7.0.0"
else
    echo -e "${RED}✗${NC} stripe>=7.0.0 (MANQUANT)"
    check_status=1
fi

if grep -q "pytest>=7.0.0" requirements.txt; then
    echo -e "${GREEN}✓${NC} pytest>=7.0.0"
else
    echo -e "${RED}✗${NC} pytest>=7.0.0 (MANQUANT)"
    check_status=1
fi

if grep -q "python-dotenv>=1.0.0" requirements.txt; then
    echo -e "${GREEN}✓${NC} python-dotenv>=1.0.0"
else
    echo -e "${RED}✗${NC} python-dotenv>=1.0.0 (MANQUANT)"
    check_status=1
fi

if grep -q "pytest-asyncio>=0.21.0" requirements.txt; then
    echo -e "${GREEN}✓${NC} pytest-asyncio>=0.21.0"
else
    echo -e "${RED}✗${NC} pytest-asyncio>=0.21.0 (MANQUANT)"
    check_status=1
fi

echo ""

# 3. Vérifier la structure des répertoires
echo "3️⃣  Vérification de la structure des répertoires..."
echo ""

if [ -d "stripe_integration" ]; then
    file_count=$(find stripe_integration -type f | wc -l)
    echo -e "${GREEN}✓${NC} stripe_integration/ ($file_count fichiers)"
else
    echo -e "${RED}✗${NC} stripe_integration/ (RÉPERTOIRE MANQUANT)"
    check_status=1
fi

if [ -d "test" ]; then
    file_count=$(find test -type f | wc -l)
    echo -e "${GREEN}✓${NC} test/ ($file_count fichiers)"
else
    echo -e "${RED}✗${NC} test/ (RÉPERTOIRE MANQUANT)"
    check_status=1
fi

echo ""

# 4. Vérifier que .env n'est pas commité
echo "4️⃣  Vérification de la sécurité..."
echo ""

if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC}  .env existe (vérifier qu'il n'est pas commité)"
    if grep -q "\.env" .gitignore 2>/dev/null; then
        echo -e "${GREEN}✓${NC} .env est dans .gitignore"
    else
        echo -e "${RED}✗${NC} .env n'est PAS dans .gitignore (RISQUE DE SÉCURITÉ!)"
        check_status=1
    fi
else
    echo -e "${YELLOW}⚠${NC}  .env n'existe pas (normal, à créer)"
fi

echo ""

# 5. Vérifier les clés en dur
echo "5️⃣  Vérification des clés en dur..."
echo ""

if grep -r "sk_" stripe_integration/ 2>/dev/null | grep -v "os.getenv"; then
    echo -e "${RED}✗${NC} Clés Stripe en dur trouvées!"
    check_status=1
else
    echo -e "${GREEN}✓${NC} Pas de clés en dur dans le code"
fi

echo ""

# 6. Résumé
echo "═══════════════════════════════════════════════════════════"
if [ $check_status -eq 0 ]; then
    echo -e "${GREEN}✅ VÉRIFICATION RÉUSSIE!${NC}"
    echo ""
    echo "Prochaines étapes:"
    echo "1. Installer les dépendances: pip install -r requirements.txt"
    echo "2. Configurer Stripe: cp .env.example .env"
    echo "3. Ajouter vos clés Stripe au fichier .env"
    echo "4. Exécuter les tests: pytest test/ -v"
    echo ""
    echo "📖 Consulter STRIPE_SETUP_GUIDE.md pour plus d'infos"
else
    echo -e "${RED}❌ VÉRIFICATION ÉCHOUÉE${NC}"
    echo "Merci de corriger les erreurs ci-dessus"
fi

echo "═══════════════════════════════════════════════════════════"

exit $check_status
