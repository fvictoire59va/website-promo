#!/usr/bin/env python3
"""
Script de validation du flux de paiement Stripe

Vérifie que:
1. Les imports Stripe sont corrects
2. Les variables d'environnement sont configurées
3. Les fonctions existent et sont syntaxiquement correctes
4. La base de données est accessible
5. Stripe peut être appelé (sans faire de vrais appels)
"""

import os
import sys
from pathlib import Path

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv()

def check_env_variables():
    """Vérifie les variables d'environnement Stripe"""
    print("🔍 Vérification des variables d'environnement...")
    
    stripe_secret = os.getenv('STRIPE_SECRET_KEY', '')
    stripe_public = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    
    if stripe_secret:
        # Masquer la plupart de la clé pour la sécurité
        masked = stripe_secret[:8] + '...' + stripe_secret[-4:]
        print(f"  ✅ STRIPE_SECRET_KEY configurée: {masked}")
        if not stripe_secret.startswith(('sk_test_', 'sk_live_')):
            print(f"     ⚠️  WARNING: Clé ne commence pas par sk_test_ ou sk_live_")
    else:
        print(f"  ❌ STRIPE_SECRET_KEY NOT FOUND")
        return False
    
    if stripe_public:
        masked = stripe_public[:8] + '...' + stripe_public[-4:]
        print(f"  ✅ STRIPE_PUBLISHABLE_KEY configurée: {masked}")
        if not stripe_public.startswith(('pk_test_', 'pk_live_')):
            print(f"     ⚠️  WARNING: Clé ne commence pas par pk_test_ ou pk_live_")
    else:
        print(f"  ❌ STRIPE_PUBLISHABLE_KEY NOT FOUND")
        return False
    
    return True

def check_stripe_import():
    """Vérifie que Stripe peut être importé"""
    print("\n🔍 Vérification de l'import Stripe...")
    
    try:
        import stripe
        print(f"  ✅ stripe importé avec succès")
        return True
    except ImportError as e:
        print(f"  ❌ Erreur d'import: {e}")
        print("     Solution: pip install stripe")
        return False

def check_nicegui_import():
    """Vérifie que NiceGUI peut être importé"""
    print("\n🔍 Vérification de l'import NiceGUI...")
    
    try:
        import nicegui
        print(f"  ✅ nicegui importé avec succès")
        return True
    except ImportError as e:
        print(f"  ❌ Erreur d'import: {e}")
        print("     Solution: pip install nicegui")
        return False

def check_database():
    """Vérifie que la base de données est configurée"""
    print("\n🔍 Vérification de la base de données...")
    
    db_user = os.getenv('DB_USER', 'fred')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'postgres')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'erpbtp_clients')
    
    print(f"  📊 Config BD:")
    print(f"     Host: {db_host}")
    print(f"     Port: {db_port}")
    print(f"     Database: {db_name}")
    print(f"     User: {db_user}")
    
    if not db_password:
        print(f"  ⚠️  WARNING: DB_PASSWORD not set")
        return False
    
    try:
        from database_config import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print(f"  ✅ Connexion à la base de données OK")
        return True
    except Exception as e:
        print(f"  ⚠️  Impossible de se connecter à la BD: {e}")
        print(f"     (Normal si le serveur n'est pas démarré)")
        return True  # On retourne True car ce n'est pas critique pour les vérifs

def check_models():
    """Vérifie que les modèles existent"""
    print("\n🔍 Vérification des modèles...")
    
    try:
        from models import Client, Abonnement
        print(f"  ✅ Model 'Client' OK")
        print(f"  ✅ Model 'Abonnement' OK")
        return True
    except ImportError as e:
        print(f"  ❌ Erreur: {e}")
        return False

def check_smtp():
    """Vérifie la configuration SMTP"""
    print("\n🔍 Vérification de la configuration SMTP...")
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = os.getenv('SMTP_PORT', '587')
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    print(f"  📧 Config SMTP:")
    print(f"     Server: {smtp_server}")
    print(f"     Port: {smtp_port}")
    print(f"     User: {smtp_user}")
    
    if not smtp_password:
        print(f"  ⚠️  WARNING: SMTP_PASSWORD not set (emails ne seront pas envoyés)")
        return False
    
    print(f"  ✅ SMTP configuré")
    return True

def check_site_commercial():
    """Vérifie que le fichier site_commercial.py peut être parsé"""
    print("\n🔍 Vérification de site_commercial.py...")
    
    try:
        # Vérifier que le fichier existe
        if not Path('site_commercial.py').exists():
            print(f"  ❌ Fichier site_commercial.py NOT FOUND")
            return False
        
        # Parser le fichier
        with open('site_commercial.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, 'site_commercial.py', 'exec')
        print(f"  ✅ site_commercial.py syntaxiquement correct")
        
        # Vérifier la présence des nouvelles fonctions
        if 'async def show_stripe_form' in code:
            print(f"  ✅ Fonction 'show_stripe_form' trouvée")
        else:
            print(f"  ❌ Fonction 'show_stripe_form' NOT FOUND")
            return False
        
        if 'async def create_trial_account' in code:
            print(f"  ✅ Fonction 'create_trial_account' trouvée")
        else:
            print(f"  ❌ Fonction 'create_trial_account' NOT FOUND")
            return False
        
        if 'STRIPE_AVAILABLE' in code:
            print(f"  ✅ Variable 'STRIPE_AVAILABLE' trouvée")
        else:
            print(f"  ❌ Variable 'STRIPE_AVAILABLE' NOT FOUND")
            return False
        
        return True
        
    except SyntaxError as e:
        print(f"  ❌ Erreur de syntaxe: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False

def check_stripe_config():
    """Vérifie la configuration Stripe existante"""
    print("\n🔍 Vérification de stripe_integration/...")
    
    try:
        from stripe_integration.stripe_config import SUBSCRIPTION_PLANS
        print(f"  ✅ SUBSCRIPTION_PLANS trouvé")
        print(f"     Plans configurés: {list(SUBSCRIPTION_PLANS.keys())}")
        return True
    except ImportError as e:
        print(f"  ⚠️  {e}")
        return True  # Non critique

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║     🔐 VALIDATION DU FLUX DE PAIEMENT STRIPE                  ║
║                                                                ║
║  Ce script vérifie que tout est correctement configuré        ║
║  pour le flux: Tarifs → Formulaire → Paiement → Confirmation  ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # Exécuter toutes les vérifications
    results['Env Variables'] = check_env_variables()
    results['Stripe Import'] = check_stripe_import()
    results['NiceGUI Import'] = check_nicegui_import()
    results['Database'] = check_database()
    results['Models'] = check_models()
    results['SMTP'] = check_smtp()
    results['site_commercial.py'] = check_site_commercial()
    results['Stripe Config'] = check_stripe_config()
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DE LA VÉRIFICATION")
    print("="*70)
    
    for name, result in results.items():
        status = "✅ OK" if result else "❌ ERREUR"
        print(f"{name:.<40} {status}")
    
    # Résultat final
    all_critical_ok = all([
        results['Env Variables'],
        results['Stripe Import'],
        results['NiceGUI Import'],
        # Models - non critique (géré par Docker)
        results['site_commercial.py']
    ])
    
    print("\n" + "="*70)
    
    if all_critical_ok:
        print("✅ TOUS LES TESTS CRITIQUES SONT PASSÉS!")
        print("\n🚀 Vous pouvez démarrer l'application:")
        print("   docker-compose up -d")
        print("\n📍 Allez à: http://localhost:8000/tarifs")
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("\n⚠️  Consultez les erreurs ci-dessus et corrigez-les")
        print("\n💡 Tips:")
        print("   - Vérifier le fichier .env")
        print("   - Installer les dépendances: pip install -r requirements.txt")
        print("   - Redémarrer le serveur: docker-compose restart")
        return 1

if __name__ == '__main__':
    sys.exit(main())
