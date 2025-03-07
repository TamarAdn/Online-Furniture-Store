from unittest.mock import Mock, patch

import pytest

from app.models.cart_item_locator import CartItemLocator
from app.models.inventory import Inventory
from app.models.shopping_cart import ShoppingCart


class TestCartItemLocator:
    """
    Test suite for the CartItemLocator class.

    This test uses parametrization to test different furniture types and attributes.
    """

    @pytest.fixture
    def mock_inventory(self):
        """
        Fixture that creates a mock Inventory instance.
        """
        return Mock(spec=Inventory)

    @pytest.fixture
    def mock_cart(self):
        """
        Fixture that creates a mock ShoppingCart instance.
        """
        return Mock(spec=ShoppingCart)

    @pytest.fixture
    def mock_furniture(self, request):
        """
        Fixture that creates a mock furniture item with specified attributes.
        """
        mock_item = Mock()
        mock_item.id = request.param.get("id", 1)
        furniture_class = request.param.get("class_name", "Chair")
        # Set the mock's class name to simulate the furniture class.
        type(mock_item).__name__ = furniture_class
        for attr_name, attr_value in request.param.get("attributes", {}).items():
            setattr(mock_item, attr_name, attr_value)
        return mock_item

    @pytest.mark.parametrize(
        "furniture_type,quantity,attributes,expected_result",
        [
            ("chair", 1, {"color": "black"}, True),
            ("table", 2, {"material": "wood", "color": "brown"}, True),
            ("sofa", 1, {}, True),
            ("bed", 3, {"size": "queen"}, True),
            ("bookcase", 1, {"shelves": 5}, True),
        ],
    )
    def test_find_and_add_to_cart_success(
        self,
        mock_inventory,
        mock_cart,
        furniture_type,
        quantity,
        attributes,
        expected_result,
    ):
        """
        Test successful item location and addition to cart.
        """
        locator = CartItemLocator(mock_inventory)
        furniture_class = CartItemLocator._CLASS_MAP.get(furniture_type.lower())
        mock_furniture = Mock()
        mock_furniture.id = 1
        type(mock_furniture).__name__ = furniture_class

        # Configure search to return a result with sufficient quantity.
        search_results = [{"furniture": mock_furniture, "quantity": quantity + 1}]
        mock_inventory.search.return_value = search_results

        result = locator.find_and_add_to_cart(
            mock_cart, furniture_type, quantity, **attributes
        )

        # Expect one search per attribute, or one if no attributes.
        expected_calls = len(attributes) if attributes else 1
        assert mock_inventory.search.call_count == expected_calls
        mock_cart.add_item.assert_called_once_with(mock_furniture, quantity)
        assert result == expected_result

    @pytest.mark.parametrize(
        "furniture_type,quantity,attributes,exception_msg",
        [
            ("unknown", 1, {}, "Unknown furniture type: unknown"),
            ("chair", 1, {"color": "black"}, "No chair found with color=black"),
            (
                "table",
                3,
                {"material": "wood"},
                "Not enough table in stock with the specified attributes",
            ),
            # For multiple attributes with no intersection,
            # we expect the "combination" error.
            (
                "sofa",
                1,
                {"color": "black", "material": "leather"},
                "No sofa found with the specified combination of attributes",
            ),
        ],
    )
    def test_find_and_add_to_cart_failure(
        self,
        mock_inventory,
        mock_cart,
        furniture_type,
        quantity,
        attributes,
        exception_msg,
    ):
        """
        Test failure scenarios when trying to locate and add items to cart.
        """
        locator = CartItemLocator(mock_inventory)

        if furniture_type == "unknown":
            # No configuration needed; should raise immediately.
            pass
        elif "combination" in exception_msg:
            # For multiple attributes with no intersection:
            # First attribute search returns an item with id=1.
            # Second attribute search returns a list
            # containing an item with a different id.
            mock_item1 = Mock()
            mock_item1.id = 1
            mock_item2 = Mock()
            mock_item2.id = 2
            mock_inventory.search.side_effect = [
                [{"furniture": mock_item1, "quantity": quantity + 1}],
                [{"furniture": mock_item2, "quantity": quantity + 1}],
            ]
        elif "enough" in exception_msg:
            # For insufficient quantity:
            mock_item = Mock()
            mock_item.id = 1
            mock_inventory.search.return_value = [
                {"furniture": mock_item, "quantity": quantity - 1}
            ]
        else:
            # For no result found for a single attribute.
            mock_inventory.search.return_value = []

        with pytest.raises(ValueError) as exc_info:
            locator.find_and_add_to_cart(
                mock_cart, furniture_type, quantity, **attributes
            )

        assert exception_msg in str(exc_info.value)

    @pytest.mark.parametrize(
        "mock_furniture",
        [
            {"id": 1, "class_name": "Chair", "attributes": {"color": "black"}},
            {"id": 2, "class_name": "Table", "attributes": {"material": "wood"}},
        ],
        indirect=True,
    )
    def test_enum_attribute_conversion(self, mock_inventory, mock_cart, mock_furniture):
        """
        Test that enum attributes are correctly converted
        to string representation.
        """
        locator = CartItemLocator(mock_inventory)
        # Create a mock enum-like object with a 'value' attribute.
        mock_enum = Mock()
        mock_enum.value = (
            "black" if mock_furniture.__class__.__name__ == "Chair" else "wood"
        )
        mock_inventory.search.return_value = [
            {"furniture": mock_furniture, "quantity": 5}
        ]

        attr_name = (
            "color" if mock_furniture.__class__.__name__ == "Chair" else "material"
        )
        furniture_type = (
            "chair" if mock_furniture.__class__.__name__ == "Chair" else "table"
        )
        attributes = {attr_name: mock_enum}

        result = locator.find_and_add_to_cart(
            mock_cart, furniture_type, 1, **attributes
        )

        assert result is True
        mock_cart.add_item.assert_called_once_with(mock_furniture, 1)

    def test_default_inventory_creation(self):
        """
        Test that a default inventory is created if none is provided.
        """
        with patch("app.models.cart_item_locator.Inventory") as mock_inventory_class:
            mock_inventory_instance = Mock(spec=Inventory)
            mock_inventory_class.return_value = mock_inventory_instance

            locator = CartItemLocator()
            mock_inventory_class.assert_called_once()
            assert locator._inventory == mock_inventory_instance

    def test_no_inventory_found(self, mock_inventory, mock_cart):
        """
        Test that when no attributes are provided and the inventory
        search returns empty, the method raises the appropriate ValueError.
        """
        locator = CartItemLocator(mock_inventory)
        # When no attributes are provided, the search is done by furniture type.
        mock_inventory.search.return_value = []

        with pytest.raises(ValueError) as exc_info:
            locator.find_and_add_to_cart(mock_cart, "sofa", 1)
        assert "No sofa found in inventory" in str(exc_info.value)
