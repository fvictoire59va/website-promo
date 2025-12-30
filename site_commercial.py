from nicegui import ui
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

# Configuration du serveur distant (à modifier selon votre configuration)
REMOTE_SERVER = os.environ.get('REMOTE_SERVER', 'votre-serveur-ubuntu')
REMOTE_USER = os.environ.get('REMOTE_USER', 'ubuntu')
REMOTE_SCRIPT_PATH = os.environ.get('REMOTE_SCRIPT_PATH', '/home/ubuntu/create-client-stack.sh')
SSH_KEY_PATH = os.environ.get('SSH_KEY_PATH', '')  # Optionnel, pour authentification par clé

def generate_secret_key(length=32):
    """Génère une clé secrète aléatoire de la longueur spécifiée"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_password(length=16):
    """Génère un mot de passe sécurisé"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def create_client_stack(client_name, postgres_password, secret_key, initial_password, progress_callback=None):
    """
    Exécute le script create-client-stack.sh sur un serveur Ubuntu distant via SSH
    
    Args:
        client_name: Nom du client
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
        update_progress("🔍 Vérification de l'environnement d'exécution...")
        await asyncio.sleep(0.1)
        
        # Échapper les caractères spéciaux pour le shell
        def escape_shell_arg(arg):
            """Échappe les caractères spéciaux pour éviter les injections shell"""
            return arg.replace("'", "'\\''")
        
        # Déterminer si on exécute localement (Linux/Container) ou à distance (Windows vers Ubuntu)
        import sys
        is_windows = os.name == 'nt' or sys.platform == 'win32'
        is_local_linux = os.path.exists('/bin/bash') or os.path.exists('/usr/bin/bash')
        
        if is_local_linux and not is_windows:
            # Exécution locale sur Linux/Container
            update_progress("✅ Environnement Linux détecté - exécution locale")
            await asyncio.sleep(0.1)
            
            script_path = os.path.join(os.path.dirname(__file__), 'create-client-stack.sh')
            bash_exe = '/bin/bash' if os.path.exists('/bin/bash') else '/usr/bin/bash'
            
            cmd = [
                bash_exe,
                script_path,
                '-c', client_name,
                '-p', postgres_password,
                '-s', secret_key,
                '-i', initial_password
            ]
            
            update_progress(f"🚀 Création de la stack '{client_name}' sur Portainer...")
            await asyncio.sleep(0.1)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
        else:
            # Exécution à distance via SSH (Windows vers serveur Ubuntu)
            update_progress("✅ Environnement Windows - connexion au serveur Ubuntu distant...")
            await asyncio.sleep(0.1)
            
            # Vérifier que les variables d'environnement sont configurées
            if REMOTE_SERVER == 'votre-serveur-ubuntu':
                return False, ("Configuration SSH manquante. Veuillez définir les variables d'environnement:\n"
                             "- REMOTE_SERVER (adresse du serveur)\n"
                             "- REMOTE_USER (utilisateur SSH)\n"
                             "- REMOTE_SCRIPT_PATH (chemin du script sur le serveur)\n"
                             "- SSH_KEY_PATH (optionnel, chemin vers la clé SSH)")
            
            update_progress(f"📡 Connexion à {REMOTE_USER}@{REMOTE_SERVER}...")
            await asyncio.sleep(0.1)
            
            # Construire la commande SSH
            escaped_client = escape_shell_arg(client_name)
            escaped_postgres = escape_shell_arg(postgres_password)
            escaped_secret = escape_shell_arg(secret_key)
            escaped_initial = escape_shell_arg(initial_password)
            
            remote_cmd = (
                f"{REMOTE_SCRIPT_PATH} "
                f"-c '{escaped_client}' "
                f"-p '{escaped_postgres}' "
                f"-s '{escaped_secret}' "
                f"-i '{escaped_initial}'"
            )
            
            # Construire la commande SSH complète
            ssh_cmd = ['ssh']
            
            # Ajouter les options SSH
            ssh_cmd.extend([
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'ConnectTimeout=10'
            ])
            
            # Ajouter la clé SSH si configurée
            if SSH_KEY_PATH and os.path.exists(SSH_KEY_PATH):
                ssh_cmd.extend(['-i', SSH_KEY_PATH])
                update_progress(f"🔑 Utilisation de la clé SSH: {SSH_KEY_PATH}")
                await asyncio.sleep(0.1)
            
            # Ajouter l'utilisateur@serveur et la commande
            ssh_cmd.append(f"{REMOTE_USER}@{REMOTE_SERVER}")
            ssh_cmd.append(remote_cmd)
            
            update_progress(f"🚀 Création de la stack '{client_name}' sur le serveur distant...")
            update_progress("⏳ Cette opération peut prendre quelques minutes...")
            await asyncio.sleep(0.1)
            
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        
        # Attendre la fin du processus
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        
        if process.returncode == 0:
            output = stdout.decode() if stdout else ""
            update_progress(f"✅ Stack créée avec succès pour {client_name}")
            return True, f"Stack créée avec succès pour {client_name}\n\n{output}"
        else:
            error_msg = stderr.decode() if stderr else stdout.decode() if stdout else "Erreur inconnue"
            update_progress(f"❌ Erreur lors de la création : {error_msg}")
            return False, f"Erreur lors de la création de la stack : {error_msg}"
    
    except asyncio.TimeoutError:
        update_progress("❌ Timeout dépassé")
        return False, "Timeout : La création de la stack a pris trop de temps (>5 minutes)"
    except FileNotFoundError as e:
        update_progress(f"❌ Commande SSH non trouvée")
        return False, f"Erreur : SSH n'est pas installé ou n'est pas dans le PATH. Installez OpenSSH : {str(e)}"
    except Exception as e:
        update_progress(f"❌ Erreur : {str(e)}")
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
                    ui.label('📧 contact@erpbtp.fr').classes('text-gray-400')
                    ui.label('📞 01 23 45 67 89').classes('text-gray-400')
            
            ui.separator().classes('my-4 bg-gray-700')
            ui.label('© 2025 ERP BTP - Tous droits réservés').classes('text-center text-gray-500')

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
    
    # Statistiques
    with ui.column().classes('w-full bg-blue-700 text-white py-16'):
        with ui.column().classes('max-w-7xl mx-auto px-4'):
            with ui.row().classes('w-full justify-around flex-wrap gap-8'):
                with ui.column().classes('text-center'):
                    ui.label('500+').classes('text-5xl font-bold mb-2')
                    ui.label('Entreprises clientes').classes('text-xl')
                
                with ui.column().classes('text-center'):
                    ui.label('10 000+').classes('text-5xl font-bold mb-2')
                    ui.label('Devis créés par mois').classes('text-xl')
                
                with ui.column().classes('text-center'):
                    ui.label('99.9%').classes('text-5xl font-bold mb-2')
                    ui.label('Disponibilité').classes('text-xl')
                
                with ui.column().classes('text-center'):
                    ui.label('4.9/5').classes('text-5xl font-bold mb-2')
                    ui.label('Satisfaction client').classes('text-xl')
    
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
                        ui.label('contact@erpbtp.fr').classes('text-gray-600')
                    
                    with ui.card().classes('p-6'):
                        ui.icon('phone', size='2em').classes('text-blue-600 mb-2')
                        ui.label('Téléphone').classes('font-bold mb-1')
                        ui.label('01 23 45 67 89').classes('text-gray-600')
                    
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
                ui.label('Démarrez votre essai gratuit').classes('text-3xl font-bold text-center mb-2')
                if plan_info[0]:
                    with ui.row().classes('w-full justify-center items-center gap-2 mb-2'):
                        ui.label(plan_info[0]).classes('text-xl font-bold text-blue-600')
                        ui.label('-').classes('text-gray-400')
                        ui.label(plan_info[1]).classes('text-lg text-gray-600')
                ui.label('30 jours gratuits - Sans carte bancaire').classes('text-center text-gray-600 mb-8')
                
                nom = ui.input('Nom *').classes('w-full')
                prenom = ui.input('Prénom *').classes('w-full')
                email = ui.input('Email professionnel *').classes('w-full')
                entreprise = ui.input('Nom de l\'entreprise *').classes('w-full')
                telephone = ui.input('Téléphone *').classes('w-full')
                effectif = ui.select(['1-5', '6-10', '11-50', '50+'], label='Nombre d\'employés').classes('w-full')
                
                with ui.row().classes('w-full items-center gap-2'):
                    cgv = ui.checkbox('J\'accepte les conditions générales')
                    ui.label('J\'accepte les conditions générales').classes('text-sm')
                
                async def start_trial():
                    if not all([nom.value, prenom.value, email.value, entreprise.value, telephone.value]):
                        ui.notify('Veuillez remplir tous les champs obligatoires', type='negative')
                        return
                    if not cgv.value:
                        ui.notify('Veuillez accepter les conditions générales', type='negative')
                        return
                    
                    # Créer une boîte de dialogue modale pour afficher la progression
                    with ui.dialog() as dialog, ui.card().classes('p-8 min-w-[500px]'):
                        ui.label('🚀 Création de votre instance ERP BTP').classes('text-2xl font-bold mb-4 text-center')
                        
                        # Zone de messages de progression
                        progress_label = ui.label('Initialisation...').classes('text-lg mb-4')
                        progress_log = ui.column().classes('w-full h-48 overflow-y-auto bg-gray-100 p-4 rounded mb-4')
                        
                        # Barre de progression
                        spinner = ui.spinner('dots', size='lg', color='blue')
                        
                        dialog.open()
                        
                        def add_progress_message(message):
                            """Ajoute un message dans le log de progression"""
                            with progress_log:
                                ui.label(message).classes('text-sm text-gray-700 mb-1')
                            progress_label.set_text(message)
                        
                        async def run_creation():
                            """Exécute la création de l'instance en arrière-plan"""
                            try:
                                add_progress_message('📝 Enregistrement de vos informations...')
                                db = SessionLocal()
                                
                                # Déterminer le plan à enregistrer
                                plan_enregistre = plan if plan else 'essai'
                                
                                # Vérifier si le client existe déjà
                                client_existant = db.query(Client).filter(Client.email == email.value).first()
                                
                                if client_existant:
                                    client = client_existant
                                    
                                    # Vérifier s'il a déjà un abonnement actif
                                    abonnement_actif = db.query(Abonnement).filter(
                                        Abonnement.client_id == client.id,
                                        Abonnement.statut == 'actif'
                                    ).first()
                                    
                                    # Si c'est une demande d'essai et qu'il a déjà un abonnement actif
                                    if abonnement_actif and plan_enregistre == 'essai':
                                        dialog.close()
                                        ui.notify(f'Vous avez déjà un abonnement actif ({abonnement_actif.plan})', type='warning')
                                        db.close()
                                        return
                                    
                                    # Si c'est une formule payante (starter, pro, enterprise) et qu'il a un abonnement
                                    if abonnement_actif and plan_enregistre != 'essai':
                                        add_progress_message('🔄 Mise à jour de votre abonnement...')
                                        # Mettre à jour l'abonnement existant
                                        prix_plans = {
                                            'starter': Decimal('29.00'),
                                            'pro': Decimal('69.00'),
                                            'enterprise': Decimal('0.00')
                                        }
                                        abonnement_actif.plan = plan_enregistre
                                        abonnement_actif.prix_mensuel = prix_plans.get(plan_enregistre, Decimal('29.00'))
                                        abonnement_actif.date_debut = datetime.utcnow()
                                        abonnement_actif.periode_essai = True
                                        abonnement_actif.date_fin_essai = datetime.utcnow() + timedelta(days=30)
                                        
                                        db.commit()
                                        dialog.close()
                                        ui.notify(f'✅ Abonnement mis à jour vers {plan_enregistre.upper()} - 30 jours d\'essai', type='positive')
                                        db.close()
                                        return
                                else:
                                    add_progress_message('👤 Création de votre compte client...')
                                    # Créer le client
                                    client = Client(
                                        nom=nom.value,
                                        prenom=prenom.value,
                                        email=email.value,
                                        entreprise=entreprise.value,
                                        telephone=telephone.value
                                    )
                                    db.add(client)
                                    db.flush()  # Pour obtenir l'ID du client
                                
                                add_progress_message('✅ Compte client créé')
                                
                                # Définir le prix selon le plan
                                prix_plans = {
                                    'starter': Decimal('29.00'),
                                    'pro': Decimal('69.00'),
                                    'enterprise': Decimal('0.00'),  # Sur mesure
                                    'essai': Decimal('0.00')  # Essai gratuit
                                }
                                prix = prix_plans.get(plan_enregistre, Decimal('0.00'))
                                
                                add_progress_message(f'📋 Création de l\'abonnement {plan_enregistre.upper()}...')
                                
                                # Créer l'abonnement avec période d'essai de 30 jours
                                abonnement = Abonnement(
                                    client_id=client.id,
                                    plan=plan_enregistre,
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
                                client_name = entreprise.value.lower().replace(' ', '-').replace('\'', '')
                                postgres_password = generate_password(16)
                                secret_key = generate_secret_key(32)
                                initial_password = generate_password(12)
                                add_progress_message('✅ Identifiants générés')
                                
                                # Exécuter le script de création de stack avec callback de progression
                                success, message = await create_client_stack(
                                    client_name=client_name,
                                    postgres_password=postgres_password,
                                    secret_key=secret_key,
                                    initial_password=initial_password,
                                    progress_callback=add_progress_message
                                )
                                
                                if success:
                                    add_progress_message('🎉 Instance déployée avec succès !')
                                    
                                    success_message = f'''✅ Essai gratuit activé ! Plan {plan_enregistre.upper()} - 30 jours gratuits
                                    
Votre instance est prête !
Identifiants temporaires :
- Utilisateur : {client_name}
- Mot de passe : {initial_password}

Vous recevrez un email avec les détails d'accès.'''
                                    
                                    dialog.close()
                                    ui.notify(success_message, type='positive', timeout=10000, multi_line=True)
                                else:
                                    add_progress_message(f'⚠️ Problème lors du déploiement')
                                    dialog.close()
                                    ui.notify(f'⚠️ Abonnement créé mais erreur lors du déploiement : {message}', type='warning', timeout=8000)
                                
                                db.close()
                                
                            except Exception as e:
                                add_progress_message(f'❌ Erreur : {str(e)}')
                                db.rollback()
                                dialog.close()
                                ui.notify(f'Erreur lors de l\'enregistrement : {e}', type='negative')
                            finally:
                                db.close()
                        
                        # Lancer la création de manière asynchrone
                        await run_creation()
                
                ui.button('Démarrer mon essai gratuit', on_click=start_trial).classes('w-full bg-green-500 hover:bg-green-600 text-lg py-4 mt-4')
                
                ui.label('✓ Pas de carte bancaire requise').classes('text-center text-gray-600 text-sm mt-4')
                ui.label('✓ Annulation à tout moment').classes('text-center text-gray-600 text-sm')
    
    create_footer()

def fix_db_sequences():
    """Corrige les séquences PostgreSQL si nécessaire"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        
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
            except Exception:
                db.rollback()
        
        db.close()
    except Exception:
        pass  # Ignorer les erreurs silencieusement

def main():
    """Lance le site commercial"""
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
        favicon='🏗️',
        dark=False
    )

if __name__ in {"__main__", "__mp_main__"}:
    main()
