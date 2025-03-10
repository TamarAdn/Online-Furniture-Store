from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SearchStrategy(ABC):
    """
    Abstract base class for search strategies.

    Defines the interface for all search strategies.
    """

    @abstractmethod
    def search(self, items: Dict[str, List]) -> List[Dict[str, Any]]:
        """
        Search the inventory using the strategy.

        Args:
            items: Dictionary of inventory items where each key is the furniture ID
                  and each value is a list containing [Furniture, quantity]

        Returns:
            List of dictionaries containing furniture and quantity
        """


class NameSearchStrategy(SearchStrategy):
    """Search strategy for finding furniture by name."""

    def __init__(self, search_term: str):
        """
        Initialize with the name search term.

        Args:
            search_term: Name or partial name to search for (case insensitive)
        """
        self.search_term = search_term.lower()

    def search(self, items: Dict[str, List]) -> List[Dict[str, Any]]:
        """
        Search for furniture by name.

        Args:
            items: Dictionary of inventory items

        Returns:
            List of dictionaries containing furniture and quantity
        """
        results = []
        for _, item_data in items.items():
            furniture, quantity = item_data
            if self.search_term in furniture.name.lower():
                results.append({"furniture": furniture, "quantity": quantity})
        return results


class PriceRangeSearchStrategy(SearchStrategy):
    """Search strategy for finding furniture by price range."""

    def __init__(self, min_price: float = 0, max_price: float = float("inf")):
        """
        Initialize with price range parameters.

        Args:
            min_price: Minimum price (inclusive, default: 0)
            max_price: Maximum price (inclusive, default: infinite)
        """
        self.min_price = min_price
        self.max_price = max_price

    def search(self, items: Dict[str, List]) -> List[Dict[str, Any]]:
        """
        Search for furniture by price range.

        Args:
            items: Dictionary of inventory items

        Returns:
            List of dictionaries containing furniture and quantity
        """
        results = []
        for _, item_data in items.items():
            furniture, quantity = item_data
            if self.min_price <= furniture.price <= self.max_price:
                results.append({"furniture": furniture, "quantity": quantity})
        return results


class AttributeSearchStrategy(SearchStrategy):
    """Search strategy for finding furniture by attribute value."""

    def __init__(
        self, attribute_name: str, attribute_value: Any, furniture_type: str = None
    ):
        """
        Initialize with attribute parameters.

        Args:
            attribute_name: Name of the attribute to search for
            attribute_value: Value of the attribute to match
            furniture_type: Optional class name of furniture to filter by
        """

        self.attribute_name = attribute_name
        self.attribute_value = attribute_value
        self.furniture_type = furniture_type

        if isinstance(self.attribute_value, str):
            self.attribute_value = self.attribute_value.lower()

    def search(self, items: Dict[str, List]) -> List[Dict[str, Any]]:
        """
        Search for furniture by attribute value.

        Args:
            items: Dictionary of inventory items

        Returns:
            List of dictionaries containing furniture and quantity
        """
        results = []

        for _, item_data in items.items():
            furniture, quantity = item_data

            # If furniture_type is specified, check if it matches
            if (
                self.furniture_type
                and furniture.__class__.__name__ != self.furniture_type
            ):
                continue

            # Try to get the attribute from the furniture item
            try:
                attr_value = getattr(furniture, self.attribute_name)

                # Convert attribute value to lowercase if it's a string
                if isinstance(attr_value, str):
                    attr_value = attr_value.lower()

                # Add to results if attribute value matches
                if attr_value == self.attribute_value:
                    results.append({"furniture": furniture, "quantity": quantity})
            except AttributeError:
                # Skip if the attribute doesn't exist
                continue

        return results
