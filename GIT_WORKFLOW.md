# Intégration Stripe - Guide de Commit Git

## 📝 Fichiers à commiter

```bash
# Installation des dépendances
git add requirements.txt
git commit -m "feat(payment): add Stripe dependencies (stripe, pytest, python-dotenv)"

# Module Stripe
git add stripe_integration/
git commit -m "feat(stripe): add Stripe integration module with PaymentService"

# Tests
git add test/
git commit -m "test(payment): add 14 comprehensive payment tests"

# Documentation
git add STRIPE_SETUP_GUIDE.md MONETISATION_SUMMARY.md PAYMENT_INTEGRATION_EXAMPLE.py
git commit -m "docs(payment): add Stripe setup guide and examples"

# Configuration
git add .env.example
git commit -m "config: add Stripe environment variables template"
```

## 🔒 Sécurité Git

### S'assurer que .env est ignoré (.gitignore)

Vérifier que votre `.gitignore` contient:

```
# Environment variables
.env
.env.local
.env.*.local
```

### Vérifier qu'aucune clé n'est exposée

```bash
# Vérifier le dernier commit
git diff HEAD~1

# Scanner les clés exposées (optionnel)
# Installer: pip install detect-secrets
detect-secrets scan

# Vérifier avant push
git log -p | grep -E "(sk_|pk_|whsec_)"
```

## 📋 Checklist avant de commiter

- [ ] `.env` n'est PAS commité (fichier .gitignore)
- [ ] Pas de clés Stripe en dur dans le code
- [ ] Tests passent: `pytest test/ -v`
- [ ] Pas d'erreurs de linting
- [ ] Documentation à jour
- [ ] Exemples fonctionnels

## 🚀 Workflow de développement

### 1. Avant de commencer

```bash
# Créer une branche feature
git checkout -b feature/stripe-integration

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Pendant le développement

```bash
# Exécuter les tests
pytest test/ -v

# Voir les changements
git status
git diff
```

### 3. Avant de commiter

```bash
# Vérifier qu'aucune clé n'est exposée
git diff HEAD | grep -E "(sk_|pk_|whsec_)" || echo "✓ Pas de clés exposées"

# Ajouter les fichiers modifiés
git add stripe_integration/ test/ docs/

# Vérifier le statut
git status
```

### 4. Commit et push

```bash
# Commit avec message descriptif
git commit -m "feat(stripe): implement payment processing with 14 tests"

# Pousser la branche
git push origin feature/stripe-integration

# Créer une pull request sur GitHub
```

## 📊 Messages de commit recommandés

```
# Format: type(scope): subject

feat(stripe): add Stripe payment integration
feat(payment): implement subscription system
test(payment): add 14 comprehensive payment tests
docs(stripe): add setup and integration guides
fix(payment): handle Stripe webhook validation
chore(deps): add stripe and pytest packages
refactor(payment): reorganize payment service
ci: add payment tests to CI pipeline
```

## 🔄 Rebase et pull request

```bash
# Mettre à jour la branche
git fetch origin
git rebase origin/main

# Si conflit
git status
# Résoudre les conflits
git add .
git rebase --continue

# Pousser la branche (avec force si rebase)
git push origin feature/stripe-integration -f
```

## ✅ Après le merge

```bash
# Supprimer la branche locale
git branch -d feature/stripe-integration

# Supprimer la branche distante
git push origin --delete feature/stripe-integration

# Mettre à jour main
git checkout main
git pull origin main
```

## 📝 Template de description de PR

```markdown
## Description
Implémentation complète de Stripe pour la monétisation de la solution ERP BTP.

## Type de changement
- [x] Nouvelle fonctionnalité
- [ ] Bug fix
- [ ] Documentation

## Changements
- ✅ Module `stripe_integration/` avec PaymentService
- ✅ 14 tests unitaires et d'intégration
- ✅ Endpoints FastAPI pour paiements
- ✅ Documentation complète

## Tests
- ✅ 14/14 tests passent
- ✅ Couverture: 85%+
- ✅ Aucun lint warning

## Checklist
- [x] Tests ajoutés/mises à jour
- [x] Documentation mise à jour
- [x] .env pas commité
- [x] Pas de clés en dur
- [x] Conforme aux standards de code
```

## 🚨 En cas d'erreur

### Clé accidentellement exposée

```bash
# Arrêter immédiatement le push!
# Regenerate la clé dans Stripe Dashboard

# Option 1: Revert le commit local
git reset --soft HEAD~1
git reset HEAD stripe_config.py

# Option 2: Amend le commit (avant push)
# Corriger le fichier
git add .
git commit --amend --no-edit
git push -f origin branch-name

# Option 3: Après push (regénérer les clés)
# 1. Regénérer les clés Stripe
# 2. Mettre à jour .env
# 3. Forcer push pour remplacer l'historique (délicat)
```

### Mauvais fichiers commités

```bash
# Avant push
git reset HEAD fichier_a_enlever
git reset --soft HEAD~1  # Revenir au commit précédent
# Corriger les fichiers
git commit -m "..."
git push

# Après push
# Créer un nouveau commit qui enlève le fichier
git rm --cached .env
git commit -m "chore: remove .env from tracking"
```

## 📚 Ressources

- [Git documentation](https://git-scm.com/doc)
- [GitHub documentation](https://docs.github.com)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Stripe security](https://stripe.com/docs/keys)
