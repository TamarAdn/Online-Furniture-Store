import datetime
from typing import Any, Dict, List, Tuple, Union

import pytest

from app.models.enums import PaymentMethod
from app.models.order import Order


@pytest.fixture
def valid_order_data() -> Dict[str, Any]:
    """
    Returns a dictionary of valid order parameters.

    Returns:
        Dict containing valid order creation parameters
    """
    return {
        "order_id": "O123",
        "user_id": "U456",
        "items": [("item1", 2), ("item2", 3)],
        "total_price": 150.75,
        "payment_method": PaymentMethod.CREDIT_CARD,
        "shipping_address": "123 Test St, Test City",
    }


def test_order_valid(valid_order_data: Dict[str, Any]) -> None:
    """
    Test that an order is created successfully with valid parameters.

    Args:
        valid_order_data: Fixture providing valid order parameters
    """
    order = Order(**valid_order_data)
    assert order.id == valid_order_data["order_id"]

    expected_str = f"Order #{valid_order_data['order_id']} - ${valid_order_data['total_price']:.2f}"
    assert str(order) == expected_str

    assert isinstance(order.date, datetime.datetime)


@pytest.mark.parametrize(
    "items_input",
    ["not a list", 123, {"item": ("item1", 2)}],
    ids=["string", "integer", "dictionary"],
)
def test_order_invalid_items_type(
    valid_order_data: Dict[str, Any], items_input: Any
) -> None:
    """
    Test that passing a non-list value for items raises a TypeError.

    Args:
        valid_order_data: Fixture providing valid order parameters
        items_input: Invalid input for items field
    """
    valid_order_data["items"] = items_input
    with pytest.raises(TypeError, match="Items must be a list"):
        Order(**valid_order_data)


@pytest.mark.parametrize(
    "item_element",
    ["not a tuple", ("only one",), ("too", "many", "elements")],
    ids=["string", "single_element_tuple", "too_many_elements"],
)
def test_order_invalid_item_elements(
    valid_order_data: Dict[str, Any], item_element: Any
) -> None:
    """
    Test that each item in items must be a tuple (or list) with exactly 2 elements.

    Args:
        valid_order_data: Fixture providing valid order parameters
        item_element: Invalid item element to test
    """
    valid_order_data["items"] = [item_element]
    with pytest.raises(
        TypeError, match=r"Each item must be a \(furniture, quantity\) tuple or list"
    ):
        Order(**valid_order_data)


@pytest.mark.parametrize(
    "total_price, expected_str",
    [
        (123.456, "Order #O123 - $123.46"),
        (50, "Order #O123 - $50.00"),
        (0.99, "Order #O123 - $0.99"),
    ],
    ids=["decimal_rounding", "integer", "cents_only"],
)
def test_order_str_format(
    valid_order_data: Dict[str, Any], total_price: Union[int, float], expected_str: str
) -> None:
    """
    Test that the __str__ method formats the total price to two decimal places.

    Args:
        valid_order_data: Fixture providing valid order parameters
        total_price: Price value to test
        expected_str: Expected string representation
    """
    valid_order_data["total_price"] = total_price
    order = Order(**valid_order_data)
    assert str(order) == expected_str


def test_order_custom_date(valid_order_data: Dict[str, Any]) -> None:
    """
    Test that providing a custom date sets the order's date accordingly.

    Args:
        valid_order_data: Fixture providing valid order parameters
    """
    custom_date = datetime.datetime(2020, 1, 1, 12, 0, 0)
    valid_order_data["date"] = custom_date
    order = Order(**valid_order_data)
    assert order.date == custom_date


@pytest.mark.parametrize(
    "payment_method", list(PaymentMethod), ids=[pm.name for pm in PaymentMethod]
)
def test_order_payment_method(
    valid_order_data: Dict[str, Any], payment_method: PaymentMethod
) -> None:
    """
    Test that the payment_method property is set correctly for various PaymentMethod values.

    Args:
        valid_order_data: Fixture providing valid order parameters
        payment_method: Payment method enum value to test
    """
    valid_order_data["payment_method"] = payment_method
    order = Order(**valid_order_data)
    assert order.payment_method == payment_method


@pytest.mark.parametrize(
    "invalid_id", [None, 123, True, [], {}], ids=["None", "int", "bool", "list", "dict"]
)
def test_order_invalid_order_id(valid_order_data: Dict[str, Any], invalid_id: Any) -> None:
    """
    Test that order_id must be a string.

    Args:
        valid_order_data: Fixture providing valid order parameters
        invalid_id: Invalid order_id value to test
    """
    valid_order_data["order_id"] = invalid_id  # Modify only the field being tested
    with pytest.raises(TypeError, match="order_id must be a string"):
        Order(**valid_order_data)


@pytest.mark.parametrize(
    "invalid_id",
    [None, 456, False, (), set()],
    ids=["None", "int", "bool", "tuple", "set"],
)
def test_order_invalid_user_id(valid_order_data: Dict[str, Any], invalid_id: Any) -> None:
    """
    Test that user_id must be a string.

    Args:
        valid_order_data: Fixture providing valid order parameters
        invalid_id: Invalid user_id value to test
    """
    valid_order_data["user_id"] = invalid_id
    with pytest.raises(TypeError, match="user_id must be a string"):
        Order(**valid_order_data)


def test_order_empty_items(valid_order_data: Dict[str, Any]) -> None:
    """
    Test that an order with no items raises a ValueError.

    Args:
        valid_order_data: Fixture providing valid order parameters
    """
    valid_order_data["items"] = []
    with pytest.raises(ValueError, match="Order must contain at least one item"):
        Order(**valid_order_data)


@pytest.mark.parametrize(
    "invalid_payment",
    [None, "CASH", 123, True, [], {}],
    ids=["None", "string", "int", "bool", "list", "dict"],
)
def test_order_invalid_payment_method(
    valid_order_data: Dict[str, Any], invalid_payment: Any
) -> None:
    """
    Test that payment_method must be a valid PaymentMethod enum.

    Args:
        valid_order_data: Fixture providing valid order parameters
        invalid_payment: Invalid payment method value to test
    """
    valid_order_data["payment_method"] = invalid_payment
    with pytest.raises(TypeError, match="payment_method must be a valid PaymentMethod enum"):
        Order(**valid_order_data)


@pytest.mark.parametrize(
    "invalid_price",
    [-1, -100.5, -0.01],
    ids=["negative_integer", "negative_large_decimal", "negative_small_decimal"],
)
def test_order_negative_total_price(
    valid_order_data: Dict[str, Any], invalid_price: Union[int, float]
) -> None:
    """
    Test that a negative total_price raises a ValueError.

    Args:
        valid_order_data: Fixture providing valid order parameters
        invalid_price: Negative price value to test
    """
    valid_order_data["total_price"] = invalid_price
    with pytest.raises(ValueError, match="total_price must be a non-negative number"):
        Order(**valid_order_data)


@pytest.mark.parametrize(
    "invalid_price_type",
    ["100", [100], {"price": 100}, (100,)],
    ids=["string", "list", "dict", "tuple"],
)
def test_order_invalid_price_type(
    valid_order_data: Dict[str, Any], invalid_price_type: Any
) -> None:
    """
    Test that a non-numeric total_price raises a ValueError.

    Args:
        valid_order_data: Fixture providing valid order parameters
        invalid_price_type: Invalid price type to test
    """
    valid_order_data["total_price"] = invalid_price_type
    with pytest.raises(ValueError, match="total_price must be a non-negative number"):
        Order(**valid_order_data)
