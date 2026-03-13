import unittest
from src.models import CartItem
from src.pricing import PricingService, PricingError

class TestPricingService(unittest.TestCase):
    def setUp(self):
        self.pricing_logic = PricingService()

    def test_subtotal_calculation_standard(self):
        item1 = CartItem(sku="A", unit_price_cents=1500, qty=2)
        item2 = CartItem(sku="B", unit_price_cents=5000, qty=1)
        # 3000 + 5000 = 8000
        res = self.pricing_logic.subtotal_cents([item1, item2])
        self.assertEqual(res, 8000)

    def test_subtotal_error_cases(self):
        items_bad_qty = [CartItem("ERR", 100, 0)]
        with self.assertRaises(PricingError):
            self.pricing_logic.subtotal_cents(items_bad_qty)
            
        items_neg_price = [CartItem("ERR", -500, 1)]
        with self.assertRaises(PricingError) as cm:
            self.pricing_logic.subtotal_cents(items_neg_price)
        self.assertEqual(str(cm.exception), "unit_price_cents must be >= 0")

    def test_coupon_logic_variations(self):
        self.assertEqual(self.pricing_logic.apply_coupon(10000, " save10 "), 9000)
        self.assertEqual(self.pricing_logic.apply_coupon(5000, "CLP2000"), 3000)
        
        self.assertEqual(self.pricing_logic.apply_coupon(1500, "clp2000"), 0)

        self.assertEqual(self.pricing_logic.apply_coupon(1000, ""), 1000)
        self.assertEqual(self.pricing_logic.apply_coupon(1000, None), 1000)
        self.assertEqual(self.pricing_logic.apply_coupon(1000, "   "), 1000)
        
    def test_invalid_coupon(self):
        with self.assertRaisesRegex(PricingError, "invalid coupon"):
            self.pricing_logic.apply_coupon(1000, "DESCUENTO50")

    def test_taxes_by_country(self):
        self.assertEqual(self.pricing_logic.tax_cents(1000, "cl "), 190)
        self.assertEqual(self.pricing_logic.tax_cents(1000, "EU"), 210)
        self.assertEqual(self.pricing_logic.tax_cents(1000, "US"), 0)
        with self.assertRaises(PricingError):
            self.pricing_logic.tax_cents(1000, "AR")

    def test_shipping_costs_logic(self):
        #Chile hasta 20.000
        self.assertEqual(self.pricing_logic.shipping_cents(25000, "CL"), 0)
        self.assertEqual(self.pricing_logic.shipping_cents(15000, "CL"), 2500)
        #Internacional fijo
        self.assertEqual(self.pricing_logic.shipping_cents(100, "US"), 5000)
        self.assertEqual(self.pricing_logic.shipping_cents(50000, "EU"), 5000)
        with self.assertRaises(PricingError):
            self.pricing_logic.shipping_cents(1000, "UK")

    def test_full_pricing_integration(self):
        #2 items de 12.000 = 24.000 subtotal 
        #Cupon SAVE10 -> 21.600 net..... Tax CL (19%) = 4.104 entonces shipping CL = 0 (pq 21.600 >= 20.000)
        items = [CartItem("PROD", 12000, 2)]
        final = self.pricing_logic.total_cents(items, "SAVE10", "CL")
        self.assertEqual(final, 21600 + 4104 + 0)