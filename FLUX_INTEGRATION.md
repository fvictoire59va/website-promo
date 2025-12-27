# Diagramme de flux - Création automatique de stack Portainer

```
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEUR                               │
│                                                              │
│  Remplit le formulaire "Démarrer mon essai gratuit"        │
│  - Nom, Prénom, Email                                       │
│  - Entreprise, Téléphone                                    │
│  - Accepte les CGV                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            VALIDATION DU FORMULAIRE                          │
│                                                              │
│  ✓ Tous les champs remplis ?                               │
│  ✓ CGV acceptées ?                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          CRÉATION DANS LA BASE DE DONNÉES                    │
│                                                              │
│  1. Vérifier si le client existe déjà                       │
│  2. Créer/Mettre à jour le Client                           │
│  3. Créer l'Abonnement (30 jours d'essai)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         GÉNÉRATION DES PARAMÈTRES SÉCURISÉS                  │
│                                                              │
│  • client_name = entreprise.lower().replace(' ', '-')      │
│    Exemple : "Dupont Construction" → "dupont-construction"  │
│                                                              │
│  • postgres_password = generate_password(16)                │
│    Exemple : "aB3$xY9#mK2@pL5!"                            │
│                                                              │
│  • secret_key = generate_secret_key(32)                     │
│    Exemple : "4Kp2xQ8mN5jL9rT3vW7yB6cF1gH0dZ4e"           │
│                                                              │
│  • initial_password = generate_password(12)                 │
│    Exemple : "xY9pL2#aK5mN"                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          EXÉCUTION DU SCRIPT BASH                            │
│                                                              │
│  Fonction : create_client_stack()                           │
│                                                              │
│  1. Détection de l'environnement                            │
│     ├─ Git Bash trouvé ?                                    │
│     └─ WSL disponible ?                                     │
│                                                              │
│  2. Construction de la commande                             │
│     bash create-client-stack.sh \                           │
│       -c "dupont-construction" \                            │
│       -p "aB3$xY9#mK2@pL5!" \                              │
│       -s "4Kp2xQ8mN5jL9rT3vW7yB6cF1gH0dZ4e" \             │
│       -i "xY9pL2#aK5mN"                                     │
│                                                              │
│  3. Exécution avec timeout de 5 minutes                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           SCRIPT BASH create-client-stack.sh                 │
│                                                              │
│  [1/4] Authentification à Portainer                         │
│        → Récupération du token JWT                          │
│                                                              │
│  [2/4] Récupération des stacks existantes                   │
│        → Calcul du prochain port disponible                 │
│        → Port app: 8080 + nombre_clients                    │
│        → Port DB: 5432 + nombre_clients                     │
│                                                              │
│  [3/4] Création de la stack                                 │
│        → Nom: "client-dupont-construction"                  │
│        → Repository: https://github.com/.../ERP-BTP         │
│        → Branch: main                                        │
│        → Compose file: docker-compose.portainer.yml         │
│        → Variables d'environnement injectées                │
│                                                              │
│  [4/4] Attente et initialisation PostgreSQL                 │
│        → Attente que PostgreSQL soit prêt                   │
│        → Vérification de la table 'users'                   │
│        → Création de l'utilisateur initial                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              CRÉATION DANS PORTAINER                         │
│                                                              │
│  Stack créée avec :                                         │
│  • Nom : client-dupont-construction                         │
│  • Conteneurs :                                             │
│    - dupont-construction-app (port 8080)                    │
│    - dupont-construction-postgres (port 5432)               │
│  • Réseau : dupont-construction-network                     │
│  • Volumes : dupont-construction-postgres-data              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           NOTIFICATION À L'UTILISATEUR                       │
│                                                              │
│  ✅ Essai gratuit activé ! Plan ESSAI - 30 jours gratuits  │
│                                                              │
│  Votre instance est en cours de déploiement sur Portainer. │
│  Identifiants temporaires :                                 │
│  - Utilisateur : dupont-construction                        │
│  - Mot de passe : xY9pL2#aK5mN                             │
│                                                              │
│  Vous recevrez un email avec les détails d'accès.          │
└─────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════
                    GESTION DES ERREURS
═══════════════════════════════════════════════════════════════

Formulaire invalide
│
└─► ❌ "Veuillez remplir tous les champs obligatoires"

CGV non acceptées
│
└─► ❌ "Veuillez accepter les conditions générales"

Client déjà existant avec abonnement actif
│
└─► ⚠️ "Vous avez déjà un abonnement actif (plan)"

Git Bash/WSL non trouvé
│
└─► ❌ "Git Bash ou WSL non trouvé. Veuillez installer..."

Erreur du script Bash
│
└─► ❌ "Erreur lors de la création de la stack : [détails]"

Timeout (> 5 minutes)
│
└─► ❌ "Timeout : La création de la stack a pris trop de temps"

Erreur base de données
│
└─► ❌ "Erreur lors de l'enregistrement : [détails]"
    (+ Rollback automatique de la transaction)


═══════════════════════════════════════════════════════════════
                 ARCHITECTURE MULTI-TENANT
═══════════════════════════════════════════════════════════════

Client 1: "dupont-construction"
├─ Stack: client-dupont-construction
├─ App: http://localhost:8080
├─ DB: postgres://localhost:5432
└─ User: dupont-construction / password123

Client 2: "martin-renovation"
├─ Stack: client-martin-renovation
├─ App: http://localhost:8081
├─ DB: postgres://localhost:5433
└─ User: martin-renovation / password456

Client 3: "abc-services"
├─ Stack: client-abc-services
├─ App: http://localhost:8082
├─ DB: postgres://localhost:5434
└─ User: abc-services / password789

...et ainsi de suite, automatiquement !
```

## Flux de données

```
Formulaire Web
    ↓
site_commercial.py (Python/NiceGUI)
    ↓
SessionLocal (SQLAlchemy)
    ↓
Base de données (PostgreSQL)
    ↓
create_client_stack() (Python)
    ↓
Git Bash / WSL (subprocess)
    ↓
create-client-stack.sh (Bash)
    ↓
Portainer API (REST)
    ↓
Docker Engine
    ↓
Conteneurs démarrés
    ↓
Stack opérationnelle
```

## Technologies utilisées

- **Frontend** : NiceGUI (Python web framework)
- **Backend** : Python 3.12, SQLAlchemy
- **Base de données** : PostgreSQL (via Cloud SQL)
- **Orchestration** : Portainer (via API REST)
- **Conteneurisation** : Docker, Docker Compose
- **Automatisation** : Bash scripting, subprocess Python
- **Sécurité** : secrets module (génération cryptographique)
