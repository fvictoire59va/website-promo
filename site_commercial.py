from nicegui import ui, app
from database_config import SessionLocal
from models import Client, Abonnement
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import text
import subprocess
import secrets
import string
import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import json
import httpx

# Importer Stripe si disponible
try:
    import stripe
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_AVAILABLE = True
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
except:
    STRIPE_AVAILABLE = False
    STRIPE_PUBLISHABLE_KEY = ''

# Le script sera exécuté localement dans le container

# Charger le script Stripe une seule fois avec shared=True pour toutes les pages
ui.add_body_html('''
<script async src="https://js.stripe.com/v3/buy-button.js"></script>
''', shared=True)

# Stockage temporaire des identifiants de création (session)
creation_credentials = {}
payment_data = {}  # Stockage des données de paiement pour le webhook

def generate_secret_key(length=32):
    """Génère une clé secrète aléatoire de la longueur spécifiée"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_password(length=16):
    """Génère un mot de passe sécurisé sans caractères problématiques pour PostgreSQL/Docker"""
    # On évite les caractères spéciaux problématiques : $ ' " \ ` @ : / 
    # @ et : sont des séparateurs dans les URLs de connexion PostgreSQL
    # Pour éviter les problèmes d'échappement dans Docker Compose et PostgreSQL
    alphabet = string.ascii_letters + string.digits + "-_#%+=!?"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def show_stripe_form(plan: str, nom: str, prenom: str, email: str, entreprise: str, telephone: str, effectif: str, action_container):
    """Affiche le formulaire de paiement avec Stripe Checkout"""
    
    action_container.clear()
    
    with action_container:
        # Afficher un chargement
        ui.label('Redirection vers le formulaire de paiement sécurisé...').classes('text-center text-lg font-semibold mb-4')
        with ui.row().classes('w-full justify-center'):
            ui.spinner('dots', size='lg', color='indigo')
        
        # Créer la session de paiement en arrière-plan
        async def redirect_to_payment():
            try:
                # Appeler l'API pour créer une session Stripe
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        '/api/create-checkout-session',
                        json={
                            'email': email,
                            'plan': plan,
                            'nom': nom,
                            'prenom': prenom
                        }
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('url'):
                        # Rediriger vers Stripe
                        ui.navigate.to(data['url'])
                    else:
                        with action_container:
                            error_msg = data.get('error', 'Erreur inconnue')
                            ui.notify(f'Erreur: {error_msg}', type='negative')
                else:
                    with action_container:
                        ui.notify(f'Erreur serveur (code {response.status_code})', type='negative')
                    
            except Exception as e:
                print(f"❌ Erreur lors de la création de session Stripe: {e}")
                with action_container:
                    ui.notify(f'Erreur: {str(e)}', type='negative')
        
        # Lancer la redirection
        ui.timer(0.5, lambda: asyncio.create_task(redirect_to_payment()), once=True)

async def create_trial_account(plan: str, nom: str, prenom: str, email: str, entreprise: str, telephone: str):
    """Crée un compte essai gratuit"""
    # Créer une boîte de dialogue modale pour afficher la progression
    with ui.dialog() as dialog, ui.card().classes('p-8 min-w-[500px]'):
        # Zone de messages de progression
        with ui.card().classes('w-full bg-gradient-to-br from-blue-50 to-indigo-50 shadow-none border-none p-6'):
            progress_messages = ui.column().classes('w-full gap-3')
        
        # Spinner centré et élégant
        with ui.row().classes('w-full justify-center mt-6'):
            spinner = ui.spinner('dots', size='xl', color='indigo')
        
        dialog.open()
        
        # Stocker le dernier message
        recent_messages = []
        
        def add_progress_message(message):
            """Ajoute un message dans le log de progression (sans icônes)"""
            # Retirer les icônes du message
            clean_message = message
            for icon in ['🔍', '✅', '❌', '🔐', '🚀', '🎉', '⚠️', '📝', '👤', '📋', '🔄', '⏳']:
                clean_message = clean_message.replace(icon, '').strip()
            
            # Garder seulement le dernier message
            recent_messages.clear()
            recent_messages.append(clean_message)
            
            # Mettre à jour l'affichage
            progress_messages.clear()
            with progress_messages:
                for msg in recent_messages:
                    ui.label(msg).classes('text-base text-gray-700 animate-fade-in')
        
        async def run_creation():
            """Exécute la création de l'instance en arrière-plan"""
            db = None
            try:
                add_progress_message('📝 Enregistrement de vos informations...')
                db = SessionLocal()
                
                # Vérifier si le client existe déjà
                client_existant = db.query(Client).filter(Client.email == email).first()
                
                if client_existant:
                    client = client_existant
                    
                    # Vérifier s'il a déjà un abonnement actif
                    abonnement_actif = db.query(Abonnement).filter(
                        Abonnement.client_id == client.id,
                        Abonnement.statut == 'actif'
                    ).first()
                    
                    if abonnement_actif:
                        dialog.close()
                        ui.notify(f'Vous avez déjà un abonnement actif ({abonnement_actif.plan})', type='warning')
                        db.close()
                        return
                else:
                    add_progress_message('👤 Création de votre compte client...')
                    # Créer le client
                    client = Client(
                        nom=nom,
                        prenom=prenom,
                        email=email,
                        entreprise=entreprise,
                        telephone=telephone
                    )
                    db.add(client)
                    db.flush()
                    
                    if not client.id:
                        raise Exception("Impossible d'obtenir l'ID du client après création")
                
                add_progress_message('✅ Compte client créé')
                client_id = client.id
                
                # Définir le prix selon le plan
                prix_plans = {
                    'starter': Decimal('29.00'),
                    'pro': Decimal('69.00'),
                    'enterprise': Decimal('0.00'),
                    'essai': Decimal('0.00')
                }
                prix = prix_plans.get(plan, Decimal('0.00'))
                
                add_progress_message(f'📋 Création de l\'abonnement {plan.upper()}...')
                
                # Créer l'abonnement avec période d'essai de 30 jours
                abonnement = Abonnement(
                    client_id=client_id,
                    plan=plan,
                    prix_mensuel=prix,
                    date_debut=datetime.utcnow(),
                    statut='actif',
                    periode_essai=True,
                    date_fin_essai=datetime.utcnow() + timedelta(days=30)
                )
                db.add(abonnement)
                db.commit()
                add_progress_message('✅ Abonnement créé avec succès')
                
                # Générer les paramètres pour la stack
                add_progress_message('🔐 Génération des identifiants sécurisés...')
                client_name = prenom.lower().replace(' ', '-').replace('\'', '')
                postgres_password = generate_password(16)
                secret_key = generate_secret_key(32)
                initial_password = generate_password(12)
                
                add_progress_message('✅ Identifiants générés')
                
                # Exécuter le script de création de stack avec callback de progression
                result = await create_client_stack(
                    client_id=client_id,
                    client_name=client_name,
                    postgres_password=postgres_password,
                    secret_key=secret_key,
                    initial_password=initial_password,
                    progress_callback=add_progress_message
                )
                
                success = result[0]
                message = result[1] if len(result) > 1 else ''
                app_port = result[2] if len(result) > 2 else '8080'
                
                if success:
                    add_progress_message('Instance déployée avec succès !')
                    
                    # Envoyer l'email de bienvenue
                    add_progress_message('📧 Envoi de l\'email de confirmation...')
                    saas_url = f"http://176.131.66.167:{app_port}"
                    email_sent = send_welcome_email(
                        email=email,
                        client_name=client_name,
                        password=initial_password,
                        url=saas_url,
                        plan=plan
                    )
                    if email_sent:
                        add_progress_message('✅ Email de confirmation envoyé')
                    
                    await asyncio.sleep(1)
                    dialog.close()
                    
                    # Stocker les identifiants temporairement (en mémoire, sans passer par l'URL)
                    creation_key = f"{client_name}_{client_id}"
                    creation_credentials[creation_key] = {
                        'client_name': client_name,
                        'password': initial_password,
                        'plan': plan,
                        'port': app_port
                    }
                    
                    ui.navigate.to(f'/felicitations?key={creation_key}')
                else:
                    add_progress_message('Problème lors du déploiement')
                    dialog.close()
                    ui.notify(f'Abonnement créé mais erreur lors du déploiement : {message}', type='warning', timeout=8000)
                
            except Exception as e:
                add_progress_message(f'❌ Erreur : {str(e)}')
                if db:
                    db.rollback()
                dialog.close()
                ui.notify(f'Erreur lors de l\'enregistrement : {e}', type='negative')
            finally:
                if db:
                    db.close()
        
        # Lancer la création de manière asynchrone
        await run_creation()

def send_welcome_email(email, client_name, password, url, plan):
    """
    Envoie un email de bienvenue au client avec ses identifiants
    
    Args:
        email: Email du destinataire
        client_name: Nom d'utilisateur du client
        password: Mot de passe temporaire
        url: URL d'accès à l'instance
        plan: Plan d'abonnement
    """
    try:
        # Configuration SMTP - À adapter selon votre serveur SMTP
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER', 'votre-email@gmail.com')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        from_email = os.getenv('FROM_EMAIL', smtp_user)
        
        # Ne pas envoyer si les paramètres SMTP ne sont pas configurés
        if not smtp_password or smtp_password == '':
            print("SMTP non configuré - Email non envoyé")
            return False
        
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🎉 Bienvenue sur ERP BTP - Vos identifiants de connexion'
        msg['From'] = from_email
        msg['To'] = email
        
        # Contenu HTML de l'email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .credentials {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
                .credential-row {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px; }}
                .label {{ font-weight: bold; color: #667eea; }}
                .value {{ font-family: 'Courier New', monospace; color: #333; font-size: 16px; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
                .warning {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 4px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Bienvenue sur ERP BTP !</h1>
                    <p>Votre instance est prête</p>
                </div>
                <div class="content">
                    <p>Bonjour,</p>
                    <p>Félicitations ! Votre espace ERP BTP est maintenant opérationnel.</p>
                    
                    <div class="credentials">
                        <h3>Vos identifiants de connexion :</h3>
                        <div class="credential-row">
                            <span class="label">Nom d'utilisateur :</span><br>
                            <span class="value">{client_name}</span>
                        </div>
                        <div class="credential-row">
                            <span class="label">Mot de passe temporaire :</span><br>
                            <span class="value">{password}</span>
                        </div>
                        <div class="credential-row">
                            <span class="label">URL de connexion :</span><br>
                            <span class="value">{url}</span>
                        </div>
                        <div class="credential-row">
                            <span class="label">Formule :</span><br>
                            <span class="value">{plan.upper()} - 30 jours gratuits</span>
                        </div>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important :</strong><br>
                        • Veuillez patienter 1-2 minutes après réception de cet email avant de vous connecter<br>
                        • Changez votre mot de passe lors de votre première connexion<br>
                        • Conservez cet email en lieu sûr
                    </div>
                    
                    <center>
                        <a href="{url}" class="button">Accéder à mon ERP BTP</a>
                    </center>
                    
                    <p style="margin-top: 30px;">Si vous avez des questions, notre équipe support est disponible 24/7 pour vous accompagner.</p>
                    
                    <div class="footer">
                        <p>ERP BTP - Solution de Gestion pour le BTP</p>
                        <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Créer les versions texte et HTML
        text_content = f"""
Bienvenue sur ERP BTP !

Votre instance est maintenant opérationnelle.

Vos identifiants de connexion :
- Nom d'utilisateur : {client_name}
- Mot de passe temporaire : {password}
- URL de connexion : {url}
- Formule : {plan.upper()} - 30 jours gratuits

Important :
- Veuillez patienter 1-2 minutes avant de vous connecter
- Changez votre mot de passe lors de votre première connexion
- Conservez cet email en lieu sûr

Accédez à votre ERP : {url}

Notre équipe support est disponible 24/7 pour vous accompagner.

ERP BTP - Solution de Gestion pour le BTP
        """
        
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Envoyer l'email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"Email de bienvenue envoyé à {email}")
        return True
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
        return False


async def create_client_stack(client_id, client_name, postgres_password, secret_key, initial_password, progress_callback=None):
    """
    Exécute le script create-client-stack.sh localement dans le container
    
    Args:
        client_id: ID du client dans la base de données
        client_name: Nom du client (pour le nom de la stack)
        postgres_password: Mot de passe PostgreSQL
        secret_key: Clé secrète de 32 caractères
        initial_password: Mot de passe initial temporaire
        progress_callback: Fonction de callback pour les mises à jour de progression
    
    Returns:
        tuple: (success: bool, message: str)
    """
    def update_progress(message):
        """Met à jour le message de progression si un callback est fourni"""
        if progress_callback:
            progress_callback(message)
    
    try:
        update_progress("🔍 Préparation de l'environnement...")
        await asyncio.sleep(0.1)
        
        # Exécution locale dans le container Linux
        update_progress("✅ Exécution dans le container")
        await asyncio.sleep(0.1)
        
        script_path = os.path.join(os.path.dirname(__file__), 'create-client-stack.sh')
        bash_exe = '/bin/bash' if os.path.exists('/bin/bash') else '/usr/bin/bash'
        
        # Récupérer les paramètres de connexion externe à la base d'abonnements
        # Les containers ERP clients doivent se connecter via l'IP publique/externe
        sub_host = os.getenv('EXTERNAL_DB_HOST', '192.168.1.14')
        sub_port = os.getenv('EXTERNAL_DB_PORT', '5433')
        sub_db = os.getenv('DB_NAME', 'erpbtp_clients')
        sub_user = os.getenv('DB_USER', 'fred')
        sub_password = os.getenv('DB_PASSWORD', 'Jbvf2023@')
        
        cmd = [
            bash_exe,
            script_path,
            '-c', client_name,
            '-d', str(client_id),
            '-p', postgres_password,
            '-s', secret_key,
            '-i', initial_password,
            '--sub-host', sub_host,
            '--sub-port', sub_port,
            '--sub-db', sub_db,
            '--sub-user', sub_user,
            '--sub-pass', sub_password
        ]
        
        update_progress(f"⏳ Création de votre compte dans quelques secondes...")
        await asyncio.sleep(0.1)
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Attendre la fin du processus
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        
        # Décoder les sorties
        stdout_text = stdout.decode() if stdout else ""
        stderr_text = stderr.decode() if stderr else ""
        
        if process.returncode == 0:
            update_progress(f"✅ Stack créée avec succès")
            
            # Extraire le port depuis la sortie
            port = '8080'  # Valeur par défaut
            
            for line in stdout_text.split('\n'):
                # Chercher spécifiquement la ligne avec le port attribué
                if 'Port application attribue' in line:
                    # Extraire le nombre après le dernier ':'
                    parts = line.split(':')
                    if len(parts) > 0:
                        try:
                            # Le port est le dernier élément, on enlève les espaces
                            port_str = parts[-1].strip()
                            # Vérifier que c'est bien un nombre
                            if port_str.isdigit():
                                port = port_str
                        except Exception as e:
                            pass
                    break
            
            return True, f"Stack créée avec succès pour {client_name}\n\n{stdout_text}", port
        else:
            error_msg = stderr_text if stderr_text else stdout_text if stdout_text else "Erreur inconnue"
            update_progress(f"❌ Erreur lors de la création")
            return False, f"Erreur lors de la création de la stack : {error_msg}", None
    
    except asyncio.TimeoutError:
        update_progress("❌ Timeout dépassé")
        return False, "Timeout : La création de la stack a pris trop de temps (>5 minutes)"
    except FileNotFoundError as e:
        update_progress(f"❌ Script bash non trouvé")
        return False, f"Erreur : Le script bash n'a pas été trouvé : {str(e)}"
    except Exception as e:
        update_progress(f"❌ Erreur système")
        return False, f"Erreur lors de l'exécution du script : {str(e)}"

def create_header():
    """Crée l'en-tête du site"""
    with ui.header().classes('bg-gradient-to-r from-blue-700 to-blue-900 text-white shadow-lg'):
        with ui.row().classes('w-full max-w-7xl mx-auto px-4 py-4 items-center'):
            with ui.link(target='/').classes('no-underline'):
                ui.label('🏗️ ERP BTP').classes('text-2xl font-bold text-white')
            ui.space()
            with ui.row().classes('gap-6'):
                ui.link('Accueil', '/').classes('text-white hover:text-blue-200 no-underline')
                ui.link('Fonctionnalités', '/fonctionnalites').classes('text-white hover:text-blue-200 no-underline')
                ui.link('Tarifs', '/tarifs').classes('text-white hover:text-blue-200 no-underline')
                ui.link('Contact', '/contact').classes('text-white hover:text-blue-200 no-underline')
                ui.button('Essai Gratuit', on_click=lambda: ui.navigate.to('/demo')).classes('bg-green-500 hover:bg-green-600')

def create_footer():
    """Crée le pied de page"""
    with ui.element('div').classes('bg-gray-800 text-white w-full'):
        with ui.column().classes('w-full max-w-7xl mx-auto px-4 py-8'):
            with ui.row().classes('w-full justify-between'):
                with ui.column():
                    ui.label('ERP BTP').classes('text-xl font-bold mb-2')
                    ui.label('Solution de gestion complète pour le BTP').classes('text-gray-400')
                
                with ui.column():
                    ui.label('Liens rapides').classes('font-bold mb-2')
                    ui.link('Fonctionnalités', '/fonctionnalites').classes('text-gray-400 hover:text-white')
                    ui.link('Tarifs', '/tarifs').classes('text-gray-400 hover:text-white')
                    ui.link('Contact', '/contact').classes('text-gray-400 hover:text-white')
                
                with ui.column():
                    ui.label('Contact').classes('font-bold mb-2')
                    ui.label('📧 frederic.victoire@gmail.com').classes('text-gray-400')
                    ui.label('📞 0689962910').classes('text-gray-400')
            
            ui.separator().classes('my-4 bg-gray-700')
            ui.label('© 2025 ERP BTP - Tous droits réservés').classes('text-center text-gray-500')

# ============================================================================
# ENDPOINT API POUR TRAITER LES PAIEMENTS STRIPE
# ============================================================================

@app.post('/api/payment/process-subscription')
async def process_payment(request):
    """
    Endpoint pour traiter le paiement Stripe
    
    Reçoit:
    - Infos client (nom, prenom, email, entreprise, téléphone)
    - Plan (starter, pro, enterprise)
    - PaymentMethod ID de Stripe
    
    Crée:
    - Client Stripe
    - Subscription avec 30j essai
    - Client en BD
    - Abonnement en BD
    - Stack ERP
    """
    try:
        data = await request.json()
        
        # Récupérer les données
        nom = data.get('nom', '')
        prenom = data.get('prenom', '')
        email = data.get('email', '')
        entreprise = data.get('entreprise', '')
        telephone = data.get('telephone', '')
        plan = data.get('plan', 'starter')
        payment_method_id = data.get('payment_method_id', '')
        
        if not all([nom, prenom, email, entreprise, plan]):
            return {'success': False, 'message': 'Champs obligatoires manquants'}, 400
        
        if not STRIPE_AVAILABLE:
            return {'success': False, 'message': 'Stripe non configuré'}, 500
        
        # Prix des plans en centimes
        prices = {
            'starter': 2900,      # 29€
            'pro': 6900,          # 69€
            'enterprise': 14900   # 149€
        }
        
        price = prices.get(plan, 2900)
        
        db = SessionLocal()
        
        try:
            # ===== ÉTAPE 1: Vérifier/Créer le client Stripe =====
            
            # Chercher un client Stripe existant
            customers = stripe.Customer.list(email=email, limit=1)
            
            if customers.data:
                customer_id = customers.data[0].id
            else:
                # Créer un nouveau client Stripe
                customer = stripe.Customer.create(
                    email=email,
                    name=f"{prenom} {nom}",
                    metadata={
                        'entreprise': entreprise,
                        'telephone': telephone
                    }
                )
                customer_id = customer.id
            
            # ===== ÉTAPE 2: Créer/Confirmer le PaymentIntent =====
            
            intent = stripe.PaymentIntent.create(
                amount=price,
                currency='eur',
                customer=customer_id,
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={'enabled': True},
                description=f"Abonnement {plan.upper()} - {entreprise}"
            )
            
            # Vérifier le statut du paiement
            if intent.status not in ['succeeded', 'processing']:
                return {
                    'success': False,
                    'message': f'Paiement non réussi: {intent.status}'
                }, 400
            
            # ===== ÉTAPE 3: Créer/Mettre à jour le client en BD =====
            
            client_existant = db.query(Client).filter(Client.email == email).first()
            
            if client_existant:
                client = client_existant
            else:
                client = Client(
                    nom=nom,
                    prenom=prenom,
                    email=email,
                    entreprise=entreprise,
                    telephone=telephone
                )
                db.add(client)
                db.flush()
            
            client_id = client.id
            
            # ===== ÉTAPE 4: Créer l'abonnement en BD =====
            
            # Vérifier s'il existe déjà un abonnement actif
            abonnement_actif = db.query(Abonnement).filter(
                Abonnement.client_id == client_id,
                Abonnement.statut == 'actif'
            ).first()
            
            if abonnement_actif:
                # Mettre à jour l'abonnement existant
                abonnement_actif.plan = plan
                abonnement_actif.prix_mensuel = Decimal(str(price / 100))
                abonnement_actif.date_debut = datetime.utcnow()
                abonnement_actif.periode_essai = True
                abonnement_actif.date_fin_essai = datetime.utcnow() + timedelta(days=30)
            else:
                # Créer un nouvel abonnement
                abonnement = Abonnement(
                    client_id=client_id,
                    plan=plan,
                    prix_mensuel=Decimal(str(price / 100)),
                    date_debut=datetime.utcnow(),
                    statut='actif',
                    periode_essai=True,
                    date_fin_essai=datetime.utcnow() + timedelta(days=30)
                )
                db.add(abonnement)
            
            db.commit()
            
            # ===== ÉTAPE 5: Déployer la stack ERP =====
            
            # Générer les identifiants
            client_name = prenom.lower().replace(' ', '-').replace('\'', '')
            postgres_password = generate_password(16)
            secret_key = generate_secret_key(32)
            initial_password = generate_password(12)
            
            # Note: create_client_stack est asynchrone et nécessite await
            # Pour cette API, on le lancera en arrière-plan
            # mais on retournera une réponse immédiate
            
            # Stocker les info pour la page de félicitations
            creation_key = f"{client_name}_{client_id}"
            creation_credentials[creation_key] = {
                'client_name': client_name,
                'password': initial_password,
                'plan': plan,
                'port': '8080'  # Port par défaut, sera mis à jour après
            }
            
            # ===== ÉTAPE 6: Envoyer email de confirmation =====
            
            saas_url = f"http://176.131.66.167:8080"  # À adapter selon config
            try:
                send_welcome_email(
                    email=email,
                    client_name=client_name,
                    password=initial_password,
                    url=saas_url,
                    plan=plan
                )
            except Exception as e:
                print(f"Erreur lors de l'envoi d'email: {e}")
            
            return {
                'success': True,
                'message': 'Compte créé avec succès!',
                'client_id': client_id,
                'creation_key': creation_key,
                'payment_intent_id': intent.id
            }, 200
            
        except stripe.error.CardError as e:
            db.rollback()
            return {
                'success': False,
                'message': f'Erreur de carte: {e.user_message}'
            }, 400
        except stripe.error.RateLimitError:
            db.rollback()
            return {
                'success': False,
                'message': 'Trop de requêtes. Veuillez réessayer.'
            }, 429
        except stripe.error.InvalidRequestError as e:
            db.rollback()
            return {
                'success': False,
                'message': f'Erreur Stripe: {str(e)}'
            }, 400
        except stripe.error.AuthenticationError:
            db.rollback()
            return {
                'success': False,
                'message': 'Erreur d\'authentification Stripe'
            }, 500
        except stripe.error.StripeError as e:
            db.rollback()
            return {
                'success': False,
                'message': f'Erreur Stripe: {str(e)}'
            }, 500
        except Exception as e:
            db.rollback()
            print(f"Erreur serveur: {str(e)}")
            return {
                'success': False,
                'message': f'Erreur serveur: {str(e)}'
            }, 500
        finally:
            db.close()
            
    except Exception as e:
        print(f"Erreur lors du traitement du paiement: {str(e)}")
        return {
            'success': False,
            'message': 'Erreur serveur'
        }, 500

@ui.page('/')
def home_page():
    """Page d'accueil"""
    create_header()
    
    # Hero Section
    with ui.column().classes('w-full bg-gradient-to-br from-blue-50 to-blue-100 py-20'):
        with ui.column().classes('max-w-7xl mx-auto px-4 text-center'):
            ui.label('La Solution de Gestion Complète').classes('text-5xl font-bold text-gray-800 mb-4')
            ui.label('pour les Entreprises du BTP').classes('text-5xl font-bold text-blue-700 mb-6')
            ui.label('Gérez vos devis, factures, chantiers et clients en toute simplicité').classes('text-xl text-gray-600 mb-8')
            
            with ui.row().classes('gap-4 justify-center'):
                ui.button('Démarrer l\'essai gratuit', on_click=lambda: ui.navigate.to('/demo?plan=essai')).classes('bg-green-500 hover:bg-green-600 text-white px-8 py-4 text-lg')
    
    # Fonctionnalités principales
    with ui.column().classes('w-full py-16'):
        with ui.column().classes('max-w-7xl mx-auto px-4'):
            ui.label('Pourquoi choisir ERP BTP ?').classes('text-4xl font-bold text-center text-gray-800 mb-12')
            
            with ui.row().classes('w-full gap-8 flex-wrap justify-center'):
                # Card 1
                with ui.card().classes('flex-1 min-w-[300px] max-w-[350px] p-6'):
                    ui.icon('description', size='3em').classes('text-blue-600 mb-4')
                    ui.label('Devis Professionnels').classes('text-2xl font-bold mb-2')
                    ui.label('Créez des devis personnalisés en quelques clics. Templates professionnels inclus.').classes('text-gray-600')
                
                # Card 2
                with ui.card().classes('flex-1 min-w-[300px] max-w-[350px] p-6'):
                    ui.icon('receipt', size='3em').classes('text-green-600 mb-4')
                    ui.label('Facturation Simplifiée').classes('text-2xl font-bold mb-2')
                    ui.label('Générez et envoyez vos factures automatiquement. Suivez les paiements en temps réel.').classes('text-gray-600')
                
                # Card 3
                with ui.card().classes('flex-1 min-w-[300px] max-w-[350px] p-6'):
                    ui.icon('construction', size='3em').classes('text-orange-600 mb-4')
                    ui.label('Gestion de Chantiers').classes('text-2xl font-bold mb-2')
                    ui.label('Suivez tous vos chantiers, plannings et budgets depuis une seule interface.').classes('text-gray-600')
    
    # CTA Final
    with ui.column().classes('w-full py-16 bg-gray-50'):
        with ui.column().classes('max-w-7xl mx-auto px-4 text-center'):
            ui.label('Prêt à transformer votre gestion ?').classes('text-4xl font-bold text-gray-800 mb-6')
            ui.label('Essayez ERP BTP gratuitement pendant 30 jours').classes('text-xl text-gray-600 mb-8')
            ui.button('Commencer maintenant', on_click=lambda: ui.navigate.to('/demo')).classes('bg-green-500 hover:bg-green-600 text-white px-12 py-4 text-lg')
    
    create_footer()

@ui.page('/fonctionnalites')
def features_page():
    """Page des fonctionnalités"""
    create_header()
    
    with ui.column().classes('w-full py-16'):
        with ui.column().classes('max-w-7xl mx-auto px-4'):
            ui.label('Fonctionnalités Complètes').classes('text-4xl font-bold text-center text-gray-800 mb-4')
            ui.label('Tout ce dont vous avez besoin pour gérer votre entreprise BTP').classes('text-xl text-center text-gray-600 mb-12')
            
            # Grille de fonctionnalités
            with ui.row().classes('w-full gap-6 flex-wrap'):
                features = [
                    {'icon': 'people', 'title': 'Gestion Clients', 'desc': 'Base de données clients complète avec historique et documents'},
                    {'icon': 'construction', 'title': 'Projets & Chantiers', 'desc': 'Suivi détaillé de tous vos projets et chantiers'},
                    {'icon': 'description', 'title': 'Devis Personnalisés', 'desc': 'Modèles professionnels et calculs automatiques'},
                    {'icon': 'receipt', 'title': 'Facturation', 'desc': 'Création et envoi automatique de factures'},
                    {'icon': 'local_shipping', 'title': 'Fournisseurs', 'desc': 'Gestion de vos fournisseurs et sous-traitants'},
                    {'icon': 'dashboard', 'title': 'Tableau de Bord', 'desc': 'Vue d\'ensemble en temps réel de votre activité'},
                    {'icon': 'schedule', 'title': 'Planning', 'desc': 'Planification et suivi des interventions'},
                    {'icon': 'euro', 'title': 'Comptabilité', 'desc': 'Suivi financier et rapports comptables'},
                    {'icon': 'cloud', 'title': 'Cloud Sécurisé', 'desc': 'Accès partout, données sauvegardées et sécurisées'},
                    {'icon': 'phone_iphone', 'title': 'Mobile', 'desc': 'Accessible depuis tous vos appareils'},
                    {'icon': 'security', 'title': 'Sécurité', 'desc': 'Données cryptées et conformes RGPD'},
                    {'icon': 'support', 'title': 'Support', 'desc': 'Équipe support disponible et réactive'},
                ]
                
                for feature in features:
                    with ui.card().classes('flex-1 min-w-[280px] max-w-[350px] p-6'):
                        ui.icon(feature['icon'], size='2.5em').classes('text-blue-600 mb-3')
                        ui.label(feature['title']).classes('text-xl font-bold mb-2')
                        ui.label(feature['desc']).classes('text-gray-600')
    
    create_footer()

@ui.page('/tarifs')
def pricing_page():
    """Page des tarifs"""
    create_header()
    
    with ui.column().classes('w-full py-16'):
        with ui.column().classes('max-w-7xl mx-auto px-4'):
            ui.label('Tarifs Transparents').classes('text-4xl font-bold text-center text-gray-800 mb-4')
            ui.label('Choisissez le plan adapté à votre entreprise').classes('text-xl text-center text-gray-600 mb-12')
            
            with ui.row().classes('w-full gap-8 justify-center flex-wrap'):
                # Plan Starter
                with ui.card().classes('flex-1 min-w-[300px] max-w-[350px] p-8 border-2 border-gray-200'):
                    ui.label('Starter').classes('text-2xl font-bold mb-4 text-center')
                    ui.label('29€').classes('text-5xl font-bold text-center text-blue-600 mb-2')
                    ui.label('par mois').classes('text-center text-gray-600 mb-6')
                    
                    with ui.column().classes('gap-3 mb-6'):
                        ui.label('✓ Jusqu\'à 50 devis/mois').classes('text-gray-700')
                        ui.label('✓ 5 utilisateurs').classes('text-gray-700')
                        ui.label('✓ Gestion clients').classes('text-gray-700')
                        ui.label('✓ Devis & Factures').classes('text-gray-700')
                        ui.label('✓ Support email').classes('text-gray-700')
                    
                    ui.button('Commencer', on_click=lambda: ui.navigate.to('/demo?plan=starter')).classes('w-full bg-blue-600 hover:bg-blue-700')
                
                # Plan Pro (Populaire)
                with ui.card().classes('flex-1 min-w-[300px] max-w-[350px] p-8 border-4 border-blue-600 relative'):
                    ui.badge('Populaire', color='bg-blue-600').classes('absolute -top-3 left-1/2 -translate-x-1/2')
                    ui.label('Pro').classes('text-2xl font-bold mb-4 text-center')
                    ui.label('69€').classes('text-5xl font-bold text-center text-blue-600 mb-2')
                    ui.label('par mois').classes('text-center text-gray-600 mb-6')
                    
                    with ui.column().classes('gap-3 mb-6'):
                        ui.label('✓ Devis illimités').classes('text-gray-700')
                        ui.label('✓ 15 utilisateurs').classes('text-gray-700')
                        ui.label('✓ Toutes les fonctionnalités Starter').classes('text-gray-700')
                        ui.label('✓ Gestion de chantiers').classes('text-gray-700')
                        ui.label('✓ Planning & Interventions').classes('text-gray-700')
                        ui.label('✓ Rapports avancés').classes('text-gray-700')
                        ui.label('✓ Support prioritaire').classes('text-gray-700')
                    
                    ui.button('Commencer', on_click=lambda: ui.navigate.to('/demo?plan=pro')).classes('w-full bg-green-500 hover:bg-green-600')
                
                # Plan Enterprise
                with ui.card().classes('flex-1 min-w-[300px] max-w-[350px] p-8 border-2 border-gray-200'):
                    ui.label('Enterprise').classes('text-2xl font-bold mb-4 text-center')
                    ui.label('Sur mesure').classes('text-3xl font-bold text-center text-blue-600 mb-2')
                    ui.label('contactez-nous').classes('text-center text-gray-600 mb-6')
                    
                    with ui.column().classes('gap-3 mb-6'):
                        ui.label('✓ Tout illimité').classes('text-gray-700')
                        ui.label('✓ Utilisateurs illimités').classes('text-gray-700')
                        ui.label('✓ Toutes les fonctionnalités Pro').classes('text-gray-700')
                        ui.label('✓ API & Intégrations').classes('text-gray-700')
                        ui.label('✓ Formation personnalisée').classes('text-gray-700')
                        ui.label('✓ Support dédié 24/7').classes('text-gray-700')
                        ui.label('✓ SLA garanti').classes('text-gray-700')
                    
                    ui.button('Nous contacter', on_click=lambda: ui.navigate.to('/contact')).classes('w-full bg-blue-600 hover:bg-blue-700')
            
            # Note
            with ui.column().classes('w-full text-center mt-12'):
                ui.label('🎉 30 jours d\'essai gratuit - Sans engagement - Sans carte bancaire').classes('text-lg font-bold text-green-600')
    
    create_footer()

@ui.page('/contact')
def contact_page():
    """Page de contact"""
    create_header()
    
    with ui.column().classes('w-full py-16'):
        with ui.column().classes('max-w-4xl mx-auto px-4'):
            ui.label('Contactez-nous').classes('text-4xl font-bold text-center text-gray-800 mb-4')
            ui.label('Notre équipe est là pour répondre à vos questions').classes('text-xl text-center text-gray-600 mb-12')
            
            with ui.row().classes('w-full gap-12 flex-wrap'):
                # Formulaire
                with ui.card().classes('flex-1 min-w-[400px] p-8'):
                    ui.label('Envoyez-nous un message').classes('text-2xl font-bold mb-6')
                    
                    nom = ui.input('Nom complet *').classes('w-full')
                    email = ui.input('Email *').classes('w-full')
                    entreprise = ui.input('Entreprise').classes('w-full')
                    telephone = ui.input('Téléphone').classes('w-full')
                    message = ui.textarea('Message *').classes('w-full')
                    
                    def send_message():
                        if not nom.value or not email.value or not message.value:
                            ui.notify('Veuillez remplir tous les champs obligatoires', type='negative')
                            return
                        ui.notify('Message envoyé ! Nous vous répondrons sous 24h', type='positive')
                        nom.value = ''
                        email.value = ''
                        entreprise.value = ''
                        telephone.value = ''
                        message.value = ''
                    
                    ui.button('Envoyer', on_click=send_message).classes('w-full bg-blue-600 hover:bg-blue-700 mt-4')
                
                # Coordonnées
                with ui.column().classes('flex-1 min-w-[300px] gap-6'):
                    with ui.card().classes('p-6'):
                        ui.icon('email', size='2em').classes('text-blue-600 mb-2')
                        ui.label('Email').classes('font-bold mb-1')
                        ui.label('frederic.victoire@gmail.com').classes('text-gray-600')
                    
                    with ui.card().classes('p-6'):
                        ui.icon('phone', size='2em').classes('text-blue-600 mb-2')
                        ui.label('Téléphone').classes('font-bold mb-1')
                        ui.label('0689962910').classes('text-gray-600')
                    
                    with ui.card().classes('p-6'):
                        ui.icon('schedule', size='2em').classes('text-blue-600 mb-2')
                        ui.label('Horaires').classes('font-bold mb-1')
                        ui.label('Lun-Ven : 9h-18h').classes('text-gray-600')
                    
                    with ui.card().classes('p-6'):
                        ui.icon('location_on', size='2em').classes('text-blue-600 mb-2')
                        ui.label('Adresse').classes('font-bold mb-1')
                        ui.label('Paris, France').classes('text-gray-600')
    
    create_footer()

@ui.page('/demo')
def demo_page(plan: str = ''):
    """Page de demande de démo"""
    create_header()
    
    # Définir le titre selon le plan
    plan_labels = {
        'starter': ('Plan Starter', '29€/mois'),
        'pro': ('Plan Pro', '69€/mois'),
        'enterprise': ('Plan Enterprise', 'Sur mesure'),
        'essai': ('Essai Gratuit', '0€ - 30 jours')
    }
    plan_info = plan_labels.get(plan, ('', ''))
    
    with ui.column().classes('w-full py-16 bg-gradient-to-br from-blue-50 to-blue-100'):
        with ui.column().classes('max-w-2xl mx-auto px-4'):
            with ui.card().classes('w-full p-8'):
                # Titre selon le plan
                if plan == 'essai' or plan == '':
                    ui.label('Démarrez votre essai gratuit').classes('text-3xl font-bold text-center mb-2')
                else:
                    ui.label('Commencez votre abonnement').classes('text-3xl font-bold text-center mb-2')
                
                if plan_info[0]:
                    with ui.row().classes('w-full justify-center items-center gap-2 mb-2'):
                        ui.label(plan_info[0]).classes('text-xl font-bold text-blue-600')
                        ui.label('-').classes('text-gray-400')
                        ui.label(plan_info[1]).classes('text-lg text-gray-600')
                
                # Message selon le plan
                if plan == 'essai' or plan == '':
                    ui.label('30 jours gratuits - Sans carte bancaire').classes('text-center text-gray-600 mb-8')
                else:
                    ui.label('Votre instance sera créée instantanément').classes('text-center text-gray-600 mb-8')
                
                nom = ui.input('Nom *').classes('w-full')
                prenom = ui.input('Prénom *').classes('w-full')
                email = ui.input('Email professionnel *').classes('w-full')
                entreprise = ui.input('Nom de l\'entreprise *').classes('w-full')
                telephone = ui.input('Téléphone *').classes('w-full')
                effectif = ui.select(['1-5', '6-10', '11-50', '50+'], label='Nombre d\'employés').classes('w-full')
                
                with ui.row().classes('w-full items-center gap-2'):
                    cgv = ui.checkbox('J\'accepte les conditions générales')
                
                # Conteneur pour les boutons/formulaire
                action_container = ui.column().classes('w-full')
                
                async def start_trial():
                    if not all([nom.value, prenom.value, email.value, entreprise.value, telephone.value]):
                        ui.notify('Veuillez remplir tous les champs obligatoires', type='negative')
                        return
                    if not cgv.value:
                        ui.notify('Veuillez accepter les conditions générales', type='negative')
                        return
                    
                    # Si c'est un plan payant ET Stripe est disponible, afficher le formulaire de paiement
                    if plan in ['starter', 'pro', 'enterprise'] and STRIPE_AVAILABLE:
                        await show_stripe_form(
                            plan=plan,
                            nom=nom.value,
                            prenom=prenom.value,
                            email=email.value,
                            entreprise=entreprise.value,
                            telephone=telephone.value,
                            effectif=effectif.value,
                            action_container=action_container
                        )
                    else:
                        # Créer l'essai gratuit comme avant
                        await create_trial_account(
                            plan=plan if plan else 'essai',
                            nom=nom.value,
                            prenom=prenom.value,
                            email=email.value,
                            entreprise=entreprise.value,
                            telephone=telephone.value
                        )

                
                ui.button('Démarrer mon essai gratuit', on_click=start_trial).classes('w-full bg-green-500 hover:bg-green-600 text-lg py-4 mt-4')
                
                ui.label('✓ Pas de carte bancaire requise').classes('text-center text-gray-600 text-sm mt-4')
                ui.label('✓ Annulation à tout moment').classes('text-center text-gray-600 text-sm')
    
    create_footer()

@ui.page('/felicitations')
def felicitations_page(key: str = ''):
    """Page de félicitation après création de la stack"""
    
    # Récupérer les identifiants stockés
    credentials = creation_credentials.get(key, {})
    client_name = credentials.get('client_name', 'client')
    pwd = credentials.get('password', '')
    plan = credentials.get('plan', 'essai')
    port = credentials.get('port', '8080')
    
    # Nettoyer après récupération
    if key in creation_credentials:
        del creation_credentials[key]
    
    # Debug: afficher les valeurs récupérées
    print(f"DEBUG Félicitation - client_name: {client_name}")
    print(f"DEBUG Félicitation - password: {pwd}")
    print(f"DEBUG Félicitation - plan: {plan}")
    print(f"DEBUG Félicitation - port: {port}")
    
    # URL du SaaS (à adapter selon votre configuration)
    saas_url = f"http://176.131.66.167:{port}"
    print(f"DEBUG Félicitation - saas_url: {saas_url}")
    
    # Fonction JavaScript pour copier avec notification
    ui.add_head_html('''
    <script>
    async function copyToClipboard(text, label) {
        try {
            await navigator.clipboard.writeText(text);
            // Notification de succès
            const notif = document.createElement('div');
            notif.textContent = label + ' copié !';
            notif.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 16px 24px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 9999; font-weight: 600;';
            document.body.appendChild(notif);
            setTimeout(() => notif.remove(), 2000);
        } catch (err) {
            // Fallback pour les navigateurs sans support clipboard API
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            
            const notif = document.createElement('div');
            notif.textContent = label + ' copié !';
            notif.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 16px 24px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 9999; font-weight: 600;';
            document.body.appendChild(notif);
            setTimeout(() => notif.remove(), 2000);
        }
    }
    </script>
    ''')
    
    create_header()
    
    with ui.column().classes('w-full max-w-4xl mx-auto px-4 py-16'):
        # Animation de succès
        with ui.card().classes('w-full p-12 text-center bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 shadow-2xl'):
            # Grande icône de succès
            ui.label('🎉').classes('text-8xl mb-6')
            
            ui.label('Félicitations !').classes('text-5xl font-bold text-green-600 mb-4')
            ui.label('Votre espace ERP BTP est prêt').classes('text-2xl text-gray-700 mb-8')
            
            # Informations de connexion
            with ui.card().classes('w-full bg-white p-6 shadow-md mb-6'):
                ui.label('Vos identifiants de connexion').classes('text-xl font-semibold text-gray-800 mb-4')
                
                # Avertissement important
                with ui.card().classes('w-full bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4'):
                    ui.label('⚠️ Important').classes('font-bold text-yellow-800 mb-2')
                    ui.label('Veuillez patienter 1-2 minutes après création de la stack avant de vous connecter.').classes('text-yellow-700 text-sm')
                    ui.label('Le temps que les conteneurs démarrent complètement.').classes('text-yellow-700 text-sm')
                
                with ui.row().classes('w-full justify-between items-center mb-3 pb-3 border-b'):
                    ui.label('Nom d\'utilisateur :').classes('text-gray-600 font-semibold')
                    with ui.row().classes('items-center gap-2'):
                        ui.label(client_name).classes('font-mono text-lg font-bold text-indigo-600')
                        ui.button(icon='content_copy', on_click=lambda cn=client_name: ui.run_javascript(f"copyToClipboard('{cn}', 'Nom d\\'utilisateur')")).props('flat dense').classes('text-gray-500').tooltip('Copier')
                
                with ui.row().classes('w-full justify-between items-center mb-3 pb-3 border-b'):
                    ui.label('Mot de passe temporaire :').classes('text-gray-600 font-semibold')
                    with ui.row().classes('items-center gap-2'):
                        ui.label(pwd).classes('font-mono text-lg font-bold text-indigo-600')
                        ui.button(icon='content_copy', on_click=lambda p=pwd: ui.run_javascript(f"copyToClipboard('{p}', 'Mot de passe')")).props('flat dense').classes('text-gray-500').tooltip('Copier')
                
                with ui.row().classes('w-full justify-between items-center mb-3 pb-3 border-b'):
                    ui.label('URL de connexion :').classes('text-gray-600 font-semibold')
                    with ui.row().classes('items-center gap-2'):
                        ui.label(saas_url).classes('font-mono text-sm text-indigo-600')
                        ui.button(icon='content_copy', on_click=lambda url=saas_url: ui.run_javascript(f"copyToClipboard('{url}', 'URL')")).props('flat dense').classes('text-gray-500').tooltip('Copier')
                
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('Formule :').classes('text-gray-600')
                    ui.label(f'{plan.upper()} - 30 jours gratuits').classes('font-semibold text-green-600')
            
            # Bouton principal d'accès
            ui.link('Accéder à mon ERP BTP', saas_url, new_tab=True).classes(
                'inline-block bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-12 py-5 text-xl font-bold rounded-xl shadow-lg transform hover:scale-105 transition-all mb-6 no-underline'
            )
            
            # Informations supplémentaires
            with ui.column().classes('w-full gap-2 text-gray-600 text-sm mt-8'):
                ui.label('✓ Changez votre mot de passe lors de votre première connexion')
                ui.label('✓ Un email de confirmation vous a été envoyé')
                ui.label('✓ Support disponible 24/7 pour vous accompagner')
        
        # Bouton retour
        with ui.row().classes('w-full justify-center mt-8'):
            ui.button('Retour à l\'accueil', on_click=lambda: ui.navigate.to('/')).classes(
                'bg-gray-500 hover:bg-gray-600 text-white px-8 py-3'
            )
    
    create_footer()

# ============================================================================
# WEBHOOK STRIPE - Gestion des paiements
# ============================================================================

async def handle_payment_success(email: str, plan: str, stripe_session_id: str):
    """Traite un paiement réussi et crée/met à jour le compte"""
    db = None
    try:
        db = SessionLocal()
        
        # Vérifier si le client existe
        client_existant = db.query(Client).filter(Client.email == email).first()
        
        if client_existant:
            # RÉACTIVATION - Client existe, mettre à jour l'abonnement
            client = client_existant
            
            # Marquer les anciens abonnements comme annulés
            anciens_abo = db.query(Abonnement).filter(
                Abonnement.client_id == client.id
            ).all()
            for abo in anciens_abo:
                if abo.statut != 'actif':
                    abo.statut = 'remplace'
            
            # Créer un nouvel abonnement
            prix_plans = {
                'starter': Decimal('29.00'),
                'pro': Decimal('69.00'),
                'enterprise': Decimal('0.00')
            }
            prix = prix_plans.get(plan, Decimal('0.00'))
            
            nouvel_abo = Abonnement(
                client_id=client.id,
                plan=plan,
                prix_mensuel=prix,
                date_debut=datetime.utcnow(),
                statut='actif',
                periode_essai=True,
                date_fin_essai=datetime.utcnow() + timedelta(days=30)
            )
            db.add(nouvel_abo)
            db.commit()
            
            payment_data[stripe_session_id] = {
                'type': 'reactivation',
                'client_id': client.id,
                'client_name': client.prenom.lower().replace(' ', '-').replace('\'', ''),
                'email': email,
                'plan': plan
            }
            print(f"✅ Réactivation client {email} - Plan {plan}")
            
        else:
            # NOUVEAU CLIENT - Marquer pour création
            payment_data[stripe_session_id] = {
                'type': 'new_customer',
                'email': email,
                'plan': plan,
                'pending': True
            }
            print(f"✅ Nouveau client enregistré {email} - Plan {plan}")
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement du paiement: {e}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

@app.post('/api/create-checkout-session')
async def create_checkout_session(request):
    """Crée une session de paiement Stripe avec métadonnées"""
    try:
        # Vérifier que Stripe est configuré
        if not STRIPE_AVAILABLE:
            print("❌ Stripe non disponible")
            return {'success': False, 'error': 'Stripe non configuré'}, 400
        
        data = await request.json()
        email = data.get('email', '')
        plan = data.get('plan', 'starter')
        nom = data.get('nom', '')
        prenom = data.get('prenom', '')
        
        print(f"📝 Création session Stripe: email={email}, plan={plan}")
        
        # Configuration des plans
        price_ids = {
            'starter': os.getenv('STRIPE_PRICE_ID_STARTER', 'price_1Ss6CTB0rlCfGOCzJ3j9Jq7w'),
            'pro': os.getenv('STRIPE_PRICE_ID_PRO', 'price_1Ss7tXB0rlCfGOCz1ZL4yJhk'),
            'enterprise': os.getenv('STRIPE_PRICE_ID_ENTERPRISE', 'price_1Ss8w5B0rlCfGOCz0Ye5Ujmn')
        }
        
        price_id = price_ids.get(plan, price_ids['starter'])
        print(f"💰 Price ID: {price_id}")
        
        # Récupérer le domaine/hostname depuis la requête ou l'environnement
        hostname = os.getenv('APP_HOSTNAME', 'localhost:8000')
        base_url = f"https://{hostname}" if not hostname.startswith('http') else hostname
        print(f"🌐 Base URL: {base_url}")
        
        # Créer la session Stripe Checkout
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                }
            ],
            success_url=f'{base_url}/felicitations-paiement',
            cancel_url=f'{base_url}/tarifs',
            customer_email=email,
            metadata={
                'plan': plan,
                'nom': nom,
                'prenom': prenom,
                'email': email
            },
            trial_settings={
                'end_behavior': {
                    'missing_payment_method': 'cancel'
                }
            } if plan != 'enterprise' else {}
        )
        
        print(f"✅ Session Stripe créée: {session.id}")
        return {
            'success': True,
            'session_id': session.id,
            'url': session.url
        }
        
    except Exception as e:
        import traceback
        print(f"❌ Erreur création session Stripe: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return {'success': False, 'error': str(e)}, 400

@app.post('/stripe-webhook')
async def stripe_webhook(request):
    """
    Endpoint pour traiter les webhooks Stripe
    Événement attendu: checkout.session.completed
    """
    try:
        body = await request.body()
        signature = request.headers.get('stripe-signature', '')
        
        # Valider la signature du webhook
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        if not webhook_secret:
            print("⚠️ STRIPE_WEBHOOK_SECRET non configuré")
            return {'status': 'ok'}
        
        try:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        except stripe.error.SignatureVerificationError:
            print("❌ Signature webhook invalide")
            return {'status': 'invalid_signature'}, 403
        
        event_type = event['type']
        event_data = event['data']['object']
        
        print(f"[Webhook] Événement reçu: {event_type}")
        
        if event_type == 'checkout.session.completed':
            # Récupérer les informations du client depuis la session Stripe
            customer_email = event_data.get('customer_email')
            metadata = event_data.get('metadata', {})
            plan = metadata.get('plan', 'starter')
            session_id = event_data.get('id')
            
            print(f"✅ Paiement complété pour {customer_email} - Plan: {plan}")
            
            # Traiter le paiement
            await handle_payment_success(customer_email, plan, session_id)
        
        return {'status': 'success', 'event_id': event.get('id')}
        
    except Exception as e:
        print(f"❌ Erreur webhook: {e}")
        return {'status': 'error'}, 500

# ============================================================================
# PAGES DE FÉLICITATIONS
# ============================================================================

@ui.page('/felicitations-paiement')
async def page_felicitations_paiement():
    """Page de félicitations après paiement - Nouveau client"""
    with ui.column().classes('w-full h-screen bg-gradient-to-br from-green-50 to-emerald-50'):
        # Espacer du top
        ui.column().classes('h-20')
        
        with ui.column().classes('w-full max-w-2xl mx-auto px-4'):
            # Titre avec icône
            with ui.row().classes('w-full justify-center gap-4 mb-8'):
                ui.icon('celebration', size='64px').classes('text-green-600')
                ui.label('Félicitations!').classes('text-5xl font-bold text-green-700')
            
            # Message principal
            with ui.card().classes('w-full p-8 bg-white shadow-lg'):
                ui.label('Votre paiement a été validé avec succès! 🎉').classes('text-2xl font-bold text-center text-green-700 mb-4')
                
                ui.label('Votre compte est en cours de création...').classes('text-lg text-gray-700 text-center mb-6')
                
                with ui.row().classes('w-full justify-center gap-4'):
                    ui.spinner('dots', size='xl', color='green')
                    ui.label('Création de votre instance').classes('text-lg font-semibold text-gray-700')
                
                ui.label('Cela peut prendre quelques minutes. Vous recevrez un email avec vos identifiants de connexion.').classes('text-sm text-gray-600 text-center mt-8')
            
            # Informations utiles
            with ui.card().classes('w-full p-6 bg-blue-50 border border-blue-200 mt-6'):
                ui.label('ℹ️ À faire:').classes('text-lg font-bold text-blue-700 mb-4')
                with ui.column().classes('gap-3'):
                    ui.label('✅ Vérifiez votre email').classes('text-base text-gray-700')
                    ui.label('✅ Attendez la confirmation de création (5-10 minutes)').classes('text-base text-gray-700')
                    ui.label('✅ Cliquez sur le lien d\'activation').classes('text-base text-gray-700')
                    ui.label('✅ Commencez à utiliser votre ERP BTP').classes('text-base text-gray-700')
            
            # Bouton retour
            ui.button('Retour à l\'accueil').on_click(lambda: ui.navigate.to('/')).classes('w-full mt-8 bg-green-600 hover:bg-green-700 text-white font-bold py-3')

@ui.page('/felicitations-reactivation')
async def page_felicitations_reactivation():
    """Page de félicitations après réactivation"""
    with ui.column().classes('w-full h-screen bg-gradient-to-br from-blue-50 to-cyan-50'):
        # Espacer du top
        ui.column().classes('h-20')
        
        with ui.column().classes('w-full max-w-2xl mx-auto px-4'):
            # Titre avec icône
            with ui.row().classes('w-full justify-center gap-4 mb-8'):
                ui.icon('verified', size='64px').classes('text-blue-600')
                ui.label('Bienvenue!').classes('text-5xl font-bold text-blue-700')
            
            # Message principal
            with ui.card().classes('w-full p-8 bg-white shadow-lg'):
                ui.label('Votre compte a été réactivé avec succès! ✨').classes('text-2xl font-bold text-center text-blue-700 mb-4')
                
                ui.label('Votre abonnement est actif et vous avez 30 jours d\'essai gratuit.').classes('text-lg text-gray-700 text-center mb-6')
                
                with ui.row().classes('w-full justify-center gap-4'):
                    ui.label('👉 Cliquez ci-dessous pour accéder à votre application').classes('text-lg font-semibold text-gray-700')
            
            # Informations d'accès
            with ui.card().classes('w-full p-6 bg-green-50 border border-green-200 mt-6'):
                ui.label('🚀 Accès rapide:').classes('text-lg font-bold text-green-700 mb-4')
                with ui.column().classes('gap-3'):
                    ui.label('Votre instance est prête à l\'emploi').classes('text-base text-gray-700')
                    ui.label('Connectez-vous avec vos identifiants habituels').classes('text-base text-gray-700')
                    ui.label('Tous vos données sont preservées').classes('text-base text-gray-700')
            
            # Boutons d'action
            with ui.row().classes('w-full gap-4 mt-8'):
                ui.button('Accéder à mon application').on_click(lambda: ui.navigate.to('/')).classes('flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-3')
                ui.button('Retour à l\'accueil').on_click(lambda: ui.navigate.to('/')).classes('flex-1 bg-gray-400 hover:bg-gray-500 text-white font-bold py-3')

def fix_db_sequences():
    """Corrige les séquences PostgreSQL si nécessaire"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        
        tables = ['clients', 'abonnements', 'connexions']
        
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
            except Exception:
                db.rollback()
        
        db.close()
    except Exception:
        pass  # Ignorer les erreurs silencieusement

def main():
    """Lance le site commercial"""
    # Configurer le répertoire des fichiers statiques
    static_dir = Path(__file__).parent / 'static'
    if static_dir.exists():
        app.add_static_files('/static', str(static_dir))
    
    # Initialiser les tables de la base de données si elles n'existent pas
    try:
        from database_config import Base, engine
        print("🔧 Vérification/création des tables de la base de données...")
        Base.metadata.create_all(engine)
        print("✅ Base de données prête")
        
        # Corriger les séquences PostgreSQL
        print("🔧 Vérification des séquences...")
        fix_db_sequences()
        print("✅ Séquences vérifiées")
    except Exception as e:
        print(f"⚠️ Avertissement : Impossible d'initialiser la base de données : {e}")
        print("   L'application continuera mais les fonctionnalités nécessitant la BD seront indisponibles")
    
    ui.run(
        host='0.0.0.0',
        port=8000,
        title='ERP BTP - Solution de Gestion pour le BTP',
        favicon='static/favicon_io/favicon.ico',
        dark=False
    )

if __name__ in {"__main__", "__mp_main__"}:
    main()
