from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.config import TAX_RATE
from app.models.discount_strategy import DiscountStrategy, NoDiscountStrategy
from app.models.enums import (
    BedSize,
    ChairMaterial,
    FurnitureSize,
    SofaColor,
    TableShape,
)


class Furniture(ABC):
    """
    Abstract base class for all furniture items.

    Provides common properties and methods for all furniture types,
    implements the Strategy pattern for discount application.
    """

    def __init__(self, name: str, price: float, **kwargs):
        """
        Initialize a new furniture item.

        Args:
            name: Type of furniture (e.g., "chair", "table")
            price: Base price of the furniture
            **kwargs: Optional parameters:
                - description: Optional detailed description
                - furniture_id: Optional ID (usually handled by Inventory)

        Raises:
            TypeError: If price is not a number
            ValueError: If price is negative or if description exceeds maximum length
        """
        # Validate price is a number
        if not isinstance(price, (float, int)):
            raise TypeError("Price must be a number")

        if price < 0:
            raise ValueError("Price cannot be negative")

        # Optional maximum price constraint to prevent unreasonable values
        if price > 1000000:
            raise ValueError("Price exceeds maximum allowed value of 1,000,000")

        # Validate name is a string
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        self._id = kwargs.get("furniture_id", None)
        self._name = name.lower()
        self._price = float(price)  # Ensure price is stored as float
        self._description = kwargs.get("description", "")

        # Validate description if provided
        if not isinstance(self._description, str):
            raise TypeError("Description must be a string")

        # Limit description length
        if len(self._description) > 1000:
            raise ValueError("Description exceeds maximum length of 1000 characters")

        # Validate ID format if provided
        if self._id is not None and not isinstance(self._id, str):
            raise TypeError("Furniture ID must be a string")

        self._discount_strategy: DiscountStrategy = NoDiscountStrategy()  # Default

    @property
    def id(self) -> Optional[str]:
        """Get the furniture's unique identifier, may be None if not set."""
        return self._id

    @property
    def name(self) -> str:
        """Get the furniture's type as a string."""
        return self._name

    @property
    def price(self) -> float:
        """Get the furniture's base price."""
        return self._price

    @property
    def description(self) -> str:
        """Get the furniture's description."""
        return self._description

    @property
    def discount_strategy(self) -> DiscountStrategy:
        """Get the current discount strategy."""
        return self._discount_strategy

    @discount_strategy.setter
    def discount_strategy(self, strategy: DiscountStrategy) -> None:
        """
        Set the discount strategy to be applied to this furniture.

        Args:
            strategy: The discount strategy to apply

        Raises:
            TypeError: If strategy is not a DiscountStrategy object
        """
        if not isinstance(strategy, DiscountStrategy):
            raise TypeError("Strategy must be a DiscountStrategy object")

        self._discount_strategy = strategy

    def get_discounted_price(self) -> float:
        """Calculate the price after applying any discount but before tax."""
        return self._discount_strategy.apply_discount(self._price)

    def get_final_price(self) -> float:
        """Calculate the final price after applying both discount and tax."""
        return self.get_discounted_price() * (1 + TAX_RATE)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert furniture object to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the furniture item
        """
        return {
            "id": self._id,
            "name": self._name,
            "price": self._price,
            "description": self._description,
            "attributes": self.get_specific_attributes(),
        }

    def is_identical_to(self, other: "Furniture") -> bool:
        """
        Check if this furniture item is identical to another.
        Two furniture items are considered identical if they are the same type
        and have the same core attributes, regardless of their ID.

        Args:
            other: The furniture item to compare with

        Returns:
            bool: True if furniture items are identical, False otherwise
        """
        # Must be same subclass type
        if type(self) is not type(other):
            return False

        # Check base Furniture attributes (shared by all)
        if (
            self.name != other.name
            or self.price != other.price
            or self.description != other.description
        ):
            return False

        # Check subclass-specific attributes by comparing the dictionaries
        # This leverages the existing get_specific_attributes method
        return self.get_specific_attributes() == other.get_specific_attributes()

    @abstractmethod
    def get_specific_attributes(self) -> Dict[str, Any]:
        """
        Get type-specific attributes for serialization.

        Must be implemented by concrete subclasses.

        Returns:
            Dictionary of attributes specific to the furniture type
        """


class Chair(Furniture):
    """
    Chair furniture type.

    Chairs have a material attribute in addition to
    the standard furniture properties.
    """

    def __init__(self, price: float, material: str, **kwargs):
        """
        Initialize a chair.

        Args:
            price: Base price of the chair
            material: Material the chair is made from (wood, plastic, leather, fabric)
            **kwargs: Optional parameters:
                - description: Optional detailed description
                - furniture_id: Optional ID (usually handled by Inventory)

        Raises:
            ValueError: If material is not a valid chair material
        """
        super().__init__(name="chair", price=price, **kwargs)

        # Validate that the material is a known chair material
        # Enum validation will handle type checking implicitly
        material = material.lower() if isinstance(material, str) else material
        try:
            self._material = ChairMaterial(material).value
        except ValueError:
            valid_materials = [m.value for m in ChairMaterial]
            raise ValueError(
                f"Invalid chair material. Valid materials are:\
                  {', '.join(valid_materials)}"
            )

    @property
    def material(self) -> str:
        """Get the chair's material."""
        return self._material

    def get_specific_attributes(self) -> Dict[str, Any]:
        """
        Get chair-specific attributes for serialization.

        Returns:
            Dictionary containing the material attribute
        """
        return {"material": self._material}


class Table(Furniture):
    """
    Table furniture type.

    Tables have shape and size attributes.
    """

    def __init__(self, price: float, shape: str, size: str = "medium", **kwargs):
        """
        Initialize a table.

        Args:
            price: Base price of the table
            shape: Shape of the table (round, square, oval)
            size: Size of the table (small, medium, large)
            **kwargs: Optional parameters:
                - description: Optional detailed description
                - furniture_id: Optional ID (usually handled by Inventory)

        Raises:
            ValueError: If shape or size is not valid
        """
        super().__init__(name="table", price=price, **kwargs)

        # Validate shape
        # Enum validation will handle type checking implicitly
        shape = shape.lower() if isinstance(shape, str) else shape
        try:
            self._shape = TableShape(shape).value
        except ValueError:
            valid_shapes = [s.value for s in TableShape]
            raise ValueError(
                f"Invalid table shape. Valid shapes are: {', '.join(valid_shapes)}"
            )

        # Validate size
        size = size.lower() if isinstance(size, str) else size
        try:
            self._size = FurnitureSize(size).value
        except ValueError:
            valid_sizes = [s.value for s in FurnitureSize]
            raise ValueError(
                f"Invalid table size. Valid sizes are: {', '.join(valid_sizes)}"
            )

    @property
    def shape(self) -> str:
        """Get the table's shape."""
        return self._shape

    @property
    def size(self) -> str:
        """Get the table's size."""
        return self._size

    def get_specific_attributes(self) -> Dict[str, Any]:
        """
        Get table-specific attributes for serialization.

        Returns:
            Dictionary containing the shape and size attributes
        """
        return {"shape": self._shape, "size": self._size}


class Sofa(Furniture):
    """
    Sofa furniture type.

    Sofas have seats and color attributes.
    """

    def __init__(
        self,
        price: float,
        seats: int = 3,  # default value 3
        color: str = "gray",  # default color - gray
        **kwargs,
    ):
        """
        Initialize a sofa.

        Args:
            price: Base price of the sofa
            seats: Number of people who can sit on the sofa (2-5)
            color: Color of the sofa (gray, black, beige, white)
            **kwargs: Optional parameters:
                - description: Optional detailed description
                - furniture_id: Optional ID (usually handled by Inventory)

        Raises:
            TypeError: If seats is not an int
            ValueError: If seats is not within the valid range or color is invalid
        """
        super().__init__(name="sofa", price=price, **kwargs)

        # Validate seats - this needs explicit type checking since it's not an enum
        if not isinstance(seats, int):
            raise TypeError("Seats must be an integer")

        if seats < 2 or seats > 5:
            raise ValueError("Sofa seats must be between 2 and 5")
        self._seats = seats

        # Validate color
        # Enum validation will handle type checking implicitly
        color = color.lower() if isinstance(color, str) else color
        try:
            self._color = SofaColor(color).value
        except ValueError:
            valid_colors = [c.value for c in SofaColor]
            raise ValueError(
                f"Invalid sofa color. Valid colors are: {', '.join(valid_colors)}"
            )

    @property
    def seats(self) -> int:
        """Get the number of seats on the sofa."""
        return self._seats

    @property
    def color(self) -> str:
        """Get the sofa's color."""
        return self._color

    def get_specific_attributes(self) -> Dict[str, Any]:
        """
        Get sofa-specific attributes for serialization.

        Returns:
            Dictionary containing the seats and color attributes
        """
        return {"seats": self._seats, "color": self._color}


class Bed(Furniture):
    """
    Bed furniture type.

    Beds have a size attribute instead of dimensions.
    """

    def __init__(self, price: float, size: str, **kwargs):
        """
        Initialize a bed.

        Args:
            price: Base price of the bed
            size: Bed size (single, twin, queen, king)
            **kwargs: Optional parameters:
                - description: Optional detailed description
                - furniture_id: Optional ID (usually handled by Inventory)

        Raises:
            ValueError: If size is not a valid bed size
        """
        super().__init__(name="bed", price=price, **kwargs)

        # Validate that the size is a known bed size
        # Enum validation will handle type checking implicitly
        size = size.lower() if isinstance(size, str) else size
        try:
            self._size = BedSize(size).value
        except ValueError:
            valid_sizes = [s.value for s in BedSize]
            raise ValueError(
                f"Invalid bed size. Valid sizes are: {', '.join(valid_sizes)}"
            )

    @property
    def size(self) -> str:
        """Get the bed's size."""
        return self._size

    def get_specific_attributes(self) -> Dict[str, Any]:
        """
        Get bed-specific attributes for serialization.

        Returns:
            Dictionary containing the size attribute
        """
        return {"size": self._size}


class Bookcase(Furniture):
    """
    Bookcase furniture type.

    Bookcases have shelves count and size attributes.
    """

    def __init__(self, price: float, shelves: int, size: str = "medium", **kwargs):
        """
        Initialize a bookcase.

        Args:
            price: Base price of the bookcase
            shelves: Number of shelves in the bookcase (1-10)
            size: Size of the bookcase (small, medium, large)
            **kwargs: Optional parameters:
                - description: Optional detailed description
                - furniture_id: Optional ID (usually handled by Inventory)

        Raises:
            TypeError: If shelves is not an int
            ValueError: If shelves is not within the valid range or size is invalid
        """
        super().__init__(name="bookcase", price=price, **kwargs)

        # Validate shelves - this needs explicit type checking since it's not an enum
        if not isinstance(shelves, int):
            raise TypeError("Shelves must be an integer")

        if shelves < 1 or shelves > 10:
            raise ValueError("Bookcase shelves must be between 1 and 10")
        self._shelves = shelves

        # Validate size
        # Enum validation will handle type checking implicitly
        size = size.lower() if isinstance(size, str) else size
        try:
            self._size = FurnitureSize(size).value
        except ValueError:
            valid_sizes = [s.value for s in FurnitureSize]
            raise ValueError(
                f"Invalid bookcase size. Valid sizes are: {', '.join(valid_sizes)}"
            )

    @property
    def shelves(self) -> int:
        """Get the number of shelves in the bookcase."""
        return self._shelves

    @property
    def size(self) -> str:
        """Get the bookcase's size."""
        return self._size

    def get_specific_attributes(self) -> Dict[str, Any]:
        """
        Get bookcase-specific attributes for serialization.

        Returns:
            Dictionary containing the shelves and size attributes
        """
        return {"shelves": self._shelves, "size": self._size}
