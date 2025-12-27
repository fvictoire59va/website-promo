# Guide de démarrage rapide - Intégration Portainer

## ✅ C'est fait !

Lorsqu'un utilisateur clique sur le bouton **"Démarrer mon essai gratuit"** avec un formulaire valide, le système :

1. ✅ Valide tous les champs du formulaire
2. ✅ Crée le client dans la base de données
3. ✅ Crée l'abonnement avec 30 jours d'essai gratuit
4. ✅ **Exécute automatiquement le script `create-client-stack.sh`**
5. ✅ Crée une nouvelle stack Portainer pour ce client
6. ✅ Affiche les identifiants temporaires à l'utilisateur

## 🚀 Comment tester ?

### 1. Démarrer le site commercial

```bash
cd "D:\PROJETS\DOCKER - SAAS - ERP BTP"
python site_commercial.py
```

### 2. Ouvrir le navigateur

Accéder à : http://localhost:8000/demo

### 3. Remplir le formulaire

Exemple de données :
- **Nom** : Dupont
- **Prénom** : Jean
- **Email** : jean.dupont@test.fr
- **Entreprise** : Test Construction
- **Téléphone** : 0123456789
- Cocher "J'accepte les conditions générales"

### 4. Cliquer sur "Démarrer mon essai gratuit"

Vous verrez :
```
🔄 Création de votre instance en cours...
🔄 Création de votre stack Portainer...
```

Puis :
```
✅ Essai gratuit activé ! Plan ESSAI - 30 jours gratuits

Votre instance est en cours de déploiement sur Portainer.
Identifiants temporaires :
- Utilisateur : test-construction
- Mot de passe : [mot de passe généré]

Vous recevrez un email avec les détails d'accès.
```

### 5. Vérifier dans Portainer

1. Se connecter à Portainer : https://localhost:9443
2. Aller dans "Stacks"
3. Vous devriez voir une nouvelle stack nommée `client-test-construction`

## 📋 Prérequis vérifiés

✅ Git Bash installé : `C:\Program Files\Git\bin\bash.exe`  
✅ Script bash présent : `create-client-stack.sh`  
✅ Tests passés avec succès

## 🔧 Configuration Portainer

Le script utilise ces paramètres par défaut (modifiables dans `create-client-stack.sh`) :

```bash
PORTAINER_URL="https://localhost:9443"
PORTAINER_USER="fred"
PORTAINER_PASSWORD="7b5KDg@z@Sno$NtC"
ENVIRONMENT_ID="2"
BASE_PORT=8080
```

## 🔐 Sécurité

Les mots de passe sont générés automatiquement de manière sécurisée :
- **PostgreSQL** : 16 caractères (lettres, chiffres, symboles)
- **Clé secrète** : 32 caractères alphanumériques
- **Mot de passe initial** : 12 caractères (affiché à l'utilisateur une seule fois)

## ⚠️ Gestion des erreurs

Le système gère automatiquement :
- ❌ Formulaire incomplet → Message d'erreur clair
- ❌ Email déjà utilisé → Mise à jour de l'abonnement existant
- ❌ Erreur de création de stack → Message détaillé
- ❌ Timeout → Arrêt après 5 minutes

## 📞 En cas de problème

### Le script ne s'exécute pas ?

Vérifier que Git Bash est installé :
```powershell
Test-Path "C:\Program Files\Git\bin\bash.exe"
```

Devrait retourner `True`.

### Erreur de connexion Portainer ?

Vérifier les identifiants dans `create-client-stack.sh` :
```bash
PORTAINER_USER="fred"
PORTAINER_PASSWORD="7b5KDg@z@Sno$NtC"
```

### Le client existe déjà ?

C'est normal ! Le système met à jour l'abonnement au lieu de créer un doublon.

## 📚 Documentation complète

Pour plus de détails, consultez :
- `README_INTEGRATION_PORTAINER.md` - Documentation complète
- `test_portainer_integration.py` - Script de test

## 🎉 C'est tout !

Le système est maintenant prêt à créer automatiquement des stacks Portainer pour chaque nouveau client !
