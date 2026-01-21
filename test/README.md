# Répertoire de Tests

Ce répertoire contient tous les tests unitaires et d'intégration pour la solution ERP BTP.

## Structure

```
test/
├── __init__.py                  # Module tests
├── test_payment.py              # Tests Stripe & paiements
├── test_subscription.py         # À implémenter
├── test_client_creation.py      # À implémenter
└── conftest.py                  # Configuration pytest (À implémenter)
```

## Tests disponibles

### test_payment.py

Tests pour l'intégration Stripe:

- **TestPaymentService** (9 tests)
  - `test_create_customer` - Création d'un client Stripe
  - `test_create_customer_with_metadata` - Création avec métadonnées
  - `test_create_payment_intent` - Création d'une intention de paiement
  - `test_create_subscription` - Création d'abonnement
  - `test_create_subscription_invalid_plan` - Validation des plans
  - `test_retrieve_subscription` - Récupération d'abonnement
  - `test_cancel_subscription_immediate` - Annulation immédiate
  - `test_cancel_subscription_at_period_end` - Annulation à la fin de période
  - `test_get_payment_methods` - Récupération des moyens de paiement
  - `test_validate_webhook` - Validation des webhooks
  - `test_get_invoice` - Récupération de factures

- **TestSubscriptionPlans** (4 tests)
  - `test_plans_exist` - Tous les plans sont définis
  - `test_plan_structure` - Validation de la structure
  - `test_plan_amounts` - Montants croissants
  - `test_plan_currency` - Devise EUR

## Exécuter les tests

### Tous les tests

```bash
pytest test/ -v
```

### Tests spécifiques

```bash
# Un fichier de test
pytest test/test_payment.py -v

# Une classe de test
pytest test/test_payment.py::TestPaymentService -v

# Un test uniquement
pytest test/test_payment.py::TestPaymentService::test_create_customer -v
```

### Avec couverture de code

```bash
pytest test/ --cov=stripe_integration --cov-report=html
```

### Mode watch (re-run automatique)

```bash
pytest-watch test/
```

### Avec output détaillé

```bash
pytest test/ -vv -s
```

## Préréquisites

Installer les dépendances de test:

```bash
pip install -r requirements.txt
```

Les packages suivants sont requis:
- `pytest>=7.0.0`
- `pytest-asyncio>=0.21.0`
- `stripe>=7.0.0`

## Configurer les tests

Les tests utilisent des mocks pour ne pas faire de vrais appels à Stripe.

### Variables d'environnement pour tests

Créer un fichier `.env.test`:

```env
STRIPE_API_KEY=sk_test_test123
STRIPE_PUBLISHABLE_KEY=pk_test_test456
STRIPE_WEBHOOK_SECRET=whsec_test789
```

## Implémenter un nouveau test

Template pour ajouter un test:

```python
# test/test_ma_fonctionnalite.py

import pytest
from unittest.mock import patch, Mock
from mon_module import ma_fonctionnalite

class TestMaFonctionnalite:
    """Tests pour ma fonctionnalité"""
    
    @patch('mon_module.stripe.SomeService')
    def test_ma_fonction(self, mock_stripe):
        """Test descriptif"""
        # Arrange - Préparer les données
        mock_stripe.create.return_value = Mock(id='test_123')
        
        # Act - Exécuter la fonction
        result = ma_fonctionnalite('param1')
        
        # Assert - Vérifier le résultat
        assert result == 'expected_value'
        mock_stripe.create.assert_called_once()
```

## CI/CD Integration

Pour intégrer les tests dans CI/CD (GitHub Actions, GitLab CI, etc.):

### GitHub Actions (.github/workflows/tests.yml)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest test/ --cov=stripe_integration
```

## Bonnes pratiques

1. ✅ **Isoler les tests** - Utiliser des mocks pour ne pas dépendre de services externes
2. ✅ **Un test = une responsabilité** - Chaque test teste une seule chose
3. ✅ **Noms clairs** - `test_xxx_when_yyy_then_zzz`
4. ✅ **AAA Pattern** - Arrange, Act, Assert
5. ✅ **Pas de dépendances entre tests** - Chaque test doit être indépendant
6. ✅ **Temps rapide** - Les tests doivent être < 100ms en général
7. ✅ **Couverture > 80%** - Viser au minimum 80% de couverture de code

## Fichiers futurs

### test_subscription.py
Tests pour la gestion des abonnements:
- Création d'abonnements
- Modifications d'abonnements
- Renouvellements
- Essais gratuits

### test_client_creation.py
Tests pour la création de clients:
- Validation des données
- Création de stack Docker
- Email de bienvenue
- Configuration de la base de données

### conftest.py
Configuration partagée pour tous les tests:
- Fixtures pytest
- Mocks globaux
- Configuration de la BD de test
