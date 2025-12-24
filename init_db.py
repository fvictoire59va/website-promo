"""
Script d'initialisation de la base de données
Créé automatiquement les tables nécessaires
"""
from cloudsql_config import Base, engine
from models import Client, Abonnement, DemoRequest

if __name__ == "__main__":
    print("🔧 Création des tables dans la base de données...")
    try:
        Base.metadata.create_all(engine)
        print("✅ Tables créées avec succès!")
        print("\nTables créées:")
        print("  - clients")
        print("  - abonnements")
        print("  - demo_requests")
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        exit(1)
