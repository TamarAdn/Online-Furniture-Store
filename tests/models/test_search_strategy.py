from typing import Any, Dict, List

import pytest

from app.models.search_strategy import (
    AttributeSearchStrategy,
    NameSearchStrategy,
    PriceRangeSearchStrategy,
    SearchStrategy,
)


# Define a dummy furniture class with minimal interface for testing.
class DummyFurniture:
    """A minimal furniture class for testing search strategies."""

    def __init__(self, fid: str, name: str, price: float = 0, **attributes) -> None:
        """Initialize dummy furniture.

        Args:
            fid: Furniture ID
            name: Furniture name
            price: Furniture price
            **attributes: Additional attributes to assign to the furniture
        """
        self.id = fid
        self.name = name
        self.price = price
        # Dynamically add any extra attributes.
        for key, value in attributes.items():
            setattr(self, key, value)


# Fixture to create a dummy inventory dictionary.
# Inventory is a dict mapping an id to a list: [furniture, quantity].
@pytest.fixture
def dummy_items() -> Dict[str, List[Any]]:
    """Create fixture of dummy furniture items for testing search strategies.

    Returns:
        A dictionary mapping furniture IDs to lists containing a furniture
        object and its quantity.
    """
    return {
        "1": [DummyFurniture("1", "Chair", price=100, color="black", seats=2), 5],
        "2": [DummyFurniture("2", "Table", price=200, shape="round"), 3],
        "3": [DummyFurniture("3", "Sofa", price=300, color="grey", seats=3), 2],
        "4": [DummyFurniture("4", "Lamp", price=50), 10],  # No "color" attribute.
    }


# -----------------------------
# Tests for NameSearchStrategy
# -----------------------------
@pytest.mark.parametrize(
    "search_term, expected_ids",
    [
        ("chair", ["1"]),
        ("table", ["2"]),
        ("sofa", ["3"]),
        ("lamp", ["4"]),
        ("nonexistent", []),
        ("CHAIR", ["1"]),  # case-insensitive check
        ("ir", ["1"]),  # substring match: "ir" is in "chair"
    ],
)
def test_name_search_strategy(
    search_term: str, expected_ids: List[str], dummy_items: Dict[str, List[Any]]
) -> None:
    """Test the NameSearchStrategy with various search terms."""
    strategy = NameSearchStrategy(search_term)
    results = strategy.search(dummy_items)
    result_ids = [item["furniture"].id for item in results]
    assert sorted(result_ids) == sorted(expected_ids)


# -------------------------------
# Tests for PriceRangeSearchStrategy
# -------------------------------
@pytest.mark.parametrize(
    "min_price, max_price, expected_ids",
    [
        (0, 150, ["1", "4"]),  # Chair (100) and Lamp (50)
        (150, 250, ["2"]),  # Table (200)
        (0, 1000, ["1", "2", "3", "4"]),  # All items
        (300, 300, ["3"]),  # Sofa (300)
        (400, 500, []),  # No item in this range
    ],
)
def test_price_range_search_strategy(
    min_price: float,
    max_price: float,
    expected_ids: List[str],
    dummy_items: Dict[str, List[Any]],
) -> None:
    """Test the PriceRangeSearchStrategy with various price ranges."""
    strategy = PriceRangeSearchStrategy(min_price, max_price)
    results = strategy.search(dummy_items)
    result_ids = [item["furniture"].id for item in results]
    assert sorted(result_ids) == sorted(expected_ids)


# ---------------------------------
# Tests for AttributeSearchStrategy
# ---------------------------------
@pytest.mark.parametrize(
    "attribute_name, attribute_value, furniture_type, expected_ids",
    [
        # Search by attribute "color" without furniture type filter.
        ("color", "black", None, ["1"]),
        ("color", "BLACK", None, ["1"]),  # Case-insensitive match.
        # Numeric attribute: "seats" equals 2.
        ("seats", 2, None, ["1"]),
        ("seats", 2, "DummyFurniture", ["1"]),  # With furniture type filter.
        ("seats", 3, "DummyFurniture", ["3"]),  # Should return Sofa.
        # Search by another attribute.
        ("shape", "round", None, ["2"]),
        # When the attribute does not exist, expect empty list.
        ("nonexistent_attr", "value", None, []),
    ],
)
def test_attribute_search_strategy(
    attribute_name: str,
    attribute_value: Any,
    furniture_type: str,
    expected_ids: List[str],
    dummy_items: Dict[str, List[Any]],
) -> None:
    """Test the AttributeSearchStrategy with various attributes and values."""
    strategy = AttributeSearchStrategy(attribute_name, attribute_value, furniture_type)
    results = strategy.search(dummy_items)
    result_ids = [item["furniture"].id for item in results]
    assert sorted(result_ids) == sorted(expected_ids)


def test_attribute_search_strategy_wrong_furniture_type(
    dummy_items: Dict[str, List[Any]]
) -> None:
    """Test AttributeSearchStrategy with a non-matching furniture type."""
    # Even if the attribute exists, if the furniture type doesn't match,
    # expect no results.
    strategy = AttributeSearchStrategy("color", "black", "Sofa")
    results = strategy.search(dummy_items)
    assert results == []


def test_attribute_search_strategy_missing_attribute(
    dummy_items: Dict[str, List[Any]]
) -> None:
    """Test AttributeSearchStrategy with a non-existent attribute."""
    # Search for an attribute that none of the items have.
    strategy = AttributeSearchStrategy("nonexistent", "value")
    results = strategy.search(dummy_items)
    assert results == []


def test_attribute_search_strategy_numeric(dummy_items: Dict[str, List[Any]]) -> None:
    """Test AttributeSearchStrategy with a numeric attribute value."""
    # Search for a numeric attribute (seats) without case conversion.
    strategy = AttributeSearchStrategy("seats", 2)
    results = strategy.search(dummy_items)
    result_ids = [item["furniture"].id for item in results]
    assert sorted(result_ids) == ["1"]


# ------------------------------
# Test to cover abstract method body
# ------------------------------
def test_abstract_search_method_returns_none() -> None:
    """Test the abstract search method in the base SearchStrategy class."""

    class DummySearch(SearchStrategy):
        def search(self, items: Dict[str, List[Any]]) -> Any:
            return super().search(items)

    dummy = DummySearch()
    result = dummy.search({})
    assert result is None
