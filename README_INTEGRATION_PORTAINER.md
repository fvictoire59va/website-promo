# Intégration du déploiement automatique Portainer

## Modifications apportées

### Fichier `site_commercial.py`

J'ai ajouté l'intégration automatique du déploiement de stacks Portainer lors de la soumission du formulaire d'essai gratuit.

#### Nouvelles fonctionnalités

1. **Génération automatique de mots de passe sécurisés**
   - `generate_secret_key(length=32)` : Génère une clé secrète pour l'application
   - `generate_password(length=16)` : Génère un mot de passe PostgreSQL sécurisé

2. **Exécution du script Bash depuis Python**
   - `create_client_stack()` : Fonction qui exécute `create-client-stack.sh`
   - Compatible avec Git Bash et WSL sur Windows
   - Timeout de 5 minutes pour éviter les blocages
   - Gestion des erreurs complète

3. **Workflow de création d'abonnement modifié**
   - Lorsqu'un utilisateur remplit le formulaire et clique sur "Démarrer mon essai gratuit" :
     1. Validation du formulaire
     2. Création du client dans la base de données
     3. Création de l'abonnement
     4. **NOUVEAU** : Exécution automatique du script `create-client-stack.sh`
     5. Affichage des identifiants temporaires à l'utilisateur

#### Paramètres générés automatiquement

Pour chaque nouvelle inscription :
- **Nom du client** : Basé sur le nom de l'entreprise (minuscules, sans espaces)
- **Mot de passe PostgreSQL** : 16 caractères aléatoires
- **Clé secrète** : 32 caractères alphanumériques
- **Mot de passe initial** : 12 caractères aléatoires (affiché à l'utilisateur)

#### Notifications utilisateur

L'utilisateur voit maintenant :
- Une notification "en cours" pendant la création
- Un message de succès avec les identifiants temporaires
- Ou un message d'erreur détaillé en cas de problème

## Prérequis

### Sur Windows

Le système doit avoir **Git Bash** ou **WSL** installé :

#### Option 1 : Git Bash (recommandé)
```bash
# Télécharger et installer Git for Windows
# https://git-scm.com/download/win
```

#### Option 2 : WSL
```powershell
# Dans PowerShell en tant qu'administrateur
wsl --install
```

### Script Bash exécutable

Sur Linux/WSL, rendre le script exécutable :
```bash
chmod +x create-client-stack.sh
```

## Variables d'environnement du script

Le script `create-client-stack.sh` utilise les paramètres suivants :

```bash
-c CLIENT_NAME          # Généré automatiquement depuis le nom de l'entreprise
-p POSTGRES_PASSWORD    # Généré automatiquement (16 caractères)
-s SECRET_KEY          # Généré automatiquement (32 caractères)
-i INITIAL_PASSWORD    # Généré automatiquement (12 caractères, affiché à l'utilisateur)
```

Les autres paramètres utilisent les valeurs par défaut du script :
- URL Portainer : `https://localhost:9443`
- Utilisateur Portainer : `fred`
- Mot de passe Portainer : `7b5KDg@z@Sno$NtC`
- Environment ID : `2`
- Port de base : `8080`

## Exemple de flux complet

1. L'utilisateur remplit le formulaire :
   ```
   Nom : Dupont
   Prénom : Jean
   Email : jean.dupont@exemple.fr
   Entreprise : Dupont Construction
   Téléphone : 0123456789
   ```

2. Le système génère automatiquement :
   ```
   client_name: dupont-construction
   postgres_password: aB3$xY9#mK2@pL5!
   secret_key: 4Kp2xQ8mN5jL9rT3vW7yB6cF1gH0dZ4e
   initial_password: xY9pL2#aK5mN
   ```

3. Le script crée une stack Portainer :
   ```
   Nom de la stack : client-dupont-construction
   Port application : 8080 (ou suivant selon le nombre de clients)
   Port PostgreSQL : 5432 (ou suivant)
   ```

4. L'utilisateur reçoit :
   ```
   ✅ Essai gratuit activé ! Plan ESSAI - 30 jours gratuits
   
   Votre instance est en cours de déploiement sur Portainer.
   Identifiants temporaires :
   - Utilisateur : dupont-construction
   - Mot de passe : xY9pL2#aK5mN
   
   Vous recevrez un email avec les détails d'accès.
   ```

## Gestion des erreurs

Le code gère plusieurs cas d'erreur :
- ✅ Absence de Git Bash ou WSL
- ✅ Timeout d'exécution du script (5 minutes)
- ✅ Erreurs du script Bash
- ✅ Client déjà existant avec abonnement actif
- ✅ Rollback de la transaction en cas d'erreur

## Améliorations possibles

1. **Envoi d'email automatique** avec les identifiants
2. **Stockage sécurisé** des identifiants dans la base de données
3. **Dashboard d'administration** pour voir toutes les stacks créées
4. **Logs détaillés** de chaque création de stack
5. **Tests unitaires** pour la fonction `create_client_stack()`
6. **Exécution asynchrone** pour ne pas bloquer l'interface utilisateur

## Tests

Pour tester l'intégration :

1. Lancer le site commercial :
   ```bash
   python site_commercial.py
   ```

2. Accéder à http://localhost:8000/demo

3. Remplir le formulaire avec des informations de test

4. Vérifier dans Portainer qu'une nouvelle stack a été créée

5. Tester la connexion avec les identifiants affichés

## Logs et débogage

Pour voir les logs d'exécution du script, vérifier :
- Les sorties stdout/stderr capturées par Python
- Les logs de Portainer
- Les logs du conteneur créé

En cas d'erreur, le message complet est affiché à l'utilisateur.
