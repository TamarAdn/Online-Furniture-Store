"""Test module for OrderManager functionality.

This module tests the OrderManager class which handles order creation,
retrieval, and management. It includes dummy classes for test fixtures,
parametrized tests for various scenarios, and tests for edge cases and
error handling.
"""
import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, cast
from unittest.mock import patch

import pytest

from app.models.enums import PaymentMethod
from app.models.order_manager import OrderManager
from app.utils import JsonFileManager


# ----------------------------
# Dummy classes for testing
# ----------------------------
class DummyFurniture:
    """Dummy furniture class for testing purposes.

    Simulates a furniture item with ID, name, and price properties.
    Used to create test orders without requiring the actual Furniture model.
    """

    def __init__(self, fid: str, name: str, final_price: float) -> None:
        """Initialize dummy furniture.

        Args:
            fid: Furniture ID
            name: Furniture name
            final_price: Final price of the furniture
        """
        self.id = fid
        self.name = name
        self._final_price = final_price

    def get_final_price(self) -> float:
        """Get the final price of the furniture.

        Simulates the pricing logic that would exist in the real Furniture model.
        This method allows tests to verify price calculations within orders.

        Returns:
            The final price of the furniture item
        """
        return self._final_price


class DummyOrder:
    """Dummy order class for testing purposes.

    Represents an order with all necessary properties for testing OrderManager.
    Contains user information, ordered items, pricing, shipping, and timestamps.
    """

    def __init__(
        self,
        order_id: str,
        user_id: str,
        items: List[Tuple[DummyFurniture, int]],
        total_price: float,
        payment_method: PaymentMethod,
        shipping_address: str,
        date: Optional[datetime.datetime] = None,
    ) -> None:
        """Initialize dummy order.

        Args:
            order_id: Order ID
            user_id: User ID
            items: List of tuples (furniture, quantity)
            total_price: Total price of the order
            payment_method: Payment method
            shipping_address: Shipping address
            date: Order date, defaults to current datetime
        """
        self.order_id = order_id
        self.user_id = user_id
        self.items = items  # List of tuples: (furniture, quantity)
        self.total_price = total_price
        self.payment_method = payment_method
        self.shipping_address = shipping_address
        self.date = date or datetime.datetime.now()


# Helper to create a dummy order with overrides
def dummy_order_instance(**overrides: Any) -> DummyOrder:
    """Create a dummy order instance with optional overrides.

    Factory function that creates a DummyOrder with sensible defaults
    that can be selectively overridden. This makes test setup more
    concise and focuses only on the values relevant to each test.

    Args:
        **overrides: Override values for the order attributes

    Returns:
        A DummyOrder instance with the specified overrides
    """
    default_items: List[Tuple[DummyFurniture, int]] = [
        (DummyFurniture("F1", "dummy_item", 50.0), 2)
    ]
    defaults: Dict[str, Any] = {
        "order_id": "O100",
        "user_id": "U100",
        "items": default_items,
        "total_price": 100.0,
        "payment_method": PaymentMethod.CREDIT_CARD,
        "shipping_address": "123 Main St",
        "date": datetime.datetime(2021, 1, 1, 12, 0, 0),
    }
    defaults.update(overrides)
    return DummyOrder(**defaults)


# ----------------------------
# Patch JsonFileManager methods for all tests in this file.
# ----------------------------
@pytest.fixture(autouse=True)
def patch_json_methods() -> None:
    """Patch JsonFileManager methods for all tests in this file.

    This fixture ensures that no actual file operations occur during testing.
    By patching the JsonFileManager's methods to do nothing or return predefined values,
    we isolate the tests from the filesystem and make them more predictable and faster.
    """
    JsonFileManager.ensure_file_exists = lambda file_path: None  # type: ignore
    JsonFileManager.read_json = lambda file_path: []  # type: ignore
    JsonFileManager.write_json = lambda file_path, data: None  # type: ignore


# ----------------------------
# Tests for OrderManager
# ----------------------------


def test_order_manager_init() -> None:
    """Test OrderManager initialization.

    Verifies that the OrderManager properly initializes by:
    1. Setting the correct file path from configuration
    2. Ensuring the file exists by calling the appropriate method
    """
    # Check that __init__ calls ensure_file_exists and sets _file_path correctly.
    from app.config import ORDERS_FILE

    with patch("app.utils.JsonFileManager.ensure_file_exists") as mock_ensure:
        om = OrderManager()
        mock_ensure.assert_called_once_with(om._file_path)
        assert om._file_path == ORDERS_FILE


@pytest.mark.parametrize(
    "order_kwargs",
    [
        # Single-item order with default date
        cast(Dict[str, Any], dummy_order_instance().__dict__),
        # Multi-item order with different total_price
        cast(
            Dict[str, Any],
            dummy_order_instance(
                total_price=200.0, items=[(DummyFurniture("F2", "item2", 75.0), 3)]
            ).__dict__,
        ),
    ],
)
def test_save_order_success(order_kwargs: Dict[str, Any]) -> None:
    """Test successful order saving with various order configurations.

    This test verifies that the OrderManager correctly:
    1. Saves an order to the JSON storage
    2. Formats the date using ISO format
    3. Properly serializes each order item with correct furniture details
    4. Works with both single-item and multi-item orders

    The test uses dynamic order objects created from the parametrized data
    and mocks the file operations to verify the data without actual I/O.

    Args:
        order_kwargs: Order keyword arguments from parametrize decorator
    """
    # Create a dummy order object dynamically.
    OrderObj = type("DummyOrderObj", (), order_kwargs)
    order = OrderObj()

    om = OrderManager()
    # We'll simulate file read/write by capturing a mutable orders_list.
    orders_list: List[Dict[str, Any]] = []

    def dummy_read(file_path: str) -> List[Dict[str, Any]]:
        return orders_list

    def dummy_write(file_path: str, data: List[Dict[str, Any]]) -> None:
        nonlocal orders_list
        orders_list = data

    with patch.object(
        JsonFileManager, "read_json", side_effect=dummy_read
    ), patch.object(JsonFileManager, "write_json", side_effect=dummy_write):
        result = om.save_order(order)
        assert result is True
        # Ensure one order is appended.
        assert len(orders_list) == 1
        saved_order = orders_list[0]
        # Check that the order's date was serialized using isoformat.
        assert saved_order["date"] == order.date.isoformat()
        # Verify that each order item is serialized correctly.
        for item, orig in zip(saved_order["items"], order.items):
            assert item["furniture_id"] == orig[0].id
            assert item["name"] == orig[0].name
            assert item["quantity"] == orig[1]
            assert item["unit_price"] == orig[0].get_final_price()


@pytest.mark.parametrize(
    "orders_list, order_id, expected",
    [
        # Order exists.
        ([{"order_id": "O1"}, {"order_id": "O2"}], "O1", {"order_id": "O1"}),
        # Order does not exist.
        ([{"order_id": "O1"}, {"order_id": "O2"}], "O3", None),
    ],
)
def test_get_order(
    orders_list: List[Dict[str, Any]], order_id: str, expected: Optional[Dict[str, Any]]
) -> None:
    """Test retrieving an order by its ID.

    This test verifies that OrderManager correctly:
    1. Searches through the orders list for a matching order_id
    2. Returns the correct order when found
    3. Returns None when the order doesn't exist

    The test uses parameterized inputs to test both scenarios (found/not found)
    without requiring duplicate test code.

    Args:
        orders_list: Mock list of orders to search through
        order_id: Order ID to retrieve
        expected: Expected result (order dict or None)
    """
    om = OrderManager()
    with patch.object(JsonFileManager, "read_json", return_value=orders_list):
        result = om.get_order(order_id)
        assert result == expected


@pytest.mark.parametrize(
    "orders_list, user_id, expected_count",
    [
        # Two orders for U1
        ([{"user_id": "U1"}, {"user_id": "U2"}, {"user_id": "U1"}], "U1", 2),
        # No orders for U3
        ([{"user_id": "U1"}, {"user_id": "U2"}], "U3", 0),
    ],
)
def test_get_user_orders(
    orders_list: List[Dict[str, Any]], user_id: str, expected_count: int
) -> None:
    """Test retrieving all orders for a specific user.

    This test verifies that the OrderManager correctly:
    1. Filters orders to only those belonging to the specified user_id
    2. Returns all matching orders as a list
    3. Returns an empty list when no orders match
    4. Properly handles different user IDs

    The test uses parameterized inputs to test multiple scenarios with
    various user IDs and expected result counts.

    Args:
        orders_list: Mock list of orders to filter
        user_id: User ID to retrieve orders for
        expected_count: Expected number of orders that should match
    """
    om = OrderManager()
    with patch.object(JsonFileManager, "read_json", return_value=orders_list):
        result = om.get_user_orders(user_id)
        assert isinstance(result, list)
        assert len(result) == expected_count


# --- Tests for unexpected inputs


def test_save_order_unexpected_order_object() -> None:
    """Test error handling when saving an invalid order object.

    This test verifies that the OrderManager correctly:
    1. Validates that the order object has required attributes
    2. Raises an appropriate exception when given an invalid object

    This ensures robust error handling for unexpected inputs.
    """
    om = OrderManager()

    # Create an order object that lacks required attributes.
    class IncompleteOrder:
        pass

    order = IncompleteOrder()
    with pytest.raises(AttributeError):
        om.save_order(order)


class StringOrder:
    """A non-object string masquerading as an order."""

    pass


class PartialOrder:
    """An order with only some of the required attributes."""

    def __init__(self) -> None:
        self.order_id = "O1"
        self.user_id = "U1"
        # Missing other required attributes


class MalformedOrder:
    """An order with attributes of incorrect types."""

    def __init__(self) -> None:
        self.order_id = "O1"
        self.user_id = "U1"
        self.date = "not a datetime"  # Wrong type
        self.total_price = "not a number"  # Wrong type
        self.payment_method = "not an enum"  # Wrong type
        self.shipping_address = 123  # Wrong type
        self.items = "not a list"  # Wrong type


@pytest.mark.parametrize(
    "invalid_order, expected_exception",
    [
        ("not an order", AttributeError),  # String instead of object
        (PartialOrder(), AttributeError),  # Missing attributes
        (MalformedOrder(), Exception),  # Wrong attribute types
        (None, AttributeError),  # None instead of order
        ({}, AttributeError),  # Dictionary instead of order
        ([], AttributeError),  # List instead of order
    ],
    ids=[
        "string_order",
        "partial_order",
        "malformed_order",
        "none_order",
        "dict_order",
        "list_order",
    ],
)
def test_save_order_checks_order_type(
    invalid_order: Any, expected_exception: Type[Exception]
) -> None:
    """Test that save_order validates the order object type with various invalid inputs.

    This test verifies that the OrderManager correctly:
    1. Validates the order object has the correct structure
    2. Raises appropriate exceptions for different kinds of invalid orders

    Args:
        invalid_order: An invalid order object to test with
        expected_exception: The exception type expected to be raised
    """
    om = OrderManager()

    with pytest.raises(expected_exception):
        om.save_order(invalid_order)


def test_get_order_unexpected_data_type() -> None:
    """Test error handling when reading orders returns invalid data.

    This test verifies that the OrderManager correctly:
    1. Checks the type of data returned from the storage
    2. Raises an appropriate exception when given non-list data

    This ensures the system fails gracefully if storage data is corrupted.
    """
    om = OrderManager()
    # If JsonFileManager.read_json returns a non-list value, our code may break.
    with patch.object(JsonFileManager, "read_json", return_value="not a list"):
        with pytest.raises(TypeError):
            om.get_order("any")


def test_get_user_orders_unexpected_data_type() -> None:
    """Test error handling when reading user orders with invalid data.

    This test verifies that the OrderManager correctly:
    1. Validates the data type from storage before processing
    2. Raises an appropriate exception when data isn't a list

    This tests the error handling path for get_user_orders when storage
    returns corrupted or invalid data.
    """
    om = OrderManager()
    with patch.object(JsonFileManager, "read_json", return_value="not a list"):
        with pytest.raises(TypeError):
            om.get_user_orders("U1")
