import copy
import uuid
from typing import Any, Dict, List, Optional, Union

from app.config import INVENTORY_FILE
from app.models.furniture import Bed, Bookcase, Chair, Furniture, Sofa, Table
from app.models.search_strategy import SearchStrategy
from app.utils import JsonFileManager


class Inventory:
    """
    Singleton class for managing furniture inventory.

    Handles adding, removing, and updating furniture items,
    as well as checking availability and searching for items.

    Uses a single dictionary approach where each entry contains
    both the furniture object and its quantity for data consistency.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Inventory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, file_path=INVENTORY_FILE):
        # Only initialize once
        if not self._initialized:
            self._file_path = file_path
            self._inventory: Dict[
                str, List[Furniture, int]
            ] = {}  # Each entry contains [furniture_object, quantity]
            JsonFileManager.ensure_file_exists(file_path)
            self._load_inventory()
            self._initialized = True

    def _generate_id(self) -> str:
        """
        Generate a unique ID for a furniture item using UUID.

        This ensures uniqueness even if items are added and removed frequently.

        Returns:
            str: A unique ID for the furniture item (UUID)
        """
        return str(uuid.uuid4())

    def _load_inventory(self) -> None:
        """
        Load inventory from JSON file.
        """
        inventory_data = JsonFileManager.read_json(self._file_path)

        for item_data in inventory_data:
            try:
                furniture = self._create_furniture_from_dict(item_data["furniture"])
                quantity = item_data["quantity"]

                # Store both furniture and quantity together
                self._inventory[furniture.id] = [furniture, quantity]
            except (ValueError, KeyError) as e:
                # Log error but continue loading other items
                print(f"Error loading inventory item: {e}")

    def add_furniture(self, furniture: Furniture, quantity: int = 1) -> str:
        """
        Add furniture to inventory. If identical furniture already exists, 
        quantity is added to the existing item.
        
        Args:
            furniture: The furniture item to add
            quantity: The quantity to add (default: 1)
        
        Returns:
            str: The furniture ID (either existing or newly generated)
            
        Raises:
            TypeError: If item is not a Furniture object
            ValueError: If quantity is not positive
        """
        if not isinstance(furniture, Furniture):
            raise TypeError("Item must be a Furniture object")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        # Check if identical furniture already exists
        for furniture_id, [existing_furniture, existing_quantity] in self._inventory.items():
            if furniture.is_identical_to(existing_furniture):
                # Update quantity of existing furniture
                self._inventory[furniture_id][1] += quantity
                self._save_inventory()
                return furniture_id
        
        # If no identical furniture exists, create a new entry
        new_id = self._generate_id()
        furniture._id = new_id
        self._inventory[new_id] = [furniture, quantity]
        self._save_inventory()
        return new_id

    def remove_furniture(self, furniture_id: str) -> bool:
        """
        Remove furniture from inventory completely.

        Args:
            furniture_id: ID of the furniture to remove

        Returns:
            bool: True if successful, False if item not found
        """
        if furniture_id not in self._inventory:
            return False

        # Remove the item completely
        del self._inventory[furniture_id]

        self._save_inventory()
        return True

    def update_quantity(self, furniture_id: str, quantity: int) -> bool:
        """
        Update the quantity of a furniture item.

        Args:
            furniture_id: ID of the furniture to update
            quantity: The new quantity (can be zero for out-of-stock items)

        Returns:
            bool: True if successful, False if item not found
        """
        if furniture_id not in self._inventory:
            return False

        # Only block negative quantities, allow zero for out-of-stock items
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        # Update the quantity
        self._inventory[furniture_id][1] = quantity
        self._save_inventory()
        return True

    def is_available(self, furniture_id: str, quantity: int = 1) -> bool:
        """
        Check if a furniture item is available in the requested quantity.

        Args:
            furniture_id: ID of the furniture to check
            quantity: The quantity to check for (default: 1)

        Returns:
            bool: True if available, False otherwise
        """
        if furniture_id not in self._inventory:
            return False

        return self._inventory[furniture_id][1] >= quantity

    def get_furniture(self, furniture_id: str) -> Optional[Furniture]:
        """
        Get a furniture item by ID.

        Args:
            furniture_id: ID of the furniture to get

        Returns:
            Furniture or None: The furniture item, or None if not found
        """
        return self._inventory.get(furniture_id, [None, 0])[0]

    def get_quantity(self, furniture_id: str) -> int:
        """
        Get the quantity of a furniture item.

        Args:
            furniture_id: ID of the furniture to check

        Returns:
            int: The quantity available, or 0 if not found
        """
        return self._inventory.get(furniture_id, [None, 0])[1]

    def get_all_furniture(self) -> List[Dict[str, Union[Furniture, int]]]:
        """
        Get all furniture items in inventory.

        Returns:
            List[Dict]: List of dictionaries containing furniture and quantity
        """
        return [
            {
                "furniture": self._inventory[item_id][0],
                "quantity": self._inventory[item_id][1],
            }
            for item_id in self._inventory
        ]

    def search(self, search_strategy: SearchStrategy) -> List[Dict[str, Any]]:
        """
        Search inventory using the provided search strategy.

        This method follows the Strategy design pattern, allowing different
        search algorithms to be used interchangeably.

        Args:
            search_strategy: The search strategy to use

        Returns:
            List[Dict]: List of dictionaries containing furniture and quantity

        Raises:
            TypeError: If search_strategy is not a SearchStrategy object
        """
        if not isinstance(search_strategy, SearchStrategy):
            raise TypeError("search_strategy must be a SearchStrategy object")

        # Create a deep copy of the inventory dictionary
        inventory_copy = {
            item_id: [copy.deepcopy(item_data[0]), item_data[1]]
            for item_id, item_data in self._inventory.items()
        }

        # Execute the search using the provided strategy with a fully protected copy
        return search_strategy.search(inventory_copy)

    def _save_inventory(self) -> None:
        """
        Save the current inventory state to the JSON file.

        Converts furniture objects and quantities to a serializable format.
        """
        # Convert inventory to serializable format
        inventory_data = []
        for item_id, (furniture, quantity) in self._inventory.items():
            # Convert the furniture object to a dictionary
            furniture_dict = furniture.to_dict()

            # Create the serializable structure
            item_data = {"furniture": furniture_dict, "quantity": quantity}

            inventory_data.append(item_data)

        # Save to file
        JsonFileManager.write_json(self._file_path, inventory_data)

    def _create_furniture_from_dict(self, furniture_dict: Dict[str, Any]) -> Furniture:
        """
        Create a furniture object from a dictionary.

        Args:
            furniture_dict: Dictionary containing furniture data

        Returns:
            Furniture object of the appropriate type

        Raises:
            ValueError: If the furniture type is not supported/ attributes are missing
        """
        # Validate required fields
        if "name" not in furniture_dict:
            raise ValueError("Furniture dictionary must contain 'name'")
        if "price" not in furniture_dict:
            raise ValueError("Furniture dictionary must contain 'price'")

        furniture_type = furniture_dict["name"].lower()
        price = furniture_dict["price"]
        furniture_id = furniture_dict.get("id")
        description = furniture_dict.get("description", "")
        attributes = furniture_dict.get("attributes", {})

        # Common kwargs for all furniture types
        kwargs = {
            "description": description,
            "furniture_id": furniture_id,  # Pass the ID if it exists
        }

        # Create the appropriate furniture type based on the name
        if furniture_type == "chair":
            if "material" not in attributes:
                raise ValueError("Chair must have a 'material' attribute")

            return Chair(price=price, material=attributes["material"], **kwargs)

        elif furniture_type == "table":
            if "shape" not in attributes:
                raise ValueError("Table must have a 'shape' attribute")

            return Table(
                price=price,
                shape=attributes["shape"],
                size=attributes.get("size", "medium"),
                **kwargs,
            )

        elif furniture_type == "sofa":
            return Sofa(
                price=price,
                seats=attributes.get("seats", 3),
                color=attributes.get("color", "gray"),
                **kwargs,
            )

        elif furniture_type == "bed":
            if "size" not in attributes:
                raise ValueError("Bed must have a 'size' attribute")

            return Bed(price=price, size=attributes["size"], **kwargs)

        elif furniture_type == "bookcase":
            if "shelves" not in attributes:
                raise ValueError("Bookcase must have a 'shelves' attribute")

            return Bookcase(
                price=price,
                shelves=attributes["shelves"],
                size=attributes.get("size", "medium"),
                **kwargs,
            )

        else:
            raise ValueError(f"Unsupported furniture type: {furniture_type}")