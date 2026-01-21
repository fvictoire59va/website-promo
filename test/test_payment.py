"""
Tests d'intégration pour les paiements Stripe
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from stripe_integration.payment_service import PaymentService
from stripe_integration.stripe_config import SUBSCRIPTION_PLANS


class TestPaymentService:
    """Tests pour le service de paiement Stripe"""

    @patch('stripe_integration.payment_service.stripe.Customer')
    def test_create_customer(self, mock_customer):
        """Test la création d'un client Stripe"""
        # Arrange
        mock_customer.create.return_value = Mock(id='cus_test123')
        email = 'test@example.com'
        name = 'Test Client'
        
        # Act
        customer_id = PaymentService.create_customer(email, name)
        
        # Assert
        assert customer_id == 'cus_test123'
        mock_customer.create.assert_called_once()

    @patch('stripe_integration.payment_service.stripe.Customer')
    def test_create_customer_with_metadata(self, mock_customer):
        """Test la création d'un client avec métadonnées"""
        # Arrange
        mock_customer.create.return_value = Mock(id='cus_test456')
        metadata = {'company_id': '123', 'plan': 'starter'}
        
        # Act
        customer_id = PaymentService.create_customer(
            'test@example.com',
            'Test Client',
            metadata=metadata
        )
        
        # Assert
        assert customer_id == 'cus_test456'

    @patch('stripe_integration.payment_service.stripe.PaymentIntent')
    def test_create_payment_intent(self, mock_intent):
        """Test la création d'une intention de paiement"""
        # Arrange
        mock_intent_obj = Mock(
            client_secret='pi_test_secret',
            id='pi_test123',
            status='requires_payment_method',
            amount=2900,
            currency='eur'
        )
        mock_intent.create.return_value = mock_intent_obj
        
        # Act
        result = PaymentService.create_payment_intent(
            amount=2900,
            currency='eur',
            description='Test payment'
        )
        
        # Assert
        assert result['payment_intent_id'] == 'pi_test123'
        assert result['client_secret'] == 'pi_test_secret'
        assert result['status'] == 'requires_payment_method'

    @patch('stripe_integration.payment_service.stripe.Subscription')
    @patch('stripe_integration.payment_service.PaymentService._get_or_create_price')
    def test_create_subscription(self, mock_get_price, mock_subscription):
        """Test la création d'un abonnement"""
        # Arrange
        mock_get_price.return_value = 'price_test123'
        mock_subscription_obj = Mock(
            id='sub_test123',
            customer='cus_test123',
            status='active',
            current_period_start=1234567890,
            current_period_end=1237246690,
            trial_end=1237246690
        )
        mock_subscription.create.return_value = mock_subscription_obj
        
        # Act
        result = PaymentService.create_subscription(
            customer_id='cus_test123',
            plan='starter',
            trial_days=30
        )
        
        # Assert
        assert result['subscription_id'] == 'sub_test123'
        assert result['customer_id'] == 'cus_test123'
        assert result['plan'] == 'starter'
        assert result['status'] == 'active'

    @patch('stripe_integration.payment_service.stripe.Subscription')
    def test_create_subscription_invalid_plan(self, mock_subscription):
        """Test la création d'abonnement avec un plan invalide"""
        # Act & Assert
        with pytest.raises(ValueError, match="Plan 'invalid' non trouvé"):
            PaymentService.create_subscription(
                customer_id='cus_test123',
                plan='invalid'
            )

    @patch('stripe_integration.payment_service.stripe.Subscription')
    def test_retrieve_subscription(self, mock_subscription):
        """Test la récupération d'un abonnement"""
        # Arrange
        mock_subscription_obj = Mock(
            id='sub_test123',
            customer='cus_test123',
            status='active',
            current_period_start=1234567890,
            current_period_end=1237246690,
            trial_end=1237246690,
            items=Mock(data=[])
        )
        mock_subscription.retrieve.return_value = mock_subscription_obj
        
        # Act
        result = PaymentService.retrieve_subscription('sub_test123')
        
        # Assert
        assert result['subscription_id'] == 'sub_test123'
        assert result['status'] == 'active'
        mock_subscription.retrieve.assert_called_once_with('sub_test123')

    @patch('stripe_integration.payment_service.stripe.Subscription')
    def test_cancel_subscription_immediate(self, mock_subscription):
        """Test l'annulation immédiate d'un abonnement"""
        # Arrange
        mock_subscription_obj = Mock(
            id='sub_test123',
            status='canceled',
            canceled_at=1234567890,
            cancel_at_period_end=False
        )
        mock_subscription.delete.return_value = mock_subscription_obj
        
        # Act
        result = PaymentService.cancel_subscription('sub_test123', immediate=True)
        
        # Assert
        assert result['subscription_id'] == 'sub_test123'
        assert result['status'] == 'canceled'
        mock_subscription.delete.assert_called_once_with('sub_test123')

    @patch('stripe_integration.payment_service.stripe.Subscription')
    def test_cancel_subscription_at_period_end(self, mock_subscription):
        """Test l'annulation d'un abonnement à la fin de la période"""
        # Arrange
        mock_subscription_obj = Mock(
            id='sub_test123',
            status='active',
            canceled_at=None,
            cancel_at_period_end=True
        )
        mock_subscription.modify.return_value = mock_subscription_obj
        
        # Act
        result = PaymentService.cancel_subscription('sub_test123', immediate=False)
        
        # Assert
        assert result['cancel_at_period_end'] is True
        mock_subscription.modify.assert_called_once()

    @patch('stripe_integration.payment_service.stripe.PaymentMethod')
    def test_get_payment_methods(self, mock_payment_method):
        """Test la récupération des moyens de paiement"""
        # Arrange
        mock_card = Mock(
            brand='visa',
            last4='4242',
            exp_month=12,
            exp_year=2025
        )
        mock_pm = Mock(
            id='pm_test123',
            type='card',
            card=mock_card
        )
        mock_payment_method.list.return_value = Mock(data=[mock_pm])
        
        # Act
        result = PaymentService.get_payment_methods('cus_test123')
        
        # Assert
        assert len(result) == 1
        assert result[0]['id'] == 'pm_test123'
        assert result[0]['card']['last4'] == '4242'

    @patch('stripe_integration.payment_service.stripe.Webhook')
    def test_validate_webhook(self, mock_webhook):
        """Test la validation d'un webhook"""
        # Arrange
        expected_event = {
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_test123'}}
        }
        mock_webhook.construct_event.return_value = expected_event
        
        # Act
        result = PaymentService.validate_webhook(b'test_body', 'test_signature')
        
        # Assert
        assert result['type'] == 'payment_intent.succeeded'

    @patch('stripe_integration.payment_service.stripe.Invoice')
    def test_get_invoice(self, mock_invoice):
        """Test la récupération d'une facture"""
        # Arrange
        mock_invoice_obj = Mock(
            id='in_test123',
            customer='cus_test123',
            amount_paid=2900,
            status='paid',
            created=1234567890,
            due_date=1234654290,
            hosted_invoice_url='https://invoice.stripe.com/test'
        )
        mock_invoice.retrieve.return_value = mock_invoice_obj
        
        # Act
        result = PaymentService.get_invoice('in_test123')
        
        # Assert
        assert result['invoice_id'] == 'in_test123'
        assert result['status'] == 'paid'
        assert result['amount'] == 2900


class TestSubscriptionPlans:
    """Tests pour les plans d'abonnement"""

    def test_plans_exist(self):
        """Vérifie que tous les plans sont définis"""
        assert 'starter' in SUBSCRIPTION_PLANS
        assert 'professional' in SUBSCRIPTION_PLANS
        assert 'enterprise' in SUBSCRIPTION_PLANS

    def test_plan_structure(self):
        """Vérifie la structure des plans"""
        for plan_name, plan_info in SUBSCRIPTION_PLANS.items():
            assert 'name' in plan_info
            assert 'amount' in plan_info
            assert 'currency' in plan_info
            assert 'interval' in plan_info
            assert 'description' in plan_info

    def test_plan_amounts(self):
        """Vérifie que les montants sont croissants"""
        starter_amount = SUBSCRIPTION_PLANS['starter']['amount']
        professional_amount = SUBSCRIPTION_PLANS['professional']['amount']
        enterprise_amount = SUBSCRIPTION_PLANS['enterprise']['amount']
        
        assert starter_amount < professional_amount < enterprise_amount

    def test_plan_currency(self):
        """Vérifie que la devise est EUR"""
        for plan_info in SUBSCRIPTION_PLANS.values():
            assert plan_info['currency'] == 'eur'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
