import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuration de la base de données PostgreSQL
DB_USER = os.getenv('DB_USER', 'fred')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Jbvf2023@')
DB_NAME = os.getenv('DB_NAME', 'erpbtp_clients')
DB_HOST = os.getenv('DB_HOST', '192.168.1.14')
DB_PORT = os.getenv('DB_PORT', '5433')

# Encoder le mot de passe pour l'URL (le @ doit devenir %40)
encoded_password = quote_plus(DB_PASSWORD)

# Connexion PostgreSQL - Utilise psycopg (v3)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
