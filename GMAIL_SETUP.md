# Configuration Gmail pour l'envoi d'emails - Guide pas à pas

## 🎯 Prérequis

- Un compte Gmail actif
- Accès aux paramètres de sécurité Google

## 📋 Étapes de configuration

### Étape 1 : Activer l'authentification à deux facteurs

1. Connectez-vous à votre compte Google
2. Accédez à https://myaccount.google.com/security
3. Dans la section "Connexion à Google", cliquez sur **"Validation en deux étapes"**
4. Suivez les instructions pour activer la validation en deux étapes
5. Vous pouvez utiliser :
   - Votre téléphone (SMS ou appel)
   - Application Google Authenticator
   - Clé de sécurité physique

⚠️ **Important** : La validation en deux étapes est obligatoire pour créer des mots de passe d'application.

### Étape 2 : Générer un mot de passe d'application

1. Retournez sur https://myaccount.google.com/security
2. Dans "Connexion à Google", cherchez **"Mots de passe des applications"**
   - Si vous ne voyez pas cette option, assurez-vous que la validation en deux étapes est bien activée
3. Cliquez sur "Mots de passe des applications"
4. Vous devrez peut-être vous reconnecter
5. Dans le menu déroulant, sélectionnez :
   - **Application** : Choisissez "Autre (nom personnalisé)"
   - Entrez un nom : **"ERP BTP"** ou **"Site Commercial"**
6. Cliquez sur **"Générer"**
7. Google affichera un mot de passe de 16 caractères (ex: `xxxx xxxx xxxx xxxx`)
8. **IMPORTANT** : Copiez ce mot de passe immédiatement, vous ne pourrez plus le voir après

### Étape 3 : Configurer le fichier .env

Ouvrez le fichier `.env` à la racine du projet et modifiez les lignes SMTP :

```bash
# Configuration SMTP Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
FROM_EMAIL=votre-email@gmail.com
```

**Exemple concret :**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=contact.erpbtp@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
FROM_EMAIL=contact.erpbtp@gmail.com
```

⚠️ **Attention** : 
- Utilisez le mot de passe d'application (16 caractères), PAS votre mot de passe Gmail habituel
- Vous pouvez garder ou retirer les espaces dans le mot de passe, les deux fonctionnent

### Étape 4 : Redémarrer l'application

#### Avec Docker :
```bash
docker-compose down
docker-compose up -d
```

#### Sans Docker :
```bash
python site_commercial.py
```

## ✅ Vérification

### Test rapide

1. Créez un nouveau client via le formulaire d'inscription
2. Utilisez une adresse email que vous contrôlez
3. Vérifiez les logs :
   ```bash
   # Avec Docker
   docker logs erpbtp_site_commercial -f
   
   # Sans Docker
   # Regardez la sortie du terminal
   ```

4. Cherchez ces messages :
   - ✅ `Email de bienvenue envoyé à xxx@xxx.com` → Succès !
   - ❌ `Erreur lors de l'envoi de l'email` → Problème (voir dépannage)

5. Vérifiez votre boîte de réception (et le dossier spam si besoin)

### Vérification des variables d'environnement

```bash
# Avec Docker
docker exec erpbtp_site_commercial printenv | grep SMTP

# Sans Docker
echo $SMTP_SERVER
echo $SMTP_PORT
```

## 🔧 Dépannage

### ❌ Erreur : "Username and Password not accepted"

**Causes :**
- Vous utilisez votre mot de passe Gmail normal au lieu du mot de passe d'application
- La validation en deux étapes n'est pas activée
- Le mot de passe d'application est incorrect

**Solutions :**
1. Vérifiez que vous avez bien copié le mot de passe d'application (16 caractères)
2. Régénérez un nouveau mot de passe d'application si nécessaire
3. Assurez-vous que la validation en deux étapes est activée

### ❌ Erreur : "Application-specific password required"

**Cause :** Vous utilisez votre mot de passe Gmail normal

**Solution :** Utilisez le mot de passe d'application de 16 caractères

### ⚠️ Message : "SMTP non configuré - Email non envoyé"

**Cause :** Les variables d'environnement ne sont pas chargées

**Solutions :**
1. Vérifiez que le fichier `.env` existe et contient les bonnes valeurs
2. Redémarrez complètement l'application
3. Avec Docker : `docker-compose down && docker-compose up -d`

### 📭 L'email arrive en spam

**C'est normal la première fois !**

**Solutions à long terme :**
1. Demandez à vos utilisateurs d'ajouter votre email à leurs contacts
2. Pour un usage professionnel, utilisez un domaine personnalisé avec :
   - Configuration SPF
   - Configuration DKIM
   - Configuration DMARC
3. Considérez l'utilisation d'un service dédié (SendGrid, Mailgun) pour l'envoi en masse

### 🔒 "Les mots de passe des applications ne sont pas disponibles"

**Cause :** Validation en deux étapes non activée

**Solution :** Activez d'abord la validation en deux étapes (voir Étape 1)

## 💡 Bonnes pratiques

### Sécurité

✅ **À FAIRE :**
- Utilisez un compte Gmail dédié pour l'application (ex: `noreply.erpbtp@gmail.com`)
- Gardez le mot de passe d'application secret
- Ne commitez JAMAIS le fichier `.env` dans Git
- Révoquez les mots de passe d'application inutilisés

❌ **À NE PAS FAIRE :**
- Partager votre mot de passe d'application
- Utiliser votre mot de passe Gmail principal
- Commiter les identifiants dans le code source

### Limitations Gmail

⚠️ **Limites d'envoi Gmail :**
- **500 emails par jour** pour un compte gratuit
- **2000 emails par jour** pour Google Workspace
- Si vous dépassez, utilisez un service professionnel (SendGrid, Mailgun)

### Révoquer un mot de passe d'application

Si vous devez révoquer un mot de passe :
1. Allez sur https://myaccount.google.com/security
2. "Mots de passe des applications"
3. Cliquez sur l'icône poubelle à côté du mot de passe à supprimer
4. Générez-en un nouveau si nécessaire

## 📱 Alternative : Google Workspace

Pour un usage professionnel avec votre propre domaine :

1. Créez un compte Google Workspace (payant)
2. Configurez votre domaine personnalisé
3. Utilisez les mêmes paramètres SMTP :
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=noreply@votredomaine.com
   SMTP_PASSWORD=mot-de-passe-application
   FROM_EMAIL=noreply@votredomaine.com
   ```

**Avantages :**
- Email professionnel avec votre domaine
- Meilleure délivrabilité
- Limites d'envoi plus élevées
- Support professionnel

## 🔗 Liens utiles

- [Aide Google : Mots de passe des applications](https://support.google.com/accounts/answer/185833)
- [Aide Google : Validation en deux étapes](https://support.google.com/accounts/answer/185839)
- [Limites d'envoi Gmail](https://support.google.com/a/answer/166852)

## 📞 Support

En cas de problème :
1. Vérifiez que la validation en deux étapes est activée
2. Régénérez un nouveau mot de passe d'application
3. Consultez les logs de l'application pour voir l'erreur exacte
4. Référez-vous à la [documentation complète](CONFIGURATION_EMAIL.md)
