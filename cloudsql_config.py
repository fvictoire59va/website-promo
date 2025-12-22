import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# À personnaliser avec vos informations Cloud SQL
CLOUDSQL_USER = os.getenv('CLOUDSQL_USER', 'fred')
CLOUDSQL_PASSWORD = os.getenv('CLOUDSQL_PASSWORD', 'Jbvf2023@')
CLOUDSQL_DB = os.getenv('CLOUDSQL_DB', 'erpbtp_clients')  # Nom de la base, pas l'identifiant d'instance
CLOUDSQL_HOST = os.getenv('CLOUDSQL_HOST', '127.0.0.1')  # Via Cloud SQL Auth Proxy (utiliser IP au lieu de localhost)
CLOUDSQL_PORT = os.getenv('CLOUDSQL_PORT', '5432')

# Encoder le mot de passe pour l'URL (le @ doit devenir %40)
encoded_password = quote_plus(CLOUDSQL_PASSWORD)

# Connexion via Cloud SQL Auth Proxy - Utilise psycopg (v3)
DATABASE_URL = f"postgresql+psycopg://{CLOUDSQL_USER}:{encoded_password}@{CLOUDSQL_HOST}:{CLOUDSQL_PORT}/{CLOUDSQL_DB}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
