from abc import ABC, abstractmethod
from typing import Union


class DiscountStrategy(ABC):
    """
    Abstract base class for discount strategies.

    Defines the interface for different discount calculation strategies
    following the Strategy design pattern.
    """

    @abstractmethod
    def apply_discount(self, price: float) -> float:
        """
        Apply the discount strategy to calculate a discounted price.

        Args:
            price: The original price to apply discount to

        Returns:
            float: The discounted price
        """


class NoDiscountStrategy(DiscountStrategy):
    """
    Strategy that applies no discount.

    This is a null object implementation of the DiscountStrategy,
    used when no discount should be applied.
    """

    def apply_discount(self, price: float) -> float:
        """
        Apply no discount, returning the original price.

        Args:
            price: The original price

        Returns:
            float: The original price unchanged

        Raises:
            TypeError: If price is not a float or int
            ValueError: If price is negative
        """
        if not isinstance(price, (int, float)):
            raise TypeError("Price must be a float or int")
        if price < 0:
            raise ValueError("Price cannot be negative")
        return price


class PercentageDiscountStrategy(DiscountStrategy):
    """
    Strategy that applies a percentage-based discount.

    Reduces the price by a specified percentage (e.g., 10% off).
    """

    def __init__(self, discount_percentage: Union[int, float]) -> None:
        """
        Initialize with a percentage discount rate.

        Args:
            discount_percentage: Percentage discount to apply (0-100)

        Raises:
            TypeError: If discount_percentage is not a float or int
            ValueError: If discount_percentage is not between 0 and 100
        """
        if not isinstance(discount_percentage, (int, float)):
            raise TypeError("Discount percentage must be a float or int")
        if not 0 <= discount_percentage <= 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        self._discount_percentage = discount_percentage

    def apply_discount(self, price: float) -> float:
        """
        Apply a percentage-based discount to the price.

        Args:
            price: The original price

        Returns:
            float: The discounted price

        Raises:
            TypeError: If price is not a float or int
            ValueError: If price is negative
        """
        if not isinstance(price, (int, float)):
            raise TypeError("Price must be a float or int")
        if price < 0:
            raise ValueError("Price cannot be negative")
        return price * (1 - self._discount_percentage / 100)


class FixedAmountDiscountStrategy(DiscountStrategy):
    """
    Strategy that applies a fixed amount discount.

    Reduces the price by a specified fixed amount (e.g., $20 off).
    """

    def __init__(self, discount_amount: Union[int, float]) -> None:
        """
        Initialize with a fixed discount amount.

        Args:
            discount_amount: Fixed amount to discount from the price

        Raises:
            TypeError: If discount_amount is not a float or int
            ValueError: If discount_amount is negative
        """
        if not isinstance(discount_amount, (int, float)):
            raise TypeError("Discount amount must be a float or int")
        if discount_amount < 0:
            raise ValueError("Discount amount cannot be negative")
        self._discount_amount = discount_amount

    def apply_discount(self, price: float) -> float:
        """
        Apply a fixed amount discount to the price.

        The price will never go below zero after the discount.

        Args:
            price: The original price

        Returns:
            float: The discounted price, minimum 0

        Raises:
            TypeError: If price is not a float or int
            ValueError: If price is negative
        """
        if not isinstance(price, (int, float)):
            raise TypeError("Price must be a float or int")
        if price < 0:
            raise ValueError("Price cannot be negative")
        return max(0, price - self._discount_amount)
