from typing import Optional

from app.models.inventory import Inventory
from app.models.search_strategy import AttributeSearchStrategy
from app.models.shopping_cart import ShoppingCart


class CartItemLocator:
    """
    Locates and adds furniture to cart based on furniture type
    and attributes, without requiring users to know IDs or prices.
    """

    # Map of furniture types to class names
    _CLASS_MAP = {
        "chair": "Chair",
        "table": "Table",
        "sofa": "Sofa",
        "bed": "Bed",
        "bookcase": "Bookcase",
    }

    def __init__(self, inventory: Optional[Inventory] = None):
        self._inventory = inventory or Inventory()

    def find_and_add_to_cart(
        self, cart: ShoppingCart, furniture_type: str, quantity: int = 1, **attributes
    ) -> bool:
        """
        Find furniture matching the type and attributes and add it to the cart.

        Args:
            cart: ShoppingCart to add the item to
            furniture_type: Type of furniture (e.g., "chair", "table")
            quantity: Quantity to add
            **attributes: Specific attributes for the furniture type
                         (e.g., color="black", material="wood")

        Returns:
            bool: True if item was found and added

        Raises:
            ValueError: If no items match or not enough in inventory
        """
        # Get the corresponding class name
        furniture_class = self._CLASS_MAP.get(furniture_type.lower())
        if not furniture_class:
            raise ValueError(f"Unknown furniture type: {furniture_type}")

        # First, find all furniture of the specified type
        matching_items = []

        # For each attribute, perform a search with the furniture_type parameter
        for attr_name, attr_value in attributes.items():
            # Convert enum values to their string representation if needed
            if hasattr(attr_value, "value"):
                attr_value = attr_value.value

            # Create search strategy for this attribute, including furniture_type filter
            attr_search = AttributeSearchStrategy(
                attr_name, attr_value, furniture_class
            )
            attr_results = self._inventory.search(attr_search)

            if not attr_results:
                raise ValueError(
                    f"No {furniture_type} found with {attr_name}={attr_value}"
                )

            # For the first attribute, initialize matching_items
            if not matching_items:
                matching_items = attr_results
                continue

            # For subsequent attributes, find the intersection
            new_matches = []
            matching_ids = {item["furniture"].id for item in matching_items}

            for item in attr_results:
                if item["furniture"].id in matching_ids:
                    new_matches.append(item)

            matching_items = new_matches

            if not matching_items:
                raise ValueError(
                    f"No {furniture_type} found with the "
                    f"specified combination of attributes"
                )

        # If no attributes were specified, search by furniture type only
        if not attributes:
            # Create a search for furniture class name
            type_search = AttributeSearchStrategy("__class__.__name__", furniture_class)
            matching_items = self._inventory.search(type_search)

            if not matching_items:
                raise ValueError(f"No {furniture_type} found in inventory")

        # Find an item with sufficient quantity
        available_item = None
        for item in matching_items:
            if item["quantity"] >= quantity:
                available_item = item
                break

        if not available_item:
            raise ValueError(
                f"Not enough {furniture_type} in stock with the specified attributes"
            )

        # Add to cart
        cart.add_item(available_item["furniture"], quantity)
        return True
