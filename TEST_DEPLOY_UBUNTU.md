# Script de test du déploiement sur Ubuntu

## 📋 Description

Ce script permet de tester le déploiement du site commercial directement sur le serveur Ubuntu **sans passer par Portainer**.

Cela permet de :
- Tester la construction des images Docker
- Identifier les erreurs de build
- Vérifier que les services démarrent correctement
- Débugger plus facilement

## 🚀 Utilisation

### 1. Copier le script sur le serveur Ubuntu

```bash
# Depuis votre machine Windows, copier le script vers Ubuntu
scp test-deploy-ubuntu.sh user@serveur-ubuntu:/tmp/

# Ou télécharger directement depuis GitHub
ssh user@serveur-ubuntu
wget https://raw.githubusercontent.com/fvictoire59va/website-promo/main/test-deploy-ubuntu.sh
chmod +x test-deploy-ubuntu.sh
```

### 2. Exécuter le script

```bash
./test-deploy-ubuntu.sh
```

Le script vous proposera 4 options :

**Option 1 : Builder les images uniquement**
- Teste la construction sans lancer les services
- Idéal pour identifier les erreurs de Dockerfile

**Option 2 : Builder et lancer les services**
- Construit les images
- Lance tous les services
- Affiche les logs

**Option 3 : Lancer sans rebuild**
- Utilise les images déjà construites
- Lance rapidement les services

**Option 4 : Nettoyer et tout reconstruire**
- Supprime tout (conteneurs, volumes, cache)
- Reconstruit à partir de zéro
- Idéal pour un test propre

## 📊 Vérifications

### Voir les logs

```bash
# Tous les services
docker-compose -f /tmp/test-site-commercial/docker-compose.yml logs -f

# Un service spécifique
docker-compose -f /tmp/test-site-commercial/docker-compose.yml logs -f site_commercial
docker-compose -f /tmp/test-site-commercial/docker-compose.yml logs -f api_client
docker-compose -f /tmp/test-site-commercial/docker-compose.yml logs -f postgres
```

### Vérifier l'état des conteneurs

```bash
docker-compose -f /tmp/test-site-commercial/docker-compose.yml ps
```

### Tester l'API

```bash
# Test de l'API Client
curl http://localhost:9100/docs

# Créer un client
curl -X POST http://localhost:9100/client-id/ \
  -H "Content-Type: application/json" \
  -d '{"nom":"Test","entreprise":"Test Corp"}'
```

### Tester le site commercial

Ouvrez dans votre navigateur :
- Site commercial : http://IP-SERVEUR:8100
- API documentation : http://IP-SERVEUR:9100/docs

## 🛑 Arrêter les services

```bash
docker-compose -f /tmp/test-site-commercial/docker-compose.yml down

# Avec suppression des volumes
docker-compose -f /tmp/test-site-commercial/docker-compose.yml down -v
```

## 🔍 Débuggage

### Si le build échoue avec "exit code: 100"

1. **Vérifier la connexion réseau** :
   ```bash
   ping archive.ubuntu.com
   ```

2. **Nettoyer le cache Docker** :
   ```bash
   docker system prune -a --volumes
   ```

3. **Vérifier les miroirs APT** :
   ```bash
   docker run --rm python:3.11-slim apt-get update
   ```

4. **Essayer avec un proxy si nécessaire** :
   ```bash
   # Ajouter dans Dockerfile.api avant RUN apt-get
   ENV http_proxy=http://proxy:port
   ENV https_proxy=http://proxy:port
   ```

### Si les services ne démarrent pas

1. **Vérifier les logs** :
   ```bash
   docker-compose -f /tmp/test-site-commercial/docker-compose.yml logs
   ```

2. **Vérifier les ports** :
   ```bash
   netstat -tulpn | grep -E '8100|9100|5433'
   ```

3. **Vérifier la base de données** :
   ```bash
   docker exec -it erpbtp_postgres_commercial psql -U fred -d erpbtp_clients
   ```

## 🧪 Tests manuels

### Test complet du workflow

1. **Accéder au site** : http://IP-SERVEUR:8100/demo

2. **Créer un client de test** :
   - Remplir le formulaire
   - Cliquer sur "Démarrer mon essai gratuit"

3. **Vérifier les logs** :
   ```bash
   docker-compose -f /tmp/test-site-commercial/docker-compose.yml logs -f site_commercial
   ```

4. **Vérifier que l'API a créé le client** :
   ```bash
   docker exec erpbtp_postgres_commercial psql -U fred -d erpbtp_clients -c "SELECT * FROM clients;"
   ```

## 📝 Notes

- Le script clone le repo dans `/tmp/test-site-commercial`
- Les données sont temporaires et seront perdues au redémarrage du serveur
- Pour une installation permanente, utilisez Portainer
- Le fichier `.env` est créé automatiquement avec vos paramètres

## 🔗 Après les tests

Une fois que tout fonctionne en test, vous pouvez :
1. Déployer via Portainer en toute confiance
2. Les mêmes images fonctionneront
3. Portainer utilisera le même `docker-compose.yml`

## 🆘 Support

Si vous rencontrez des erreurs :
1. Copiez les logs complets
2. Notez l'étape exacte qui échoue
3. Vérifiez les variables d'environnement dans `.env`
