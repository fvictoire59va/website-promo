# Flux de Paiement Stripe - Documentation Complète

## 🎯 Vue d'ensemble

Le système intègre maintenant un flux complet de paiement avec Stripe pour les plans payants (Starter, Pro, Enterprise) et un flux d'essai gratuit pour les utilisateurs qui ne veulent pas entrer leurs données de paiement.

## 📊 Architecture du Flux

```
┌─────────────────────────────────────────────────────────────┐
│              Page Tarifs (/tarifs)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Starter    │  │  Pro (★)     │  │ Enterprise   │      │
│  │   29€/mois   │  │   69€/mois   │  │   149€/mois  │      │
│  └────┬─────────┘  └────┬─────────┘  └────┬─────────┘      │
└───────┼────────────────┼────────────────┼────────────────────┘
        │                │                │
        └─── Clic "Commencer" ────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
    Plan Payant?                      Plan Essai?
        │                                  │
        ▼                                  ▼
┌─────────────────────────┐      ┌──────────────────┐
│  Formulaire Paiement    │      │  Formulaire      │
│  (Plan + Stripe Form)   │      │  Essai Simple    │
│                         │      │                  │
│  • Infos Client         │      │  • Infos Client  │
│  • Carte Bancaire       │      │  • CGU            │
│  • 30j Essai Gratuit    │      │  • Créer Compte  │
│  • 0€ Aujourd'hui       │      │  • Stack Deploy  │
└────────┬────────────────┘      └────────┬─────────┘
         │                                │
         │ Paiement Traité               │ Compte Créé
         │                                │
         ▼                                ▼
    ┌─────────────────────────────────────────┐
    │  Page Félicitations (/felicitations)   │
    │  Affiche les identifiants de connexion  │
    │  Email de bienvenue envoyé              │
    └─────────────────────────────────────────┘
```

## 🔄 Flux Détaillé

### 1️⃣ Page Tarifs (`/tarifs`)
- Affiche les 3 plans disponibles
- Boutons "Commencer" pour chaque plan
- 30 jours d'essai gratuit pour tous

### 2️⃣ Sélection du Plan
Quand l'utilisateur clique "Commencer":

**Si Plan Payant (Starter/Pro/Enterprise) + Stripe Disponible:**
- Affiche le formulaire avec champ de paiement Stripe
- 30 jours d'essai gratuit → 0€ payé aujourd'hui
- Après le 30e jour : prélèvement automatique

**Si Plan Essai ou Stripe Non Disponible:**
- Affiche formulaire simple sans paiement
- Création immédiate du compte avec 30j d'essai

### 3️⃣ Formulaire d'Inscription (`/demo?plan=starter|pro|enterprise`)

**Champs Obligatoires:**
- Nom *
- Prénom *
- Email professionnel *
- Entreprise *
- Téléphone *
- Nombre d'employés

**Pour les Plans Payants - Formulaire de Paiement:**
```javascript
// Élément Stripe montré pour les plans payants
<div id="card-element">...</div>

// Acceptation des conditions d'utilisation obligatoire
```

### 4️⃣ Traitement du Paiement

```python
# Fonction: show_stripe_form()
# Étapes:

1. Créer client Stripe
   stripe.Customer.create(
       email=email,
       name=f"{prenom} {nom}",
       metadata={...}
   )

2. Créer abonnement avec période d'essai
   stripe.Subscription.create(
       customer=customer_id,
       items=[{price_data...}],
       trial_period_days=30,
       payment_behavior='default_incomplete'
   )

3. Créer client dans base de données
   Client(nom, prenom, email, entreprise, telephone)

4. Créer abonnement dans base de données
   Abonnement(
       client_id=client.id,
       plan=plan,
       prix_mensuel=Decimal(price),
       date_debut=now(),
       statut='actif',
       periode_essai=True,
       date_fin_essai=now() + 30 days
   )

5. Déployer la stack ERP
   create_client_stack(client_id, client_name, ...)

6. Envoyer email de bienvenue
   send_welcome_email(email, client_name, password, url, plan)
```

### 5️⃣ Page de Confirmation (`/felicitations`)
Affiche:
- ✅ Message de succès
- 🔐 Identifiants de connexion (copiables)
  - Nom d'utilisateur
  - Mot de passe temporaire
  - URL de connexion
  - Plan d'abonnement
- ⚠️ Avertissement : patienter 1-2 min avant connexion
- 📧 Email de confirmation envoyé

## 🔧 Configuration Requise

### Fichier `.env`
```env
# Clés Stripe (Test ou Production)
# IMPORTANT: Utiliser vos propres clés depuis https://dashboard.stripe.com
STRIPE_SECRET_KEY=sk_test_YOUR_TEST_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_PUBLISHABLE_KEY_HERE

# Configuration SMTP (pour emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=mot_de_passe_app
FROM_EMAIL=votre-email@gmail.com
```

### Dépendances Python
```bash
# Déjà présentes dans requirements.txt
stripe>=6.0.0
nicegui>=1.4.0
sqlalchemy>=2.0.0
```

## 📱 Flux Utilisateur Complet

### Scenario 1: Plan Gratuit (Essai)
```
1. Utilisateur clique "Commencer" sur page /tarifs
2. Remplit formulaire simple (pas de paiement)
3. Accepte CGU
4. Clic "Démarrer mon essai gratuit"
5. Stack créée et déployée
6. Reçoit email + page félicitations
7. Accès immédiat pendant 30 jours gratuits
```

### Scenario 2: Plan Payant (Starter/Pro)
```
1. Utilisateur clique "Commencer" sur page /tarifs
2. Remplit formulaire AVEC formulaire Stripe
3. Entre sa carte bancaire
4. Accepte CGU
5. Clic "Créer mon compte"
6. Stripe traite:
   - Crée client Stripe
   - Crée subscription avec 30j essai
   - Aucune charge le 1er jour (essai)
7. Backend crée:
   - Client en BD
   - Abonnement en BD
   - Stack ERP
8. Reçoit email + page félicitations
9. Accès immédiat pendant 30 jours
10. Après 30j: prélèvement de 29€/69€/149€ selon le plan

## 🛡️ Sécurité

### Gestion des Données Bancaires
- ✅ Les données bancaires sont traitées par Stripe directement
- ✅ Aucune donnée bancaire stockée en BD
- ✅ Utilisation de Stripe.js côté client (PCI compliance)
- ✅ Signature webhook pour vérifier les paiements

### Données Clients
- ✅ Hashage des mots de passe
- ✅ Validation des emails
- ✅ Vérification des doublons
- ✅ Logs d'audit via table `connexions`

## 🔔 Webhooks Stripe (À Implémenter)

Les webhooks suivants doivent être configurés dans le tableau de bord Stripe:

```python
# URL: https://votredomaine.com/stripe-webhook

# Événements à gérer:
- customer.subscription.created
- customer.subscription.updated  
- customer.subscription.deleted
- payment_intent.succeeded
- payment_intent.payment_failed
- invoice.payment_succeeded
- invoice.payment_failed
```

## 📊 Statuts d'Abonnement

```python
# Valeurs possibles dans la BD:
'actif'      # Abonnement actif (en cours ou période d'essai)
'suspendu'   # Abonnement suspendu (non-paiement)
'annule'     # Annulé par l'utilisateur
'expire'     # Expiré (après période d'essai sans paiement)
```

## 🐛 Troubleshooting

### "Stripe non disponible"
- Vérifier que `STRIPE_SECRET_KEY` est dans `.env`
- Vérifier que la clé commence par `sk_test_` (test) ou `sk_live_` (production)

### "Paiement rejeté"
- Vérifier que la carte de test Stripe est valide
- Carte test: `4242 4242 4242 4242` / `12/25` / `123`

### Email non reçu
- Vérifier la configuration SMTP
- Vérifier que le mot de passe app Gmail est correct
- Vérifier les logs: `Add-AppPassword` pour Gmail

### Utilisateur ne peut pas se connecter après paiement
- Patienter 1-2 minutes (déploiement de la stack)
- Vérifier que le port est accessible
- Vérifier les logs Docker: `docker-compose logs`

## 📈 Monitoring

### Indicateurs à Suivre
1. **Taux de conversion**: Clics "Commencer" → Paiements complétés
2. **Taux d'essai**: Essais gratuits → Conversions payantes
3. **Taux d'abandon**: Commencé formulaire → Abandon
4. **Erreurs Stripe**: Nombre de paiements échoués

### Logs Importants
```bash
# Docker logs
docker-compose logs -f site_commercial

# Regarder pour:
- "DEBUG Client créé avec ID:"
- "✅ Stack créée avec succès"
- "Erreur lors de la création du client Stripe:"
```

## 🎓 Exemples de Cartes de Test Stripe

```
Succès:           4242 4242 4242 4242
Décliné:         4000 0000 0000 0002
Expiration:      4000 0000 0000 0069
CVC Décliné:     4000 0000 0000 0127
```

[Date: Janvier 2025]
