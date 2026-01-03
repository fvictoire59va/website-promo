#!/usr/bin/env python3
"""
Script de test pour vérifier l'envoi d'emails via Gmail
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_smtp_connection():
    """Teste la connexion et l'envoi d'un email"""
    
    # Récupérer les paramètres SMTP
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    from_email = os.getenv('FROM_EMAIL', smtp_user)
    
    print("="*60)
    print("🔧 TEST DE CONFIGURATION SMTP")
    print("="*60)
    print(f"Serveur SMTP : {smtp_server}")
    print(f"Port         : {smtp_port}")
    print(f"Utilisateur  : {smtp_user}")
    print(f"Expéditeur   : {from_email}")
    print(f"Mot de passe : {'*' * len(smtp_password) if smtp_password else '[NON CONFIGURÉ]'}")
    print("="*60)
    print()
    
    # Vérifier que les paramètres sont configurés
    if not smtp_password or smtp_password == 'votre-mot-de-passe-application-16-caracteres':
        print("❌ ERREUR : Le mot de passe SMTP n'est pas configuré dans le fichier .env")
        print("\nVeuillez configurer les variables SMTP dans le fichier .env :")
        print("  SMTP_USER=votre-email@gmail.com")
        print("  SMTP_PASSWORD=votre-mot-de-passe-application")
        return False
    
    if not smtp_user or smtp_user == 'votre-email@gmail.com':
        print("❌ ERREUR : L'utilisateur SMTP n'est pas configuré dans le fichier .env")
        return False
    
    # Demander l'email de test
    print("📧 Envoi d'un email de test...")
    test_email = input(f"Entrez l'adresse email de destination (défaut: {smtp_user}) : ").strip()
    if not test_email:
        test_email = smtp_user
    
    print(f"\n🚀 Tentative d'envoi vers : {test_email}")
    print("-" * 60)
    
    try:
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🧪 Test - Configuration SMTP ERP BTP'
        msg['From'] = from_email
        msg['To'] = test_email
        
        # Contenu texte
        text_content = """
Test de configuration SMTP - ERP BTP

Si vous recevez cet email, la configuration SMTP est correcte !

✅ Serveur SMTP : Fonctionnel
✅ Authentification : Réussie
✅ Envoi d'email : Opérationnel

Vous pouvez maintenant utiliser le système d'envoi d'emails pour les nouveaux clients.

---
Ceci est un email de test automatique.
        """
        
        # Contenu HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                .success { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 4px; }
                .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 Test SMTP</h1>
                    <p>Configuration ERP BTP</p>
                </div>
                <div class="content">
                    <p>Si vous recevez cet email, <strong>la configuration SMTP est correcte !</strong></p>
                    
                    <div class="success">
                        <strong>✅ Tests réussis :</strong><br>
                        • Connexion au serveur SMTP<br>
                        • Authentification<br>
                        • Envoi d'email
                    </div>
                    
                    <p>Vous pouvez maintenant utiliser le système d'envoi d'emails pour les nouveaux clients.</p>
                    
                    <div class="footer">
                        <p>ERP BTP - Email de test automatique</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Connexion et envoi
        print("1️⃣  Connexion au serveur SMTP...", end=" ")
        server = smtplib.SMTP(smtp_server, smtp_port)
        print("✅")
        
        print("2️⃣  Activation de TLS...", end=" ")
        server.starttls()
        print("✅")
        
        print("3️⃣  Authentification...", end=" ")
        server.login(smtp_user, smtp_password)
        print("✅")
        
        print("4️⃣  Envoi de l'email...", end=" ")
        server.send_message(msg)
        print("✅")
        
        print("5️⃣  Fermeture de la connexion...", end=" ")
        server.quit()
        print("✅")
        
        print("-" * 60)
        print()
        print("="*60)
        print("✅ SUCCÈS ! Email de test envoyé avec succès")
        print("="*60)
        print()
        print(f"📬 Vérifiez la boîte de réception de : {test_email}")
        print("   (N'oubliez pas de vérifier le dossier spam)")
        print()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("❌")
        print()
        print("="*60)
        print("❌ ERREUR D'AUTHENTIFICATION")
        print("="*60)
        print(f"Détails : {e}")
        print()
        print("Causes possibles :")
        print("  • Vous utilisez votre mot de passe Gmail normal")
        print("    → Utilisez un mot de passe d'application (16 caractères)")
        print("  • La validation en deux étapes n'est pas activée")
        print("  • Le mot de passe d'application est incorrect")
        print()
        print("Solution :")
        print("  1. Activez la validation en deux étapes sur votre compte Google")
        print("  2. Générez un mot de passe d'application")
        print("  3. Mettez à jour SMTP_PASSWORD dans le fichier .env")
        print()
        return False
        
    except smtplib.SMTPException as e:
        print("❌")
        print()
        print("="*60)
        print("❌ ERREUR SMTP")
        print("="*60)
        print(f"Détails : {e}")
        print()
        return False
        
    except Exception as e:
        print("❌")
        print()
        print("="*60)
        print("❌ ERREUR INATTENDUE")
        print("="*60)
        print(f"Détails : {e}")
        print()
        print("Vérifiez :")
        print("  • La connexion Internet")
        print("  • Les paramètres du pare-feu")
        print("  • Que le port 587 n'est pas bloqué")
        print()
        return False

if __name__ == "__main__":
    try:
        success = test_smtp_connection()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        exit(1)
