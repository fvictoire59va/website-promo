"""
Exemple de page de paiement pour l'intégration Stripe
À ajouter dans le site_commercial.py
"""

# Ajouter cet import en haut du fichier:
# from stripe_integration import PaymentService, STRIPE_PUBLISHABLE_KEY

def create_payment_page():
    """Crée la page de paiement avec Stripe"""
    with ui.column().classes('w-full max-w-7xl mx-auto px-4 py-8'):
        ui.label('💳 Paiement de votre abonnement').classes('text-3xl font-bold mb-8')
        
        with ui.card().classes('w-full shadow-lg'):
            with ui.row().classes('w-full gap-8'):
                # Colonne gauche: Résumé de la commande
                with ui.column().classes('flex-1'):
                    ui.label('Résumé de votre commande').classes('text-xl font-bold mb-4')
                    
                    # Éléments de la commande
                    with ui.card().classes('w-full bg-blue-50 border-l-4 border-blue-500'):
                        plan = 'starter'  # À passer en paramètre
                        plan_info = SUBSCRIPTION_PLANS[plan]
                        
                        with ui.row().classes('w-full justify-between'):
                            ui.label(f"📦 {plan_info['name']}").classes('font-semibold')
                            ui.label(f"{plan_info['amount']/100:.2f}€").classes('font-bold text-lg text-blue-600')
                        
                        ui.label(plan_info['description']).classes('text-sm text-gray-600 mt-2')
                        
                        with ui.row().classes('w-full justify-between mt-4 pt-4 border-t'):
                            ui.label('Durée de l\'essai gratuit:').classes('font-semibold')
                            ui.label('30 jours').classes('text-green-600 font-bold')
                
                # Colonne droite: Formulaire de paiement
                with ui.column().classes('flex-1'):
                    ui.label('Informations de paiement').classes('text-xl font-bold mb-4')
                    
                    # Champs du formulaire
                    email = ui.input('Email').classes('w-full').props('outlined')
                    full_name = ui.input('Nom complet').classes('w-full').props('outlined')
                    
                    ui.label('Informations de la carte').classes('font-semibold mt-4 mb-2')
                    
                    # Note: Le stripe.js doit être intégré pour la vraie solution
                    ui.label('⚠️ L\'intégration Stripe Elements doit être complétée avec Stripe.js').classes('text-amber-600 text-sm')
                    
                    card_number = ui.input('Numéro de carte').classes('w-full').props('outlined')
                    
                    with ui.row().classes('w-full gap-4'):
                        expiry = ui.input('MM/YY').classes('flex-1').props('outlined')
                        cvc = ui.input('CVC').classes('flex-1').props('outlined')
                    
                    # Bouton de paiement
                    async def process_payment():
                        if not email.value or not full_name.value:
                            ui.notify('Veuillez remplir tous les champs', type='negative')
                            return
                        
                        try:
                            # Créer un client Stripe
                            customer_id = PaymentService.create_customer(
                                email=email.value,
                                name=full_name.value,
                                metadata={'signup_date': str(datetime.now())}
                            )
                            
                            # Créer un abonnement
                            subscription = PaymentService.create_subscription(
                                customer_id=customer_id,
                                plan='starter',
                                trial_days=30
                            )
                            
                            ui.notify('✅ Abonnement créé avec succès!', type='positive')
                            
                        except Exception as e:
                            ui.notify(f'❌ Erreur: {str(e)}', type='negative')
                    
                    with ui.row().classes('w-full gap-4 mt-6'):
                        ui.button('Essayer gratuitement', on_click=process_payment).classes(
                            'flex-1 bg-green-600 hover:bg-green-700 text-white'
                        )
                        ui.button('Annuler', on_click=lambda: ui.navigate.back()).classes(
                            'flex-1 bg-gray-300 hover:bg-gray-400'
                        )


# Route pour la page de paiement
@app.get('/paiement')
async def payment_page():
    """Page de paiement"""
    ui.page_title('Paiement - ERP BTP')
    create_header()
    create_payment_page()
