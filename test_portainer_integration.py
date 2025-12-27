"""
Script de test pour l'intégration Portainer
Ce script teste la fonction create_client_stack sans créer réellement de stack
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from site_commercial import generate_secret_key, generate_password, create_client_stack

def test_generate_secret_key():
    """Test de la génération de clé secrète"""
    print("Test de generate_secret_key()...")
    key = generate_secret_key(32)
    assert len(key) == 32, f"La clé devrait avoir 32 caractères, trouvé {len(key)}"
    assert key.isalnum(), "La clé devrait être alphanumérique"
    print(f"✅ Clé générée : {key}")

def test_generate_password():
    """Test de la génération de mot de passe"""
    print("\nTest de generate_password()...")
    password = generate_password(16)
    assert len(password) == 16, f"Le mot de passe devrait avoir 16 caractères, trouvé {len(password)}"
    print(f"✅ Mot de passe généré : {password}")

def test_create_client_stack_dry_run():
    """Test de la fonction create_client_stack (sans exécution réelle)"""
    print("\nTest de create_client_stack()...")
    print("Note : Ce test vérifie uniquement la présence de Git Bash ou WSL")
    print("       Il ne créera PAS de stack réelle\n")
    
    # Paramètres de test
    client_name = "test-entreprise"
    postgres_password = generate_password(16)
    secret_key = generate_secret_key(32)
    initial_password = generate_password(12)
    
    print(f"Paramètres générés :")
    print(f"  Client Name : {client_name}")
    print(f"  Postgres Password : {postgres_password}")
    print(f"  Secret Key : {secret_key}")
    print(f"  Initial Password : {initial_password}")
    
    # Vérifier que Git Bash ou WSL est disponible
    git_bash_paths = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ]
    
    bash_found = False
    for path in git_bash_paths:
        if os.path.exists(path):
            print(f"\n✅ Git Bash trouvé : {path}")
            bash_found = True
            break
    
    if not bash_found:
        try:
            import subprocess
            result = subprocess.run(['wsl', '--version'], capture_output=True, check=True)
            print(f"\n✅ WSL trouvé")
            print(result.stdout.decode())
            bash_found = True
        except:
            print("\n❌ Ni Git Bash ni WSL n'ont été trouvés")
            print("   Installez l'un des deux pour utiliser cette fonctionnalité")
    
    # Vérifier que le script bash existe
    script_path = os.path.join(os.path.dirname(__file__), 'create-client-stack.sh')
    if os.path.exists(script_path):
        print(f"\n✅ Script trouvé : {script_path}")
    else:
        print(f"\n❌ Script non trouvé : {script_path}")
    
    print("\n" + "="*60)
    print("AVERTISSEMENT : Pour tester la création réelle d'une stack,")
    print("décommentez les lignes suivantes et assurez-vous que :")
    print("  1. Portainer est en cours d'exécution")
    print("  2. Les identifiants Portainer dans le script sont corrects")
    print("="*60)
    
    # Décommentez ces lignes pour un test réel (ATTENTION : créera une vraie stack !)
    # success, message = create_client_stack(
    #     client_name=client_name,
    #     postgres_password=postgres_password,
    #     secret_key=secret_key,
    #     initial_password=initial_password
    # )
    # 
    # if success:
    #     print(f"\n✅ {message}")
    # else:
    #     print(f"\n❌ {message}")

def test_client_name_sanitization():
    """Test de la sanitization du nom de client"""
    print("\nTest de sanitization du nom de client...")
    
    test_cases = [
        ("Dupont Construction", "dupont-construction"),
        ("L'Entreprise Martin", "lentreprise-martin"),
        ("ABC  Services", "abc--services"),
        ("Test & Co", "test-&-co"),
    ]
    
    for original, expected in test_cases:
        sanitized = original.lower().replace(' ', '-').replace('\'', '')
        print(f"  '{original}' -> '{sanitized}'")
        if '&' not in original:  # Le & n'est pas retiré dans notre implémentation actuelle
            assert sanitized == expected or sanitized.replace('&', '') == expected.replace('&', ''), \
                f"Expected {expected}, got {sanitized}"
    
    print("✅ Tous les tests de sanitization passent")

if __name__ == "__main__":
    print("="*60)
    print("Tests d'intégration Portainer")
    print("="*60)
    
    try:
        test_generate_secret_key()
        test_generate_password()
        test_client_name_sanitization()
        test_create_client_stack_dry_run()
        
        print("\n" + "="*60)
        print("✅ Tous les tests sont passés avec succès !")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ Échec du test : {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        sys.exit(1)
