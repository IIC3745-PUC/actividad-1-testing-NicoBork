import unittest
from unittest.mock import Mock, MagicMock
from src.models import CartItem
from src.pricing import PricingService, PricingError
from src.checkout import CheckoutService, ChargeResult

class TestCheckoutService(unittest.TestCase):
    def setUp(self):
        self.mock_payments = Mock()
        self.mock_email = Mock()
        self.mock_fraud = Mock()
        self.mock_repo = Mock()
        self.mock_pricing = Mock()
        
        self.service = CheckoutService(
            payments=self.mock_payments,
            email=self.mock_email,
            fraud=self.mock_fraud,
            repo=self.mock_repo,
            pricing=self.mock_pricing
        )

    def test_checkout_invalid_user(self):
        result = self.service.checkout("  ", [], "token", "CL")
        self.assertEqual(result, "INVALID_USER")

    def test_checkout_pricing_error(self):
        self.mock_pricing.total_cents.side_effect = PricingError("test error")
        result = self.service.checkout("user1", [], "token", "CL")
        self.assertIn("INVALID_CART:test error", result)

    def test_checkout_rejected_fraud(self):
        self.mock_pricing.total_cents.return_value = 1000
        self.mock_fraud.score.return_value = 80
        result = self.service.checkout("user1", [], "token", "CL")
        self.assertEqual(result, "REJECTED_FRAUD")

    def test_checkout_payment_failed(self):
        self.mock_pricing.total_cents.return_value = 1000
        self.mock_fraud.score.return_value = 0
        self.mock_payments.charge.return_value = ChargeResult(ok=False, reason="no funds")
        
        result = self.service.checkout("user1", [], "token", "CL")
        self.assertIn("PAYMENT_FAILED:no funds", result)

    def test_checkout_success(self):
        self.mock_pricing.total_cents.return_value = 5000
        self.mock_fraud.score.return_value = 10
        self.mock_payments.charge.return_value = ChargeResult(ok=True, charge_id="ch123")
        
        result = self.service.checkout("user1", [CartItem("A", 5000, 1)], "token", "CL", "SAVE10")
        
        self.assertTrue(result.startswith("OK:"))
        self.mock_repo.save.assert_called_once()
        self.mock_email.send_receipt.assert_called_once()

    def test_default_pricing_init(self):
        service = CheckoutService(Mock(), Mock(), Mock(), Mock())
        self.assertIsInstance(service.pricing, PricingService)