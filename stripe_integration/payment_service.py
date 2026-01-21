"""
Service de gestion des paiements avec Stripe
"""
import stripe
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from stripe_integration.stripe_config import SUBSCRIPTION_PLANS, STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_API_KEY


class PaymentService:
    """Service principal pour gérer les paiements Stripe"""

    @staticmethod
    def create_customer(email: str, name: str, metadata: Dict = None) -> str:
        """
        Crée un client Stripe
        
        Args:
            email: Email du client
            name: Nom du client
            metadata: Métadonnées additionnelles
            
        Returns:
            str: ID du client Stripe
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur lors de la création du client Stripe : {str(e)}")

    @staticmethod
    def create_payment_intent(amount: int, currency: str = 'eur', 
                             customer_id: str = None,
                             description: str = None) -> Dict:
        """
        Crée une intention de paiement
        
        Args:
            amount: Montant en centimes
            currency: Devise (par défaut EUR)
            customer_id: ID du client Stripe
            description: Description du paiement
            
        Returns:
            Dict: Détails du paiement créé
        """
        try:
            payload = {
                'amount': amount,
                'currency': currency
            }
            
            if customer_id:
                payload['customer'] = customer_id
            if description:
                payload['description'] = description
                
            intent = stripe.PaymentIntent.create(**payload)
            
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'status': intent.status,
                'amount': intent.amount,
                'currency': intent.currency
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur lors de la création du paiement : {str(e)}")

    @staticmethod
    def create_subscription(customer_id: str, plan: str, trial_days: int = 30) -> Dict:
        """
        Crée un abonnement pour un client
        
        Args:
            customer_id: ID du client Stripe
            plan: Plan d'abonnement ('starter', 'professional', 'enterprise')
            trial_days: Nombre de jours d'essai gratuit
            
        Returns:
            Dict: Détails de l'abonnement créé
        """
        try:
            if plan not in SUBSCRIPTION_PLANS:
                raise ValueError(f"Plan '{plan}' non trouvé")
            
            plan_info = SUBSCRIPTION_PLANS[plan]
            
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': plan_info['price_id'] or PaymentService._get_or_create_price(plan),
                }],
                trial_period_days=trial_days,
                payment_behavior='default_incomplete',
                metadata={'plan': plan}
            )
            
            return {
                'subscription_id': subscription.id,
                'customer_id': subscription.customer,
                'plan': plan,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'trial_end': subscription.trial_end
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur lors de la création de l'abonnement : {str(e)}")

    @staticmethod
    def _get_or_create_price(plan: str) -> str:
        """Obtient ou crée le price ID pour un plan donné"""
        if plan not in SUBSCRIPTION_PLANS:
            raise ValueError(f"Plan '{plan}' non trouvé")
            
        plan_info = SUBSCRIPTION_PLANS[plan]
        
        try:
            # Chercher les prix existants
            prices = stripe.Price.list(
                product=None,
                recurring={'interval': plan_info['interval']},
                type='recurring'
            )
            
            for price in prices.data:
                if price.unit_amount == plan_info['amount'] and price.currency == plan_info['currency']:
                    return price.id
            
            # Créer un nouveau prix
            product = stripe.Product.create(
                name=plan_info['name'],
                type='service',
                description=plan_info['description']
            )
            
            price = stripe.Price.create(
                product=product.id,
                unit_amount=plan_info['amount'],
                currency=plan_info['currency'],
                recurring={'interval': plan_info['interval']},
                lookup_key=f"price_{plan}"
            )
            
            return price.id
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur lors de la création du prix : {str(e)}")

    @staticmethod
    def retrieve_subscription(subscription_id: str) -> Dict:
        """
        Récupère les détails d'un abonnement
        
        Args:
            subscription_id: ID de l'abonnement
            
        Returns:
            Dict: Détails de l'abonnement
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                'subscription_id': subscription.id,
                'customer_id': subscription.customer,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'trial_end': subscription.trial_end,
                'items': subscription.items.data
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur lors de la récupération de l'abonnement : {str(e)}")

    @staticmethod
    def cancel_subscription(subscription_id: str, immediate: bool = False) -> Dict:
        """
        Annule un abonnement
        
        Args:
            subscription_id: ID de l'abonnement
            immediate: Si True, annule immédiatement; sinon à la fin de la période
            
        Returns:
            Dict: Détails de l'abonnement annulé
        """
        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'canceled_at': subscription.canceled_at,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur lors de l'annulation de l'abonnement : {str(e)}")

    @staticmethod
    def get_payment_methods(customer_id: str) -> List[Dict]:
        """
        Récupère les moyens de paiement d'un client
        
        Args:
            customer_id: ID du client
            
        Returns:
            List[Dict]: Liste des moyens de paiement
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            
            return [
                {
                    'id': pm.id,
                    'type': pm.type,
                    'card': {
                        'brand': pm.card.brand,
                        'last4': pm.card.last4,
                        'exp_month': pm.card.exp_month,
                        'exp_year': pm.card.exp_year
                    } if pm.card else None
                }
                for pm in payment_methods.data
            ]
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur lors de la récupération des moyens de paiement : {str(e)}")

    @staticmethod
    def validate_webhook(body: bytes, signature: str) -> Dict:
        """
        Valide et traite un webhook Stripe
        
        Args:
            body: Corps du webhook
            signature: Signature du webhook
            
        Returns:
            Dict: Événement webhook
        """
        try:
            event = stripe.Webhook.construct_event(
                body, signature, STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            raise Exception(f"Signature webhook invalide : {str(e)}")
        except ValueError as e:
            raise Exception(f"Erreur lors du traitement du webhook : {str(e)}")

    @staticmethod
    def get_invoice(invoice_id: str) -> Dict:
        """
        Récupère les détails d'une facture
        
        Args:
            invoice_id: ID de la facture
            
        Returns:
            Dict: Détails de la facture
        """
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            
            return {
                'invoice_id': invoice.id,
                'customer_id': invoice.customer,
                'amount': invoice.amount_paid,
                'status': invoice.status,
                'created': invoice.created,
                'due_date': invoice.due_date,
                'url': invoice.hosted_invoice_url
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur lors de la récupération de la facture : {str(e)}")
