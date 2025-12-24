# Déploiement Docker - ERP BTP

## 📦 Architecture

Ce projet utilise Docker Compose avec deux services :
- **PostgreSQL** : Base de données (remplace Cloud SQL)
- **Site Commercial** : Application web NiceGUI

## 🚀 Démarrage rapide

### Avec Docker Compose (ligne de commande)

```bash
# Construire et démarrer les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose down

# Arrêter et supprimer les volumes (ATTENTION: perte de données)
docker-compose down -v
```

### Avec Portainer

1. **Importer dans Portainer** :
   - Connectez-vous à Portainer
   - Allez dans "Stacks" → "Add stack"
   - Donnez un nom : `erpbtp`
   - Méthode : "Upload" ou "Git repository"
   - Collez le contenu de `docker-compose.yml`

2. **Configurer les variables (optionnel)** :
   - Section "Environment variables"
   - Modifiez si nécessaire les identifiants PostgreSQL

3. **Déployer** :
   - Cliquez sur "Deploy the stack"

## 🔧 Configuration

### Variables d'environnement

Les variables sont définies dans le `docker-compose.yml` :

**PostgreSQL :**
- `POSTGRES_USER`: fred
- `POSTGRES_PASSWORD`: Jbvf2023@
- `POSTGRES_DB`: erpbtp_clients

**Site Commercial :**
- `CLOUDSQL_HOST`: postgres (nom du service)
- `CLOUDSQL_PORT`: 5432
- `CLOUDSQL_USER`: fred
- `CLOUDSQL_PASSWORD`: Jbvf2023@
- `CLOUDSQL_DB`: erpbtp_clients

### Ports exposés

- **8000** : Site commercial (http://localhost:8000)
- **5432** : PostgreSQL (pour administration externe)

## 🗄️ Initialisation de la base de données

Au premier lancement, il faut créer les tables :

```bash
# Accéder au conteneur du site
docker exec -it erpbtp_site_commercial bash

# Lancer Python
python

# Dans Python
from cloudsql_config import Base, engine
from models import Client, Abonnement, DemoRequest
Base.metadata.create_all(engine)
exit()
```

Ou créez un script `init_db.py` :

```python
from cloudsql_config import Base, engine
from models import Client, Abonnement, DemoRequest

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("✅ Tables créées avec succès!")
```

Puis exécutez :
```bash
docker exec erpbtp_site_commercial python init_db.py
```

## 📊 Administration PostgreSQL

### Avec psql (depuis l'hôte)

```bash
psql -h localhost -p 5432 -U fred -d erpbtp_clients
```

### Avec pgAdmin (via Docker)

Ajoutez ce service au `docker-compose.yml` :

```yaml
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: erpbtp_pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@erpbtp.fr
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    networks:
      - erpbtp_network
```

Accès : http://localhost:5050

## 🔄 Mise à jour

```bash
# Reconstruire après modification du code
docker-compose up -d --build

# Ou rebuild seulement le site commercial
docker-compose up -d --build site_commercial
```

## 💾 Sauvegarde et Restauration

### Sauvegarde

```bash
# Dump de la base de données
docker exec erpbtp_postgres_commercial pg_dump -U fred erpbtp_clients > backup.sql

# Ou avec docker-compose
docker-compose exec postgres pg_dump -U fred erpbtp_clients > backup.sql
```

### Restauration

```bash
# Restaurer depuis un dump
docker exec -i erpbtp_postgres_commercial psql -U fred erpbtp_clients < backup.sql

# Ou avec docker-compose
docker-compose exec -T postgres psql -U fred erpbtp_clients < backup.sql
```

## 🐛 Dépannage

### Les conteneurs ne démarrent pas

```bash
# Voir les logs
docker-compose logs

# Logs en temps réel
docker-compose logs -f
```

### Erreur de connexion à PostgreSQL

```bash
# Vérifier que PostgreSQL est prêt
docker-compose exec postgres pg_isready -U fred

# Tester la connexion
docker-compose exec postgres psql -U fred -d erpbtp_clients -c "SELECT version();"
```

### Nettoyer tout et recommencer

```bash
# Arrêter et supprimer tout
docker-compose down -v

# Supprimer les images
docker-compose down --rmi all -v

# Redémarrer
docker-compose up -d
```

## 🔒 Sécurité - Production

**⚠️ IMPORTANT pour la production :**

1. **Changez les mots de passe** dans le `docker-compose.yml`
2. **Utilisez des secrets Docker** ou des variables d'environnement externes
3. **Ne pas exposer le port PostgreSQL** (commentez le mapping de port 5432)
4. **Activez SSL/TLS** pour PostgreSQL
5. **Utilisez un proxy inverse** (Nginx, Traefik) avec HTTPS

Exemple avec secrets :

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    secrets:
      - postgres_password

secrets:
  postgres_password:
    external: true
```

## 📝 Notes

- Les données PostgreSQL sont persistées dans le volume `postgres_data`
- Le code source est monté en volume pour le développement (à désactiver en production)
- Le healthcheck assure que le site démarre après PostgreSQL
- Compatible avec Portainer pour une gestion visuelle
