import uuid
from typing import Any, Dict, List, Union
from unittest.mock import patch

import pytest

from app.models.furniture import Bed, Bookcase, Chair, Furniture, Sofa, Table
from app.models.inventory import Inventory
from app.models.search_strategy import SearchStrategy
from app.utils import JsonFileManager


# Fixture to automatically patch JsonFileManager methods and reset the singleton.
@pytest.fixture(autouse=True)
def patch_json_file_manager_and_reset_singleton() -> None:
    """Patch JsonFileManager methods and reset Inventory singleton."""
    # Prevent file I/O by overriding these methods.
    JsonFileManager.ensure_file_exists = lambda file_path: None
    JsonFileManager.read_json = lambda file_path: []
    JsonFileManager.write_json = lambda file_path, data: None
    # Reset the singleton instance so each test gets a fresh Inventory.
    Inventory._instance = None


# --- Dummy SearchStrategy for testing the search() method ---
class DummySearchStrategy(SearchStrategy):
    """Dummy search strategy implementation for testing."""

    def search(
        self, inventory: Dict[str, List[Union[Furniture, int]]]
    ) -> List[Dict[str, Any]]:
        """Search implementation that returns all items with quantity > 0."""
        return [
            {"furniture": item_data[0], "quantity": item_data[1]}
            for item_data in inventory.values()
            if item_data[1] > 0
        ]


# ----------------------------
# Tests for the Inventory class
# ----------------------------


def test_singleton() -> None:
    """Test that Inventory follows singleton pattern."""
    inv1 = Inventory()
    inv2 = Inventory()
    assert inv1 is inv2


def test_generate_id() -> None:
    """Test ID generation for inventory items."""
    inv = Inventory()
    new_id = inv._generate_id()
    # Check that the returned id is a valid UUID string.
    uuid.UUID(new_id)  # will raise ValueError if invalid
    assert isinstance(new_id, str)


def test_load_inventory() -> None:
    """Test inventory loading from storage."""
    # Provide dummy data for two furniture items.
    dummy_data = [
        {
            "furniture": {
                "id": "F1",
                "name": "chair",
                "price": 100.0,
                "description": "desc",
                "attributes": {"material": "wood"},
            },
            "quantity": 5,
        },
        {
            "furniture": {
                "id": "F2",
                "name": "table",
                "price": 200.0,
                "description": "desc",
                "attributes": {"shape": "round", "size": "medium"},
            },
            "quantity": 3,
        },
    ]
    with patch.object(JsonFileManager, "read_json", return_value=dummy_data):
        inv = Inventory()
        # _load_inventory is called during __init__
        assert len(inv._inventory) == 2
        for key, (furniture, qty) in inv._inventory.items():
            assert key in ["F1", "F2"]
            assert isinstance(furniture, Furniture)


def test_load_inventory_with_invalid_item(capsys) -> None:
    """Test handling of invalid items during inventory loading."""
    # Supply an item that will fail _create_furniture_from_dict (missing "name").
    dummy_data = [
        {
            "furniture": {
                # "name" is missing
                "price": 100.0,
                "description": "desc",
                "attributes": {"material": "wood"},
            },
            "quantity": 5,
        }
    ]
    with patch.object(JsonFileManager, "read_json", return_value=dummy_data):
        inv = Inventory()
        captured = capsys.readouterr().out
        assert "Error loading inventory item:" in captured
        # Inventory should remain empty because the item failed to load.
        assert len(inv._inventory) == 0


# --- Tests for add_furniture ---


def test_add_furniture_invalid_item() -> None:
    """Test adding invalid item to inventory."""
    inv = Inventory()
    with pytest.raises(TypeError, match="Item must be a Furniture object"):
        inv.add_furniture("not a furniture", 1)


def test_add_furniture_invalid_quantity() -> None:
    """Test adding furniture with invalid quantity."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood", description="Simple chair")
    with pytest.raises(ValueError, match="Quantity must be positive"):
        inv.add_furniture(furniture, 0)


def test_add_furniture_success() -> None:
    """Test successful furniture addition to inventory."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood", description="Simple chair")
    with patch.object(inv, "_save_inventory") as mock_save:
        new_id = inv.add_furniture(furniture, 2)
        assert new_id in inv._inventory
        assert furniture.id == new_id
        assert inv._inventory[new_id][1] == 2
        mock_save.assert_called_once()


def test_add_furniture_existing_item() -> None:
    """Test adding identical furniture to inventory updates quantity."""
    inv = Inventory()
    chair1 = Chair(price=100.0, material="wood", description="Same chair")
    chair2 = Chair(price=100.0, material="wood", description="Same chair")

    with patch.object(inv, "_save_inventory") as mock_save:
        # Add the first chair
        first_id = inv.add_furniture(chair1, 2)
        # Add an identical chair
        second_id = inv.add_furniture(chair2, 3)

        # Both additions should share the same ID
        assert first_id == second_id
        # The quantity should be the sum of both additions
        assert inv._inventory[first_id][1] == 5
        mock_save.assert_called()


# --- Tests for remove_furniture ---


def test_remove_furniture_not_found() -> None:
    """Test removing non-existent furniture from inventory."""
    inv = Inventory()
    assert inv.remove_furniture("nonexistent") is False


def test_remove_furniture_success() -> None:
    """Test successful furniture removal from inventory."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood")
    with patch.object(inv, "_save_inventory"):
        new_id = inv.add_furniture(furniture, 3)
        result = inv.remove_furniture(new_id)
        assert result is True
        assert new_id not in inv._inventory


# --- Tests for update_quantity ---


def test_update_quantity_not_found() -> None:
    """Test updating quantity for non-existent furniture."""
    inv = Inventory()
    assert inv.update_quantity("nonexistent", 5) is False


def test_update_quantity_negative() -> None:
    """Test updating quantity with negative value."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood")
    with patch.object(inv, "_save_inventory"):
        new_id = inv.add_furniture(furniture, 3)
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            inv.update_quantity(new_id, -1)


def test_update_quantity_success() -> None:
    """Test successful quantity update for furniture."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood")
    with patch.object(inv, "_save_inventory") as mock_save:
        new_id = inv.add_furniture(furniture, 3)
        result = inv.update_quantity(new_id, 10)
        assert result is True
        assert inv._inventory[new_id][1] == 10
        mock_save.assert_called()


# --- Tests for is_available ---


@pytest.mark.parametrize(
    "existing_qty, req_qty, expected",
    [
        (5, 3, True),
        (2, 3, False),
    ],
)
def test_is_available(existing_qty: int, req_qty: int, expected: bool) -> None:
    """Test availability check with different quantities."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood")
    with patch.object(inv, "_save_inventory"):
        new_id = inv.add_furniture(furniture, existing_qty)
    assert inv.is_available(new_id, req_qty) == expected
    assert inv.is_available("nonexistent", 1) is False


# --- Tests for get_furniture and get_quantity ---


def test_get_furniture_and_quantity() -> None:
    """Test retrieving furniture and quantity from inventory."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood")
    with patch.object(inv, "_save_inventory"):
        new_id = inv.add_furniture(furniture, 4)
    assert inv.get_furniture(new_id) == furniture
    assert inv.get_quantity(new_id) == 4
    assert inv.get_furniture("nonexistent") is None
    assert inv.get_quantity("nonexistent") == 0


# --- Test for get_all_furniture ---


def test_get_all_furniture() -> None:
    """Test retrieving all furniture from inventory."""
    inv = Inventory()
    furniture1 = Chair(price=100.0, material="wood")
    furniture2 = Table(price=200.0, shape="round")
    with patch.object(inv, "_save_inventory"):
        inv.add_furniture(furniture1, 3)
        inv.add_furniture(furniture2, 2)
    all_items = inv.get_all_furniture()
    assert len(all_items) == 2
    for item in all_items:
        assert "furniture" in item and "quantity" in item


# --- Tests for search ---


def test_search_valid() -> None:
    """Test valid search operation with search strategy."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood")
    with patch.object(inv, "_save_inventory"):
        inv.add_furniture(furniture, 5)
    dummy_strategy = DummySearchStrategy()
    results = inv.search(dummy_strategy)
    assert isinstance(results, list)
    assert len(results) >= 1


def test_search_invalid_strategy() -> None:
    """Test search with invalid search strategy."""
    inv = Inventory()
    with pytest.raises(
        TypeError, match="search_strategy must be a SearchStrategy object"
    ):
        inv.search("not a strategy")


# --- Test for _save_inventory ---
def test_save_inventory() -> None:
    """Test saving inventory to storage."""
    inv = Inventory()
    furniture = Chair(price=100.0, material="wood")
    inv.add_furniture(furniture, 3)
    with patch.object(JsonFileManager, "write_json") as mock_write:
        inv._save_inventory()
        mock_write.assert_called_once()


# --- Tests for _create_furniture_from_dict ---


@pytest.mark.parametrize(
    "furniture_dict,expected_type",
    [
        (
            {
                "id": "F1",
                "name": "chair",
                "price": 100.0,
                "description": "desc",
                "attributes": {"material": "wood"},
            },
            Chair,
        ),
        (
            {
                "id": "F2",
                "name": "table",
                "price": 200.0,
                "description": "desc",
                "attributes": {"shape": "round", "size": "medium"},
            },
            Table,
        ),
        (
            {
                "id": "F3",
                "name": "sofa",
                "price": 300.0,
                "description": "desc",
                "attributes": {"seats": 3, "color": "gray"},
            },
            Sofa,
        ),
        (
            {
                "id": "F4",
                "name": "bed",
                "price": 400.0,
                "description": "desc",
                "attributes": {"size": "queen"},
            },
            Bed,
        ),
        (
            {
                "id": "F5",
                "name": "bookcase",
                "price": 150.0,
                "description": "desc",
                "attributes": {"shelves": 3, "size": "medium"},
            },
            Bookcase,
        ),
    ],
)
def test_create_furniture_from_dict_valid(
    furniture_dict: Dict[str, Any], expected_type: type
) -> None:
    """Test creating different furniture types from dictionary."""
    inv = Inventory()
    furniture = inv._create_furniture_from_dict(furniture_dict)
    assert isinstance(furniture, expected_type)
    assert furniture.id == furniture_dict["id"]
    assert furniture.name == furniture_dict["name"].lower()
    assert furniture.price == furniture_dict["price"]
    assert furniture.description == furniture_dict["description"]


def test_create_furniture_from_dict_missing_name() -> None:
    """Test error handling when furniture dict is missing name."""
    inv = Inventory()
    furniture_dict = {
        "price": 100.0,
        "description": "desc",
        "attributes": {"material": "wood"},
    }
    with pytest.raises(ValueError, match="Furniture dictionary must contain 'name'"):
        inv._create_furniture_from_dict(furniture_dict)


def test_create_furniture_from_dict_missing_price() -> None:
    """Test error handling when furniture dict is missing price."""
    inv = Inventory()
    furniture_dict = {
        "name": "chair",
        "description": "desc",
        "attributes": {"material": "wood"},
    }
    with pytest.raises(ValueError, match="Furniture dictionary must contain 'price'"):
        inv._create_furniture_from_dict(furniture_dict)


def test_create_furniture_from_dict_invalid_chair_missing_material() -> None:
    """Test error when chair is missing required material attribute."""
    inv = Inventory()
    furniture_dict = {
        "name": "chair",
        "price": 100.0,
        "description": "desc",
        "attributes": {},
    }
    with pytest.raises(ValueError, match="Chair must have a 'material' attribute"):
        inv._create_furniture_from_dict(furniture_dict)


def test_create_furniture_from_dict_table_missing_shape() -> None:
    """Test error when table is missing required shape attribute."""
    inv = Inventory()
    furniture_dict = {
        "id": "F6",
        "name": "table",
        "price": 200.0,
        "description": "desc",
        "attributes": {"size": "medium"},  # missing "shape"
    }
    with pytest.raises(ValueError, match="Table must have a 'shape' attribute"):
        inv._create_furniture_from_dict(furniture_dict)


def test_create_furniture_from_dict_bed_missing_size() -> None:
    """Test error when bed is missing required size attribute."""
    inv = Inventory()
    furniture_dict = {
        "id": "F7",
        "name": "bed",
        "price": 400.0,
        "description": "desc",
        "attributes": {},  # missing "size"
    }
    with pytest.raises(ValueError, match="Bed must have a 'size' attribute"):
        inv._create_furniture_from_dict(furniture_dict)


def test_create_furniture_from_dict_bookcase_missing_shelves() -> None:
    """Test error when bookcase is missing required shelves attribute."""
    inv = Inventory()
    furniture_dict = {
        "id": "F8",
        "name": "bookcase",
        "price": 150.0,
        "description": "desc",
        "attributes": {"size": "medium"},  # missing "shelves"
    }
    with pytest.raises(ValueError, match="Bookcase must have a 'shelves' attribute"):
        inv._create_furniture_from_dict(furniture_dict)


def test_create_furniture_from_dict_unsupported() -> None:
    """Test error handling for unsupported furniture type."""
    inv = Inventory()
    furniture_dict = {
        "id": "F9",
        "name": "unsupported_type",
        "price": 100.0,
        "description": "desc",
        "attributes": {},
    }
    with pytest.raises(
        ValueError, match="Unsupported furniture type: unsupported_type"
    ):
        inv._create_furniture_from_dict(furniture_dict)
