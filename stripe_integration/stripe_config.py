"""
Configuration Stripe pour la monétisation de la solution ERP BTP
"""
import os
import stripe
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Stripe
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Initialiser Stripe
stripe.api_key = STRIPE_API_KEY

# Plans d'abonnement disponibles
SUBSCRIPTION_PLANS = {
    'starter': {
        'name': 'Plan Starter',
        'price_id': os.getenv('STRIPE_PRICE_ID_STARTER', ''),
        'amount': 2900,  # 29€ en cents
        'currency': 'eur',
        'interval': 'month',
        'description': 'Parfait pour les petits chantiers'
    },
    'professional': {
        'name': 'Plan Professionnel',
        'price_id': os.getenv('STRIPE_PRICE_ID_PROFESSIONAL', ''),
        'amount': 5900,  # 59€ en cents
        'currency': 'eur',
        'interval': 'month',
        'description': 'Pour les entreprises en croissance'
    },
    'enterprise': {
        'name': 'Plan Entreprise',
        'price_id': os.getenv('STRIPE_PRICE_ID_ENTERPRISE', ''),
        'amount': 14900,  # 149€ en cents
        'currency': 'eur',
        'interval': 'month',
        'description': 'Solutions personnalisées pour les grandes entreprises'
    }
}

def check_stripe_configuration():
    """Vérifie que Stripe est correctement configuré"""
    if not STRIPE_API_KEY:
        raise ValueError("STRIPE_API_KEY non configurée dans les variables d'environnement")
    if not STRIPE_PUBLISHABLE_KEY:
        raise ValueError("STRIPE_PUBLISHABLE_KEY non configurée dans les variables d'environnement")
    return True
