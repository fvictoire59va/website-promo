"""
Intégration Stripe complète avec les endpoints FastAPI
À ajouter dans site_commercial.py
"""

from fastapi import Request, HTTPException
from stripe_integration import PaymentService
from stripe_integration.stripe_config import SUBSCRIPTION_PLANS
from datetime import datetime
from decimal import Decimal
from database_config import SessionLocal
from models import Client, Abonnement
import os

# ============================================================================
# ENDPOINTS POUR LES PAIEMENTS ET ABONNEMENTS
# ============================================================================

@app.post('/api/payment/create-customer')
async def create_stripe_customer(request: Request):
    """
    Crée un client Stripe et le lie au client ERP
    
    Body JSON:
    {
        "client_id": 123,
        "email": "client@example.com",
        "name": "Jean Dupont"
    }
    """
    try:
        data = await request.json()
        
        customer_id = PaymentService.create_customer(
            email=data['email'],
            name=data['name'],
            metadata={
                'client_id': str(data.get('client_id', '')),
                'created_at': datetime.now().isoformat()
            }
        )
        
        # Stocker le customer_id dans la base de données
        # UPDATE clients SET stripe_customer_id = customer_id WHERE id = client_id
        
        return {
            'success': True,
            'customer_id': customer_id,
            'message': 'Client créé avec succès'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/api/payment/create-payment-intent')
async def create_payment_intent(request: Request):
    """
    Crée une intention de paiement pour un paiement unique
    
    Body JSON:
    {
        "amount": 2900,  # en centimes
        "currency": "eur",
        "customer_id": "cus_...",
        "description": "Paiement abonnement Starter"
    }
    """
    try:
        data = await request.json()
        
        result = PaymentService.create_payment_intent(
            amount=data['amount'],
            currency=data.get('currency', 'eur'),
            customer_id=data.get('customer_id'),
            description=data.get('description')
        )
        
        return {
            'success': True,
            'payment_intent_id': result['payment_intent_id'],
            'client_secret': result['client_secret'],
            'amount': result['amount'],
            'currency': result['currency']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/api/subscription/create')
async def create_subscription(request: Request):
    """
    Crée un abonnement Stripe avec essai gratuit
    
    Body JSON:
    {
        "customer_id": "cus_...",
        "plan": "starter",  # starter, professional, enterprise
        "trial_days": 30
    }
    """
    try:
        data = await request.json()
        
        if data['plan'] not in ['starter', 'professional', 'enterprise']:
            raise ValueError("Plan invalide")
        
        subscription = PaymentService.create_subscription(
            customer_id=data['customer_id'],
            plan=data['plan'],
            trial_days=data.get('trial_days', 30)
        )
        
        # Stocker les données d'abonnement dans la base de données
        
        return {
            'success': True,
            'subscription_id': subscription['subscription_id'],
            'status': subscription['status'],
            'trial_end': subscription['trial_end'],
            'message': f"Abonnement {data['plan']} créé avec succès - 30 jours gratuits!"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/api/subscription/{subscription_id}')
async def get_subscription(subscription_id: str):
    """Récupère les détails d'un abonnement"""
    try:
        subscription = PaymentService.retrieve_subscription(subscription_id)
        return {
            'success': True,
            'subscription': subscription
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/api/subscription/{subscription_id}/cancel')
async def cancel_subscription(request: Request, subscription_id: str):
    """
    Annule un abonnement
    
    Body JSON:
    {
        "immediate": false  # false = à la fin de la période, true = immédiat
    }
    """
    try:
        data = await request.json()
        
        result = PaymentService.cancel_subscription(
            subscription_id=subscription_id,
            immediate=data.get('immediate', False)
        )
        
        return {
            'success': True,
            'subscription': result,
            'message': "Abonnement annulé" if result['cancel_at_period_end'] 
                      else "Abonnement arrêté immédiatement"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/api/payment-methods/{customer_id}')
async def get_customer_payment_methods(customer_id: str):
    """Récupère les moyens de paiement d'un client"""
    try:
        payment_methods = PaymentService.get_payment_methods(customer_id)
        
        return {
            'success': True,
            'payment_methods': payment_methods,
            'count': len(payment_methods)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/api/invoice/{invoice_id}')
async def get_invoice(invoice_id: str):
    """Récupère les détails d'une facture"""
    try:
        invoice = PaymentService.get_invoice(invoice_id)
        
        return {
            'success': True,
            'invoice': invoice
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/stripe-webhook')
async def stripe_webhook(request: Request):
    """
    Endpoint pour traiter les webhooks Stripe
    Important: Configurer cet URL dans le dashboard Stripe
    """
    try:
        body = await request.body()
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            raise HTTPException(status_code=400, detail="Signature manquante")
        
        event = PaymentService.validate_webhook(body, signature)
        
        # Traiter les différents événements
        event_type = event['type']
        event_data = event['data']['object']
        
        print(f"[Webhook] Événement reçu: {event_type}")
        
        if event_type == 'customer.subscription.created':
            print(f"✅ Abonnement créé: {event_data.get('id')}")
            # Mettre à jour le statut du client dans la BD
            # Envoyer un email de bienvenue
            
        elif event_type == 'customer.subscription.updated':
            print(f"🔄 Abonnement mis à jour: {event_data.get('id')}")
            # Mettre à jour les informations d'abonnement
            
        elif event_type == 'customer.subscription.deleted':
            print(f"❌ Abonnement annulé: {event_data.get('id')}")
            # Désactiver l'accès du client
            
        elif event_type == 'payment_intent.succeeded':
            print(f"✅ Paiement réussi: {event_data.get('id')}")
            # Marquer la commande comme payée
            # Générer une facture
            
        elif event_type == 'payment_intent.payment_failed':
            print(f"❌ Paiement échoué: {event_data.get('id')}")
            # Notifier le client du problème
            # Relancer le paiement
            
        elif event_type == 'invoice.created':
            print(f"📄 Facture créée: {event_data.get('id')}")
            # Stocker la facture dans la BD
            
        elif event_type == 'invoice.payment_succeeded':
            print(f"💰 Facture payée: {event_data.get('id')}")
            # Marquer la facture comme payée
        
        return {'status': 'success', 'event_id': event.get('id')}
        
    except Exception as e:
        print(f"❌ Erreur webhook: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 400


# ============================================================================
# PAGE UI NICEGUI POUR LE PAIEMENT
# ============================================================================

def create_payment_page():
    """Crée la page de paiement avec interface NiceGUI"""
    
    with ui.column().classes('w-full max-w-7xl mx-auto px-4 py-8'):
        ui.label('💳 Choisir votre abonnement').classes('text-4xl font-bold text-center mb-12')
        
        # Afficher les trois plans
        with ui.row().classes('w-full justify-center gap-8 flex-wrap'):
            
            # Plan Starter
            with ui.card().classes('w-80 shadow-xl hover:shadow-2xl transition-shadow'):
                with ui.column().classes('gap-6 p-6'):
                    ui.label('🚀 Plan Starter').classes('text-2xl font-bold text-blue-600')
                    ui.label('Idéal pour les petits chantiers').classes('text-gray-600')
                    
                    with ui.row().classes('items-baseline gap-1'):
                        ui.label('29').classes('text-4xl font-bold')
                        ui.label('€/mois').classes('text-lg')
                    
                    ui.label('30 jours d\'essai gratuit').classes(
                        'text-sm bg-green-100 text-green-800 px-3 py-1 rounded'
                    )
                    
                    ui.separator()
                    
                    with ui.column().classes('gap-3'):
                        ui.label('✅ Jusqu\'à 5 projets').classes('text-sm')
                        ui.label('✅ Support par email').classes('text-sm')
                        ui.label('✅ Rapports basiques').classes('text-sm')
                    
                    async def select_starter():
                        await select_plan('starter', 29)
                    
                    ui.button('Commencer', on_click=select_starter).classes(
                        'w-full bg-blue-600 hover:bg-blue-700 text-white'
                    )
            
            # Plan Professional
            with ui.card().classes('w-80 shadow-2xl border-2 border-orange-500'):
                with ui.column().classes('gap-6 p-6'):
                    ui.label('⭐ POPULAIRE').classes(
                        'text-xs font-bold text-white bg-orange-500 px-3 py-1 rounded w-fit'
                    )
                    ui.label('📊 Plan Professionnel').classes('text-2xl font-bold text-orange-600')
                    ui.label('Pour les entreprises en croissance').classes('text-gray-600')
                    
                    with ui.row().classes('items-baseline gap-1'):
                        ui.label('59').classes('text-4xl font-bold')
                        ui.label('€/mois').classes('text-lg')
                    
                    ui.label('30 jours d\'essai gratuit').classes(
                        'text-sm bg-green-100 text-green-800 px-3 py-1 rounded'
                    )
                    
                    ui.separator()
                    
                    with ui.column().classes('gap-3'):
                        ui.label('✅ Projets illimités').classes('text-sm')
                        ui.label('✅ Support prioritaire').classes('text-sm')
                        ui.label('✅ Rapports avancés').classes('text-sm')
                        ui.label('✅ Intégrations API').classes('text-sm')
                    
                    async def select_professional():
                        await select_plan('professional', 59)
                    
                    ui.button('Commencer', on_click=select_professional).classes(
                        'w-full bg-orange-600 hover:bg-orange-700 text-white'
                    )
            
            # Plan Enterprise
            with ui.card().classes('w-80 shadow-xl hover:shadow-2xl transition-shadow'):
                with ui.column().classes('gap-6 p-6'):
                    ui.label('🏢 Plan Entreprise').classes('text-2xl font-bold text-purple-600')
                    ui.label('Solutions personnalisées').classes('text-gray-600')
                    
                    with ui.row().classes('items-baseline gap-1'):
                        ui.label('149').classes('text-4xl font-bold')
                        ui.label('€/mois').classes('text-lg')
                    
                    ui.label('30 jours d\'essai gratuit').classes(
                        'text-sm bg-green-100 text-green-800 px-3 py-1 rounded'
                    )
                    
                    ui.separator()
                    
                    with ui.column().classes('gap-3'):
                        ui.label('✅ Tout du plan Pro').classes('text-sm')
                        ui.label('✅ Support 24/7').classes('text-sm')
                        ui.label('✅ Formation personnalisée').classes('text-sm')
                        ui.label('✅ Compte dédié').classes('text-sm')
                    
                    async def select_enterprise():
                        await select_plan('enterprise', 149)
                    
                    ui.button('Contacter', on_click=select_enterprise).classes(
                        'w-full bg-purple-600 hover:bg-purple-700 text-white'
                    )


async def select_plan(plan_name: str, price: int):
    """Affiche le formulaire de paiement quand un plan est sélectionné"""
    dialog = ui.dialog()
    
    with dialog, ui.card().classes('w-full max-w-2xl p-8'):
        ui.label('💳 Créez votre compte et payez').classes('text-3xl font-bold mb-6')
        
        # Formulaire
        form_data = {
            'nom': '',
            'prenom': '',
            'email': '',
            'entreprise': '',
            'telephone': '',
            'adresse': '',
            'ville': '',
            'code_postal': ''
        }
        
        error_label = ui.label().classes('text-red-600 font-semibold mb-4 hidden')
        success_label = ui.label().classes('text-green-600 font-semibold mb-4 hidden')
        
        with ui.column().classes('w-full gap-4'):
            # Identité
            with ui.row().classes('w-full gap-4'):
                nom_input = ui.input(label='Nom *').classes('flex-1').props('outlined')
                prenom_input = ui.input(label='Prénom *').classes('flex-1').props('outlined')
            
            email_input = ui.input(label='Email *').classes('w-full').props('outlined type=email')
            
            # Entreprise
            with ui.row().classes('w-full gap-4'):
                entreprise_input = ui.input(label='Entreprise *').classes('flex-1').props('outlined')
                telephone_input = ui.input(label='Téléphone').classes('flex-1').props('outlined')
            
            # Adresse
            adresse_input = ui.input(label='Adresse').classes('w-full').props('outlined')
            
            with ui.row().classes('w-full gap-4'):
                ville_input = ui.input(label='Ville').classes('flex-1').props('outlined')
                cp_input = ui.input(label='Code postal').classes('flex-1').props('outlined')
            
            ui.separator()
            
            # Moyens de paiement
            ui.label('Informations de paiement').classes('text-xl font-bold mt-4')
            
            # Élément Stripe pour la carte
            ui.html(f'''
            <div id="card-element" style="border: 1px solid #ccc; padding: 12px; border-radius: 4px; margin: 16px 0;"></div>
            <div id="card-errors" style="color: #fa755a; margin-top: 8px;"></div>
            ''')
            
            ui.separator()
            
            # Résumé
            ui.label('Résumé de votre commande').classes('text-lg font-semibold mt-4')
            
            with ui.card().classes('w-full p-4 bg-gray-50'):
                with ui.row().classes('w-full justify-between'):
                    ui.label('Plan choisi :').classes('font-semibold')
                    ui.label(plan_name.upper()).classes('font-bold text-blue-600')
                
                with ui.row().classes('w-full justify-between'):
                    ui.label('Prix mensuel :').classes('font-semibold')
                    ui.label(f'{price}€').classes('font-bold')
                
                with ui.row().classes('w-full justify-between'):
                    ui.label('Période d\'essai :').classes('font-semibold')
                    ui.label('30 jours gratuits').classes('text-green-600 font-bold')
                
                ui.separator().classes('my-2')
                
                with ui.row().classes('w-full justify-between'):
                    ui.label('Total à payer aujourd\'hui :').classes('text-lg font-bold')
                    ui.label('0€*').classes('text-lg font-bold text-green-600')
                
                ui.label('*Aucun frais pendant les 30 jours d\'essai').classes('text-xs text-gray-600 text-center mt-2')
            
            ui.separator()
            
            # Checkbox conditions
            agreed = ui.checkbox('J\'accepte les conditions d\'utilisation').classes('mt-4')
            
            # Boutons
            with ui.row().classes('w-full gap-4 mt-6'):
                ui.button('Annuler', on_click=dialog.close).classes('flex-1 bg-gray-500 hover:bg-gray-600')
                
                async def handle_payment():
                    """Traite le paiement"""
                    # Valider le formulaire
                    if not nom_input.value or not prenom_input.value or not email_input.value or not entreprise_input.value:
                        error_label.text = '❌ Veuillez remplir tous les champs obligatoires'
                        error_label.set_visibility(True)
                        return
                    
                    if not agreed.value:
                        error_label.text = '❌ Veuillez accepter les conditions d\'utilisation'
                        error_label.set_visibility(True)
                        return
                    
                    error_label.set_visibility(False)
                    
                    # Afficher un loader
                    submit_btn.enabled = False
                    submit_btn.text = '⏳ Traitement du paiement...'
                    
                    try:
                        # Créer le client Stripe et traiter le paiement
                        response = await ui.run.io_bound(
                            lambda: ui.context.client.session.post(
                                '/api/payment/process-subscription',
                                json={
                                    'nom': nom_input.value,
                                    'prenom': prenom_input.value,
                                    'email': email_input.value,
                                    'entreprise': entreprise_input.value,
                                    'telephone': telephone_input.value,
                                    'adresse': adresse_input.value,
                                    'ville': ville_input.value,
                                    'code_postal': cp_input.value,
                                    'plan': plan_name,
                                    'price': price
                                }
                            )
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            success_label.text = f'✅ {result.get("message", "Abonnement créé avec succès!")}'
                            success_label.set_visibility(True)
                            
                            # Rediriger vers la page de confirmation après 2 secondes
                            await asyncio.sleep(2)
                            ui.navigate.to(f'/confirmation/{result.get("client_id")}')
                        else:
                            error = response.json()
                            error_label.text = f'❌ Erreur: {error.get("message", "Erreur lors du paiement")}'
                            error_label.set_visibility(True)
                    except Exception as e:
                        error_label.text = f'❌ Erreur: {str(e)}'
                        error_label.set_visibility(True)
                    finally:
                        submit_btn.enabled = True
                        submit_btn.text = 'Créer mon compte'
                
                submit_btn = ui.button('Créer mon compte', on_click=handle_payment).classes('flex-1 bg-green-600 hover:bg-green-700 text-white')
        
        # Ajouter le script Stripe en bas du dialogue
        ui.html(f'''
        <script src="https://js.stripe.com/v3/"></script>
        <script>
        var stripe = Stripe('{os.getenv("STRIPE_PUBLISHABLE_KEY")}');
        var elements = stripe.elements();
        var cardElement = elements.create('card');
        cardElement.mount('#card-element');
        
        cardElement.on('change', function(event) {{
            var displayError = document.getElementById('card-errors');
            if (event.error) {{
                displayError.textContent = event.error.message;
            }} else {{
                displayError.textContent = '';
            }}
        }});
        </script>
        ''')
    
    dialog.open()



@app.get('/tarifs')
def tarifs_page():
    """Page de tarification"""
    ui.page_title('Tarifs - ERP BTP')
    create_header()
    
    with ui.column().classes('w-full'):
        create_payment_page()
        create_footer()
