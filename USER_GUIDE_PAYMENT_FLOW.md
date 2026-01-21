# 🎯 Guide Utilisateur - De la Page Tarifs au Paiement

## 📍 Le Chemin Complet

### 1. **Page d'Accueil → Tarifs**
```
URL: http://localhost:8000/
       ↓
Clic sur "Tarifs" (dans le menu ou sur bouton d'accueil)
       ↓
URL: http://localhost:8000/tarifs
```

### 2. **Page Tarifs**
```
URL: http://localhost:8000/tarifs

Affiche 3 plans:

┌─────────────────────────────────────────────┐
│ 🚀 Starter    │ ⭐ Pro (POPULAIRE) │ 🏢 Enterprise │
│   29€/mois    │    69€/mois       │  149€/mois    │
│               │                   │               │
│ [Commencer]   │   [Commencer]     │ [Contacter]   │
└─────────────────────────────────────────────┘

+ Badge "30 jours d'essai gratuit"
```

### 3. **Clic sur "Commencer"**

#### Cas A: Plan Payant (Starter = 29€/Pro = 69€/Enterprise = 149€)
**ET** Stripe est configuré dans `.env`

```
                         ↓
           Redirige vers formulaire de paiement
                         ↓
              (Reste sur /demo?plan=starter)
```

#### Cas B: Sans Stripe OU Essai Gratuit
```
                         ↓
           Redirige vers formulaire d'essai simple
                         ↓
              (Reste sur /demo)
```

---

## 📋 Formulaire de Paiement (Plan Payant)

Apparaît sur la même page `/demo?plan=starter|pro|enterprise`

```
┌────────────────────────────────────────────────┐
│  💳 Créez votre compte et payez                │
│                                                │
│  Infos Client:                                 │
│  ┌──────────────────────────────────────────┐ │
│  │ Nom *                │ Prénom *          │ │
│  ├──────────────────────────────────────────┤ │
│  │ Email professionnel *                   │ │
│  ├──────────────────────────────────────────┤ │
│  │ Nom de l'entreprise *                   │ │
│  ├──────────────────────────────────────────┤ │
│  │ Téléphone *          │ Effectif          │ │
│  ├──────────────────────────────────────────┤ │
│  │ Adresse              │ Code Postal       │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  💳 Informations de Paiement:                  │
│  ┌──────────────────────────────────────────┐ │
│  │  Card Number        │ MM/YY              │ │
│  │  CVC                                     │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  📦 Résumé de votre commande:                  │
│  ┌──────────────────────────────────────────┐ │
│  │ Plan choisi:       Starter               │ │
│  │ Prix mensuel:      29€                   │ │
│  │ 1ère période:      30 jours gratuits     │ │
│  │ ─────────────────────────────────────── │ │
│  │ À PAYER AUJOURD'HUI: 0€ ✅              │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ☑️ J'accepte les conditions d'utilisation    │
│                                                │
│  [Annuler]           [Créer mon compte]       │
└────────────────────────────────────────────────┘
```

### Champs Requis:
- ✅ Nom *
- ✅ Prénom *
- ✅ Email professionnel *
- ✅ Entreprise *
- ✅ Téléphone *
- ✅ Carte Bancaire (gérée par Stripe)
- ✅ Acceptation CGU

### Pour Tester:
```
Nom: Jean
Prénom: Dupont
Email: jean.dupont@entreprise.com
Entreprise: Dupont BTP
Téléphone: 06 12 34 56 78

Carte: 4242 4242 4242 4242
Expiration: 12/25
CVC: 123
```

---

## ✅ Processus de Paiement

Quand vous cliquez **"Créer mon compte"**:

```
1. Validation côté client
   └─ Tous les champs remplis? ✓
   └─ CGU acceptées? ✓

2. Envoi à Stripe.js
   └─ Tokenisation de la carte (sécurisée)
   └─ Aucune donnée bancaire n'arrive à votre serveur

3. Création Client Stripe
   └─ Email + Nom + Métadonnées

4. Création Abonnement Stripe
   └─ Plan: Starter/Pro/Enterprise
   └─ Essai: 30 jours GRATUIT
   └─ Après 30j: Prélèvement automatique du montant
   └─ Aucun montant débité aujourd'hui (essai)

5. Création Client en BD (PostgreSQL)
   ├─ Nom, Prénom, Email
   ├─ Entreprise, Téléphone
   └─ Date de création

6. Création Abonnement en BD
   ├─ Plan: starter/pro/enterprise
   ├─ Prix: 29€/69€/149€
   ├─ Statut: actif
   ├─ Période d'essai: 30 jours
   └─ Date fin essai: Aujourd'hui + 30 jours

7. Déploiement de la Stack ERP
   ├─ Création du conteneur Docker
   ├─ Configuration PostgreSQL
   ├─ Génération des identifiants
   └─ Assignation d'un port unique

8. Envoi d'Email de Bienvenue
   └─ Identifiants de connexion
   └─ URL d'accès
   └─ Avertissements importants

9. Page de Félicitations
   ├─ ✅ "Félicitations!"
   ├─ 🔐 Identifiants (copiables)
   ├─ ⚠️ "Patienter 1-2 minutes"
   └─ 🔗 Bouton "Accéder à mon ERP"
```

---

## 📄 Page de Félicitations

Après un paiement réussi:

```
URL: http://localhost:8000/felicitations?key=jean-dupont_12345

┌──────────────────────────────────────────────────┐
│                                                  │
│                    🎉                            │
│            Félicitations!                        │
│       Votre espace ERP BTP est prêt              │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ Vos identifiants de connexion            │   │
│  │                                          │   │
│  │ ⚠️ Important                            │   │
│  │ Patienter 1-2 minutes avant connexion    │   │
│  │                                          │   │
│  │ Nom d'utilisateur: jean-dupont    [📋]  │   │
│  │ Mot de passe:      Az7#Kx9_12    [📋]  │   │
│  │ URL:               http://....:8101 [📋]│   │
│  │ Plan:              STARTER (30j gratuits)│   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│       [Accéder à mon ERP BTP] (Nouveau Tab)    │
│                                                  │
│  ✓ Changez votre mot de passe à la 1ère connexion │
│  ✓ Email de confirmation envoyé                │
│  ✓ Support disponible 24/7                      │
│                                                  │
│            [Retour à l'accueil]                │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Actions Possibles:
1. **Cliquer "Accéder à mon ERP"**
   - Ouvre une nouvelle onglet
   - URL: http://176.131.66.167:8101 (exemple)
   - Identifiants affichés sur la page
   - ⚠️ Attendre 1-2 minutes

2. **Copier les Identifiants**
   - Cliquer l'icône [📋] à côté de chaque champ
   - Automatiquement copié dans le presse-papier
   - Notification "Copié!" apparaît

3. **Retour à l'Accueil**
   - Cliquer "Retour à l'accueil"
   - Retour à http://localhost:8000/

---

## 🎯 Raccourcis Directs

Au lieu d'aller sur /tarifs:

```
Plan Essai Gratuit:
http://localhost:8000/demo

Plan Starter (29€):
http://localhost:8000/demo?plan=starter

Plan Pro (69€):
http://localhost:8000/demo?plan=pro

Plan Enterprise (149€):
http://localhost:8000/demo?plan=enterprise
```

---

## ⏱️ Timeline Complète

```
Minute 0:00
└─ Remplir formulaire
└─ Entrer carte bancaire
└─ Clic "Créer mon compte"

Minute 0:05-0:10
└─ Stripe traite le paiement
└─ Client créé en BD
└─ Abonnement créé
└─ Stack commence à se déployer

Minute 0:30
└─ Page félicitations s'affiche
└─ Identifiants visibles
└─ Email envoyé

Minute 1:30-2:00
└─ Stack complètement déployée
└─ Conteneur prêt
└─ Port ouvert et accessible

Minute 2:00+
└─ ✅ VOUS POUVEZ VOUS CONNECTER
```

---

## 🔑 Après la Création

### Connexion à l'ERP

```
1. URL: http://176.131.66.167:8101 (ou le port attribué)
2. Nom d'utilisateur: jean-dupont (du formulaire)
3. Mot de passe: Az7#Kx9_12 (généré automatiquement)
4. Clic "Se Connecter"
```

### Première Connexion

⚠️ **Vous DEVEZ changer votre mot de passe!**

```
1. Se connecter avec le mot de passe temporaire
2. Aller à: Profil → Changer le mot de passe
3. Entrer le mot de passe temporaire
4. Entrer le nouveau mot de passe (2x)
5. Valider
```

### Accès Rapide

- **Factures:** Comptabilité → Factures
- **Devis:** Devis → Liste des Devis
- **Chantiers:** Chantiers → Mon Planning
- **Clients:** Contacts → Clients

---

## 🐛 Problèmes Courants

### ❌ "Je me connecte mais l'ERP ne charge pas"
```
Solution: Patienter 1-2 minutes de plus
→ Stack en cours de démarrage
→ Rafraîchir la page après 2-3 min
```

### ❌ "Mot de passe incorrect"
```
Solution: Vérifier la casse (majuscule/minuscule)
→ Copier-coller le mot de passe depuis félicitations
→ Email aussi envoyé pour référence
```

### ❌ "Le paiement est décliné"
```
Si carte de test: Utiliser 4242 4242 4242 4242
Si carte réelle: Vérifier l'expiration
              Vérifier le code postal
              Contacter votre banque
```

### ❌ "Je n'ai pas reçu l'email"
```
Solution: Vérifier spam/courrier indésirable
        Recharger la page félicitations
        Contacter support
```

---

## 📞 Support

Pour toute question ou problème:

```
Email: support@erpbtp.com (à adapter)
Chat: Support 24/7 (à ajouter)
Téléphone: +33 (0)X XX XX XX XX (à adapter)
```

---

**Bienvenue sur ERP BTP! 🚀**
