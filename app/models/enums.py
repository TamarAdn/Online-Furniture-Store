from enum import Enum


class PaymentMethod(Enum):
    """Payment options."""

    CREDIT_CARD = "Credit Card"
    PAYPAL = "PayPal"
    APPLE_PAY = "Apple Pay"
    GOOGLE_PAY = "Google Pay"


class ChairMaterial(Enum):
    """Standard chair materials for validation."""

    WOOD = "wood"
    PLASTIC = "plastic"
    LEATHER = "leather"
    FABRIC = "fabric"


class TableShape(Enum):
    """Standard table shapes for validation."""

    ROUND = "round"
    SQUARE = "square"
    OVAL = "oval"


class FurnitureSize(Enum):
    """Standard sizes."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class SofaColor(Enum):
    """Standard sofa colors."""

    GRAY = "gray"
    BLACK = "black"
    BEIGE = "beige"
    WHITE = "white"


class BedSize(Enum):
    """Standard bed sizes for validation."""

    SINGLE = "single"
    TWIN = "twin"
    QUEEN = "queen"
    KING = "king"
