#!/usr/bin/env python3
"""
Script pour corriger les séquences PostgreSQL des tables
Résout le problème de clé primaire en double après restauration de données
"""

from database_config import SessionLocal
from sqlalchemy import text

def fix_sequences():
    """Réinitialise les séquences PostgreSQL pour qu'elles correspondent aux données existantes"""
    db = SessionLocal()
    
    try:
        print("🔧 Correction des séquences PostgreSQL...")
        
        # Liste des tables à corriger
        tables = ['clients', 'abonnements', 'demo_requests']
        
        for table in tables:
            try:
                # Obtenir le maximum ID actuel
                result = db.execute(text(f"SELECT MAX(id) FROM {table}"))
                max_id = result.scalar()
                
                if max_id is not None:
                    # Réinitialiser la séquence à max_id + 1
                    sequence_name = f"{table}_id_seq"
                    new_value = max_id + 1
                    
                    db.execute(text(f"SELECT setval('{sequence_name}', {new_value}, false)"))
                    db.commit()
                    
                    print(f"✅ Table '{table}': séquence réinitialisée à {new_value}")
                else:
                    print(f"ℹ️  Table '{table}': vide, pas de correction nécessaire")
                    
            except Exception as e:
                print(f"⚠️  Erreur sur la table '{table}': {e}")
                db.rollback()
        
        print("\n✅ Correction des séquences terminée!")
        print("Vous pouvez maintenant créer de nouveaux abonnements sans erreur.")
        
    except Exception as e:
        print(f"❌ Erreur globale : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_sequences()
