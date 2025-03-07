from typing import Dict, List, Optional, Union

from app.models.discount_strategy import DiscountStrategy, NoDiscountStrategy
from app.models.furniture import Furniture
from app.models.inventory import Inventory


class ShoppingCart:
    """
    Manages a collection of furniture items for purchase.

    This class handles adding, removing, and updating items in a user's shopping cart,
    along with calculating subtotals and totals with optional discount strategies.
    It also ensures that the requested quantities are available in inventory.
    """

    def __init__(self, inventory: Optional[Inventory] = None) -> None:
        """
        Initialize an empty shopping cart.

        The cart stores items as a dictionary where keys are furniture IDs
        and values are lists containing the furniture object and quantity.

        Args:
            inventory: Optional Inventory instance for availability checks.
                       If None, a new instance will be created when needed.
        """
        # Dictionary with furniture_id as key and [furniture, quantity] as value
        self._items: Dict[str, List[Union[Furniture, int]]] = {}
        self._discount_strategy: DiscountStrategy = NoDiscountStrategy()
        self._inventory = inventory

    @property
    def discount_strategy(self) -> DiscountStrategy:
        """
        Get the current discount strategy.

        Returns:
            DiscountStrategy: The current discount strategy (never None)
        """
        return self._discount_strategy

    @discount_strategy.setter
    def discount_strategy(self, strategy: Optional[DiscountStrategy]) -> None:
        """
        Set the discount strategy to apply to the cart total.

        If None is provided, reverts to NoDiscountStrategy.

        Args:
            strategy: The discount strategy to apply
        """
        self._discount_strategy = (
            strategy if strategy is not None else NoDiscountStrategy()
        )

    def add_item(self, furniture: Furniture, quantity: int = 1) -> None:
        """
        Add a furniture item to the cart.

        Adds the specified quantity of the furniture item to the cart,
        checking inventory availability first. If the item already exists
        in the cart, the quantity is updated.

        Args:
            furniture: The furniture item to add
            quantity: The quantity to add (default: 1)

        Raises:
            TypeError: If the item is not a Furniture object
            ValueError: If quantity is not positive or not enough items are in inventory
        """
        if not isinstance(furniture, Furniture):
            raise TypeError("Item must be a Furniture object")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Get current quantity in cart
        current_quantity = self._items.get(furniture.id, [None, 0])[1]

        # Calculate new quantity
        total_quantity_needed = current_quantity + quantity

        # Check inventory availability
        inventory = self._get_inventory()
        if not inventory.is_available(furniture.id, total_quantity_needed):
            raise ValueError(f"Not enough {furniture.name} in inventory")

        # Update cart
        if furniture.id in self._items:
            self._items[furniture.id][1] = total_quantity_needed  # Update quantity
        else:
            self._items[furniture.id] = [furniture, quantity]  # Add new item

    def _get_inventory(self) -> Inventory:
        """
        Get the inventory instance, creating one if needed.

        Returns:
            Inventory: The inventory instance
        """
        if self._inventory is None:
            self._inventory = Inventory()
        return self._inventory

    def remove_item(self, furniture_id: str, quantity: Optional[int] = None) -> bool:
        """
        Remove a furniture item from the cart.

        If quantity is not specified, removes the item completely.
        Otherwise, reduces the quantity by the specified amount.

        Args:
            furniture_id: ID of the furniture item to remove
            quantity: Quantity to remove (default: None, removes all)

        Returns:
            bool: True if removal was successful, False if item was not in cart
        """
        if furniture_id not in self._items:
            return False

        if quantity is not None and quantity < 0:
            raise ValueError("Quantity to remove must be non-negative")

        if quantity is None or quantity >= self._items[furniture_id][1]:
            del self._items[furniture_id]
        else:
            self._items[furniture_id][1] -= quantity

        return True

    def get_items(self) -> List[List[Union[Furniture, int]]]:
        """
        Get all items in the cart.

        Returns a defensive copy to prevent modification of internal state.

        Returns:
            List[List[Union[Furniture, int]]]: A list of [furniture, quantity] lists
        """
        return [item[:] for item in self._items.values()]  # Return copies of the lists

    def get_subtotal(self) -> float:
        """
        Calculate the subtotal of all items in the cart.

        The subtotal is the sum of each item's final price multiplied by its quantity.

        Returns:
            float: The cart subtotal
        """
        return sum(item[0].get_final_price() * item[1] for item in self._items.values())

    def get_total(self) -> float:
        """
        Calculate the total price of the cart after applying any discount.

        The discount strategy is always applied (defaults to no discount).

        Returns:
            float: The cart total after discounts
        """
        subtotal = self.get_subtotal()
        return self._discount_strategy.apply_discount(subtotal)

    def clear(self) -> None:
        """
        Clear all items from the cart.
        """
        self._items = {}

    def is_empty(self) -> bool:
        """
        Check if the cart is empty.

        Returns:
            bool: True if the cart is empty, False otherwise
        """
        return not self._items

    def __len__(self) -> int:
        """
        Get the total number of items in the cart.

        Returns:
            int: The sum of quantities of all items
        """
        return sum(item[1] for item in self._items.values())
