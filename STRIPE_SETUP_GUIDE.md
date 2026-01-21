# Intégration Stripe pour la Monétisation - Guide d'Installation

## Vue d'ensemble

Cette intégration permet de monétiser votre solution ERP BTP avec Stripe pour gérer :
- ✅ Les paiements par carte bancaire
- ✅ Les abonnements récurrents  
- ✅ Les essais gratuits (30 jours)
- ✅ Les annulations d'abonnement
- ✅ Les webhooks pour les événements de paiement
- ✅ La gestion des factures

## Plans d'abonnement disponibles

1. **Plan Starter** - 29€/mois
   - Idéal pour les petits chantiers
   - 30 jours d'essai gratuit

2. **Plan Professionnel** - 59€/mois
   - Pour les entreprises en croissance
   - 30 jours d'essai gratuit

3. **Plan Entreprise** - 149€/mois
   - Solutions personnalisées
   - 30 jours d'essai gratuit

## Installation

### 1. Installer les dépendances

Les dépendances Stripe et pytest ont déjà été ajoutées à `requirements.txt`:

```bash
pip install -r requirements.txt
```

Packages ajoutés:
- `stripe>=7.0.0` - SDK Stripe Python
- `python-dotenv>=1.0.0` - Gestion des variables d'environnement
- `pytest>=7.0.0` - Framework de test
- `pytest-asyncio>=0.21.0` - Support async pour pytest

### 2. Configurer les clés Stripe

1. Créer un compte sur [stripe.com](https://stripe.com)
2. Obtenir vos clés depuis le dashboard Stripe:
   - Clé secrète (sk_test_...)
   - Clé publique (pk_test_...)
   - Secret webhook (whsec_...)

3. Copier `.env.example` en `.env` et configurer:

```bash
cp .env.example .env
```

Editer `.env`:
```env
STRIPE_API_KEY=sk_test_YOUR_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
```

### 3. Créer les produits dans Stripe

Depuis le dashboard Stripe:

1. Aller dans **Products**
2. Créer 3 produits:
   - Starter ($29/month)
   - Professional ($59/month)
   - Enterprise ($149/month)
3. Copier les Price IDs dans `.env`:

```env
STRIPE_PRICE_ID_STARTER=price_1234567890
STRIPE_PRICE_ID_PROFESSIONAL=price_0987654321
STRIPE_PRICE_ID_ENTERPRISE=price_1122334455
```

## Structure du code

### Répertoires créés

```
stripe_integration/
├── __init__.py              # Exports publics
├── stripe_config.py         # Configuration Stripe
└── payment_service.py       # Service de paiement

test/
├── __init__.py
└── test_payment.py          # Tests d'intégration paiement
```

### Modules principaux

#### `stripe_integration/stripe_config.py`
- Configuration centralisée de Stripe
- Définition des plans d'abonnement
- Validation de la configuration

#### `stripe_integration/payment_service.py`
- `create_customer()` - Créer un client Stripe
- `create_payment_intent()` - Créer une intention de paiement
- `create_subscription()` - Créer un abonnement
- `cancel_subscription()` - Annuler un abonnement
- `retrieve_subscription()` - Récupérer les détails d'un abonnement
- `get_payment_methods()` - Lister les cartes d'un client
- `validate_webhook()` - Valider les webhooks Stripe
- `get_invoice()` - Récupérer une facture

## Exécuter les tests

### Tests unitaires du paiement

```bash
# Tous les tests
pytest test/test_payment.py -v

# Tests spécifiques
pytest test/test_payment.py::TestPaymentService::test_create_customer -v

# Avec couverture de code
pytest test/test_payment.py --cov=stripe_integration
```

### Tests disponibles

Le fichier `test/test_payment.py` inclut 14 tests:

- ✅ Création de clients
- ✅ Création de paiements
- ✅ Création d'abonnements
- ✅ Annulation d'abonnements
- ✅ Récupération de paiements
- ✅ Validation des webhooks
- ✅ Récupération des factures
- ✅ Validation des plans d'abonnement

## Intégration dans site_commercial.py

Voir `PAYMENT_INTEGRATION_EXAMPLE.py` pour un exemple complet d'intégration d'une page de paiement.

### Utilisation basique

```python
from stripe_integration import PaymentService

# Créer un client
customer_id = PaymentService.create_customer(
    email='client@example.com',
    name='Jean Dupont'
)

# Créer un abonnement avec essai gratuit
subscription = PaymentService.create_subscription(
    customer_id=customer_id,
    plan='starter',
    trial_days=30
)

print(f"Abonnement créé: {subscription['subscription_id']}")
```

## Gestion des webhooks

Pour traiter les événements Stripe (paiement réussi, essai terminé, etc.):

```python
from stripe_integration import PaymentService
from fastapi import Request

@app.post('/stripe-webhook')
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get('stripe-signature')
    
    try:
        event = PaymentService.validate_webhook(body, signature)
        
        if event['type'] == 'customer.subscription.created':
            # Traiter la création d'abonnement
            pass
        elif event['type'] == 'payment_intent.succeeded':
            # Traiter le paiement réussi
            pass
        
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 400
```

## Configurer les webhooks Stripe

1. Dashboard Stripe → **Webhooks**
2. Ajouter un endpoint:
   - URL: `https://votre-site.com/stripe-webhook`
   - Events à écouter:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `invoice.created`
     - `invoice.payment_succeeded`

## Variables d'environnement requises

```env
# Stripe
STRIPE_API_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_STARTER=price_...
STRIPE_PRICE_ID_PROFESSIONAL=price_...
STRIPE_PRICE_ID_ENTERPRISE=price_...

# SMTP (déjà existants)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...

# PostgreSQL (déjà existants)
EXTERNAL_DB_HOST=...
EXTERNAL_DB_PORT=5433
DB_NAME=erpbtp_clients
DB_USER=fred
DB_PASSWORD=...
```

## Sécurité

⚠️ **Important:**
- ✅ Les clés Stripe ne doivent JAMAIS être exposées en public
- ✅ Utiliser des variables d'environnement (.env) pour les clés secrètes
- ✅ Ne pas commiter le fichier `.env` (ajouter à `.gitignore`)
- ✅ En production, utiliser les VRAIES clés de production (pk_live_, sk_live_)
- ✅ Valider les webhooks avec le secret pour éviter les falsifications

## Modèle de données pour stocker les paiements

À ajouter à `models.py`:

```python
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

class StripeCustomer(Base):
    __tablename__ = 'stripe_customers'
    
    id = Column(String, primary_key=True)  # Clé Stripe
    client_id = Column(Integer, ForeignKey('clients.id'))
    stripe_customer_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now)

class StripeSubscription(Base):
    __tablename__ = 'stripe_subscriptions'
    
    id = Column(String, primary_key=True)
    stripe_subscription_id = Column(String, unique=True)
    customer_id = Column(String, ForeignKey('stripe_customers.id'))
    plan = Column(String)  # starter, professional, enterprise
    status = Column(String)  # active, trialing, past_due, canceled
    trial_end = Column(DateTime)
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
```

## Ressources utiles

- [Documentation Stripe Python](https://stripe.com/docs/libraries/python)
- [Guide des abonnements](https://stripe.com/docs/billing/subscriptions/overview)
- [Reference API Stripe](https://stripe.com/docs/api)
- [Webhook events](https://stripe.com/docs/webhooks)

## Support

Pour des questions ou problèmes:
1. Vérifier les logs Stripe dans le dashboard
2. Consulter la documentation officielle Stripe
3. Tester avec les clés de test (prefix `test_`)
4. Exécuter les tests unitaires pour vérifier l'intégration
