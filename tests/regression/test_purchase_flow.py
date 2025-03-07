import unittest
import uuid
from unittest.mock import patch

from app.config import TAX_RATE
from app.models.checkout_system import CheckoutSystem
from app.models.discount_strategy import PercentageDiscountStrategy
from app.models.enums import ChairMaterial, PaymentMethod, TableShape
from app.models.furniture import Chair, Table
from app.models.inventory import Inventory
from app.models.jwt_manager import JWTManager
from app.models.order_manager import OrderManager
from app.models.user_database import UserDatabase
from app.models.user_manager import UserManager


class PurchaseFlowRegressionTest(unittest.TestCase):
    """
    Regression test for the complete e-commerce purchase flow.

    This test verifies the end-to-end functionality of the purchase process by testing:
        1. User authentication and session management
        2. Product browsing and cart operations
        3. Price calculations including tax application
        4. Discount strategy application
        5. Checkout process and order creation
        6. Inventory updates after purchase

    The test provides comprehensive coverage of integration points between key system
    components: UserManager, Inventory, ShoppingCart, and CheckoutSystem. It ensures
    that these components work correctly together and that the complete purchase flow
    functions as expected.

    This regression test helps catch regressions when changes are made to any of the
    individual components in the purchase flow.
    """

    def setUp(self):
        """Set up test environment before each test."""
        # Initialize components
        self.user_db = UserDatabase()
        self.jwt_manager = JWTManager()
        self.user_manager = UserManager(self.user_db, self.jwt_manager)
        self.inventory = Inventory()
        self.order_manager = OrderManager()
        self.checkout_system = CheckoutSystem(self.inventory, self.order_manager)

        # Create a test user
        self.test_username = f"testuser_{uuid.uuid4()}"
        self.test_password = "Test@1234"  # Satisfies password strength requirements
        self.test_email = f"{self.test_username}@example.com"
        self.test_full_name = "Test User"
        self.test_address = "123 Test Street, Test City, 12345"

        # Mock the add_user method to avoid actual file operations
        with patch.object(UserDatabase, "add_user"), patch.object(
            UserDatabase, "username_exists", return_value=False
        ), patch.object(UserDatabase, "email_exists", return_value=False):
            self.test_user = self.user_manager.register_user(
                username=self.test_username,
                full_name=self.test_full_name,
                email=self.test_email,
                password=self.test_password,
                shipping_address=self.test_address,
            )

        # Add test products to inventory
        with patch.object(Inventory, "_save_inventory"):
            self.chair = Chair(
                price=100.0, material=ChairMaterial.WOOD.value, description="Test Chair"
            )
            self.chair_id = self.inventory.add_furniture(self.chair, quantity=10)

            self.table = Table(
                price=200.0, shape=TableShape.ROUND.value, description="Test Table"
            )
            self.table_id = self.inventory.add_furniture(self.table, quantity=5)

        # Login the test user
        with patch.object(
            UserDatabase,
            "validate_credentials",
            return_value={
                "id": self.test_user.id,
                "username": self.test_username,
                "full_name": self.test_full_name,
                "email": self.test_email,
                "shipping_address": self.test_address,
            },
        ):
            self.test_user, self.tokens = self.user_manager.login(
                self.test_username, self.test_password
            )

    def test_complete_purchase_flow(self):
        """
        Test the complete purchase flow from adding items to completing checkout.
        """
        # Step 1: Verify user is authenticated
        self.assertTrue(self.test_user.is_authenticated)

        # Step 2: Add items to cart
        cart = self.test_user.shopping_cart
        cart.add_item(self.chair, 2)
        cart.add_item(self.table, 1)

        # Verify items were added correctly
        cart_items = cart.get_items()
        self.assertEqual(len(cart_items), 2)

        # Find chair in cart
        chair_in_cart = None
        table_in_cart = None
        for item in cart_items:
            if item[0].id == self.chair_id:
                chair_in_cart = item
            elif item[0].id == self.table_id:
                table_in_cart = item

        self.assertIsNotNone(chair_in_cart, "Chair should be in the cart")
        self.assertIsNotNone(table_in_cart, "Table should be in the cart")
        self.assertEqual(chair_in_cart[1], 2, "Should have 2 chairs in cart")
        self.assertEqual(table_in_cart[1], 1, "Should have 1 table in cart")

        # Step 3: Calculate initial cart total
        initial_subtotal = cart.get_subtotal()

        # Use TAX_RATE from application config
        base_chair_price = 100.0
        base_table_price = 200.0

        # Chair price with tax * quantity
        taxed_chair_price = base_chair_price * (1 + TAX_RATE) * 2
        # Table price with tax * quantity
        taxed_table_price = base_table_price * (1 + TAX_RATE) * 1

        expected_subtotal = taxed_chair_price + taxed_table_price

        self.assertAlmostEqual(initial_subtotal, expected_subtotal, places=2)

        # Step 4: Apply a discount to the cart
        discount_strategy = PercentageDiscountStrategy(10)  # 10% discount
        cart.discount_strategy = discount_strategy

        # Calculate new total and verify discount was applied
        discounted_total = cart.get_total()

        # The discount is applied to the subtotal (which already includes tax),
        # then the result is returned as the total
        expected_discounted_total = expected_subtotal * 0.9  # 10% off

        # Compare with a small tolerance due to floating point calculations
        self.assertLess(
            abs(discounted_total - expected_discounted_total),
            0.01,
            f"Discounted total should be close to {expected_discounted_total}",
        )

        # Step 5: Complete checkout
        with patch.object(OrderManager, "save_order", return_value=True), patch.object(
            Inventory, "update_quantity", return_value=True
        ), patch.object(Inventory, "get_quantity", side_effect=[10, 5]):
            order = self.checkout_system.process_checkout(
                self.test_user, PaymentMethod.CREDIT_CARD
            )

        # Verify order was created with correct details
        self.assertEqual(order.user_id, self.test_user.id)
        self.assertEqual(order.total_price, discounted_total)
        self.assertEqual(order.payment_method, PaymentMethod.CREDIT_CARD)
        self.assertEqual(order.shipping_address, self.test_address)

        # Verify order items match cart items
        self.assertEqual(len(order.items), 2)

        # Verify cart is empty after checkout
        self.assertTrue(cart.is_empty())
