import pytest

# Import the discount strategies
from app.models.discount_strategy import (
    FixedAmountDiscountStrategy,
    NoDiscountStrategy,
    PercentageDiscountStrategy,
)


class TestDiscountStrategies:
    """Test cases for the different discount strategies.

    This test suite verifies that all discount strategies correctly:
    1. Calculate discounts according to their specific algorithms
    2. Validate price inputs (type and value)
    3. Validate discount parameters (type and value)
    4. Handle edge cases appropriately
    """

    @pytest.mark.parametrize(
        "price, expected_price",
        [
            (100.0, 100.0),  # Standard price
            (0.0, 0.0),  # Zero price (boundary case)
            (50.5, 50.5),  # Decimal price
            (1000.0, 1000.0),  # Large price
            (0.001, 0.001),  # Very small price
        ],
    )
    def test_no_discount_strategy(self, price, expected_price):
        """Verify NoDiscountStrategy returns original price unchanged.

        Tests that the strategy correctly implements the null object pattern
        by returning the input price without any modifications.
        """
        strategy = NoDiscountStrategy()
        result = strategy.apply_discount(price)

        assert result == expected_price

    def test_no_discount_strategy_negative_price(self):
        """Verify NoDiscountStrategy rejects negative prices.

        Tests that the strategy correctly validates input prices
        and raises appropriate exceptions for invalid values.
        """
        strategy = NoDiscountStrategy()

        with pytest.raises(ValueError) as excinfo:
            strategy.apply_discount(-10.0)
        assert "Price cannot be negative" in str(excinfo.value)

    def test_no_discount_strategy_invalid_type(self):
        """Verify NoDiscountStrategy rejects non-numeric price types.

        Tests that the strategy correctly validates input types
        and raises appropriate exceptions for invalid types.
        """
        strategy = NoDiscountStrategy()

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount("100")
        assert "Price must be a float or int" in str(excinfo.value)

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount(None)
        assert "Price must be a float or int" in str(excinfo.value)

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount([100])
        assert "Price must be a float or int" in str(excinfo.value)

    @pytest.mark.parametrize(
        "price, discount_percentage, expected_price",
        [
            (100.0, 10, 90.0),  # Standard 10% discount
            (100.0, 0, 100.0),  # 0% discount (boundary case)
            (100.0, 100, 0.0),  # 100% discount (boundary case)
            (50.0, 20, 40.0),  # 20% off different price
            (199.99, 15, 169.9915),  # Discount with decimal price
            (10.0, 50, 5.0),  # 50% discount (half price)
            (0.01, 10, 0.009),  # Discount on very small price
            (0.0, 50, 0.0),  # Discount on zero price
        ],
    )
    def test_percentage_discount_strategy(
        self, price, discount_percentage, expected_price
    ):
        """Verify PercentageDiscountStrategy correctly applies percentage discounts.

        Tests that the strategy correctly calculates discounted prices
        by reducing the original price by the specified percentage.
        """
        strategy = PercentageDiscountStrategy(discount_percentage)
        result = strategy.apply_discount(price)

        assert result == pytest.approx(expected_price)

    def test_percentage_discount_strategy_negative_price(self):
        """Verify PercentageDiscountStrategy rejects negative prices.

        Tests that the strategy correctly validates input prices
        and raises appropriate exceptions for invalid values.
        """
        strategy = PercentageDiscountStrategy(10)

        with pytest.raises(ValueError) as excinfo:
            strategy.apply_discount(-10.0)
        assert "Price cannot be negative" in str(excinfo.value)

    def test_percentage_discount_strategy_invalid_price_type(self):
        """Verify PercentageDiscountStrategy rejects non-numeric price types.

        Tests that the strategy correctly validates input types
        and raises appropriate exceptions for invalid types.
        """
        strategy = PercentageDiscountStrategy(10)

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount("100")
        assert "Price must be a float or int" in str(excinfo.value)

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount(None)
        assert "Price must be a float or int" in str(excinfo.value)

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount([100])
        assert "Price must be a float or int" in str(excinfo.value)

    def test_percentage_discount_strategy_validation(self):
        """Verify PercentageDiscountStrategy validates discount percentages.

        Tests that the strategy constructor properly validates:
        1. The discount percentage range (0-100)
        2. The discount percentage type (must be numeric)
        """
        # Test valid values
        PercentageDiscountStrategy(0)  # Minimum valid value
        PercentageDiscountStrategy(50)  # Mid-range value
        PercentageDiscountStrategy(100)  # Maximum valid value
        PercentageDiscountStrategy(0.5)  # Decimal percentage

        # Test invalid values
        with pytest.raises(ValueError) as excinfo:
            PercentageDiscountStrategy(-1)  # Below minimum
        assert "Discount percentage must be between 0 and 100" in str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            PercentageDiscountStrategy(101)  # Above maximum
        assert "Discount percentage must be between 0 and 100" in str(excinfo.value)

        # Test invalid types
        with pytest.raises(TypeError) as excinfo:
            PercentageDiscountStrategy("50")  # String value
        assert "Discount percentage must be a float or int" in str(excinfo.value)

        with pytest.raises(TypeError) as excinfo:
            PercentageDiscountStrategy(None)  # None value
        assert "Discount percentage must be a float or int" in str(excinfo.value)

    @pytest.mark.parametrize(
        "price, discount_amount, expected_price",
        [
            (100.0, 10, 90.0),  # Standard $10 discount
            (100.0, 0, 100.0),  # $0 discount (no change)
            (100.0, 100, 0.0),  # Discount equals price (result = 0)
            (50.0, 20, 30.0),  # Partial discount
            (30.0, 50, 0.0),  # Discount exceeds price (floor at 0)
            (0.1, 0.05, 0.05),  # Small price with small discount
            (0.0, 10, 0.0),  # Zero price (remains zero)
        ],
    )
    def test_fixed_amount_discount_strategy(
        self, price, discount_amount, expected_price
    ):
        """Verify FixedAmountDiscountStrategy correctly applies fixed discounts.

        Tests that the strategy correctly calculates discounted prices
        by subtracting the fixed amount, without going below zero.
        """
        strategy = FixedAmountDiscountStrategy(discount_amount)
        result = strategy.apply_discount(price)

        assert result == pytest.approx(expected_price)

    def test_fixed_amount_discount_strategy_negative_price(self):
        """Verify FixedAmountDiscountStrategy rejects negative prices.

        Tests that the strategy correctly validates input prices
        and raises appropriate exceptions for invalid values.
        """
        strategy = FixedAmountDiscountStrategy(10)

        with pytest.raises(ValueError) as excinfo:
            strategy.apply_discount(-10.0)
        assert "Price cannot be negative" in str(excinfo.value)

    def test_fixed_amount_discount_strategy_invalid_price_type(self):
        """Verify FixedAmountDiscountStrategy rejects non-numeric price types.

        Tests that the strategy correctly validates input types
        and raises appropriate exceptions for invalid types.
        """
        strategy = FixedAmountDiscountStrategy(10)

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount("100")
        assert "Price must be a float or int" in str(excinfo.value)

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount(None)
        assert "Price must be a float or int" in str(excinfo.value)

        with pytest.raises(TypeError) as excinfo:
            strategy.apply_discount([100])
        assert "Price must be a float or int" in str(excinfo.value)

    def test_fixed_amount_discount_strategy_validation(self):
        """Verify FixedAmountDiscountStrategy validates discount amounts.

        Tests that the strategy constructor properly validates:
        1. The discount amount (must be non-negative)
        2. The discount amount type (must be numeric)
        """
        # Test valid values
        FixedAmountDiscountStrategy(0)  # Minimum valid value (no discount)
        FixedAmountDiscountStrategy(10)  # Standard discount
        FixedAmountDiscountStrategy(100)  # Large discount
        FixedAmountDiscountStrategy(0.5)  # Decimal amount

        # Test invalid values
        with pytest.raises(ValueError) as excinfo:
            FixedAmountDiscountStrategy(-1)  # Negative discount
        assert "Discount amount cannot be negative" in str(excinfo.value)

        # Test invalid types
        with pytest.raises(TypeError) as excinfo:
            FixedAmountDiscountStrategy("10")  # String value
        assert "Discount amount must be a float or int" in str(excinfo.value)

        with pytest.raises(TypeError) as excinfo:
            FixedAmountDiscountStrategy(None)  # None value
        assert "Discount amount must be a float or int" in str(excinfo.value)
