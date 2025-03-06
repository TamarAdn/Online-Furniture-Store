import pytest

from app.config import TAX_RATE
from app.models.discount_strategy import (
    FixedAmountDiscountStrategy,
    NoDiscountStrategy,
    PercentageDiscountStrategy,
)
from app.models.enums import (
    BedSize,
    ChairMaterial,
    FurnitureSize,
    SofaColor,
    TableShape,
)
from app.models.furniture import Bed, Bookcase, Chair, Furniture, Sofa, Table


class TestFurnitureBase:
    """
    Test base for the common functionality of the Furniture abstract class.
    Uses a concrete implementation for testing abstract class methods.
    """

    class ConcreteFurniture(Furniture):
        """Concrete implementation of the abstract Furniture class for testing."""

        def get_specific_attributes(self):
            return {"test_attr": "test_value"}

    def test_init_valid(self):
        """Test that a furniture item can be created with valid parameters."""
        furniture = self.ConcreteFurniture(
            name="test", price=100.0, description="Test description"
        )
        assert furniture.name == "test"
        assert furniture.price == 100.0
        assert furniture.description == "Test description"
        assert isinstance(furniture.discount_strategy, NoDiscountStrategy)

    def test_init_with_id(self):
        """Test that a furniture item can be created with an ID."""
        furniture = self.ConcreteFurniture(
            name="test", price=100.0, furniture_id="F123"
        )
        assert furniture.id == "F123"

    def test_init_negative_price(self):
        """Test that creating a furniture with a negative price raises a ValueError."""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            self.ConcreteFurniture(name="test", price=-10.0)

    def test_init_non_numeric_price(self):
        """Test that creating a furniture with a
        non-numeric price raises a TypeError."""
        with pytest.raises(TypeError, match="Price must be a number"):
            self.ConcreteFurniture(name="test", price="100")

    def test_init_price_exceeds_maximum(self):
        """Test that creating a furniture with a price
        exceeding the maximum raises a ValueError."""
        with pytest.raises(ValueError, match="Price exceeds maximum allowed value"):
            self.ConcreteFurniture(name="test", price=2000000)

    def test_init_non_string_name(self):
        """Test that creating a furniture with a non-string name raises a TypeError."""
        with pytest.raises(TypeError, match="Name must be a string"):
            self.ConcreteFurniture(name=123, price=100.0)

    def test_init_non_string_description(self):
        """Test that creating a furniture with a non-string
        description raises a TypeError."""
        with pytest.raises(TypeError, match="Description must be a string"):
            self.ConcreteFurniture(name="test", price=100.0, description=123)

    def test_init_description_too_long(self):
        """Test that creating a furniture with a
        description exceeding the maximum length raises a ValueError."""
        with pytest.raises(ValueError, match="Description exceeds maximum length"):
            self.ConcreteFurniture(name="test", price=100.0, description="a" * 1001)

    def test_init_non_string_id(self):
        """Test that creating a furniture with a non-string ID raises a TypeError."""
        with pytest.raises(TypeError, match="Furniture ID must be a string"):
            self.ConcreteFurniture(name="test", price=100.0, furniture_id=123)

    def test_name_normalization(self):
        """Test that the name is normalized to lowercase."""
        furniture = self.ConcreteFurniture(name="TeSt", price=100.0)
        assert furniture.name == "test"

    def test_discount_strategy_setter(self):
        """Test that the discount strategy can be changed."""
        furniture = self.ConcreteFurniture(name="test", price=100.0)
        assert isinstance(furniture.discount_strategy, NoDiscountStrategy)

        # Change to percentage discount
        new_strategy = PercentageDiscountStrategy(20)
        furniture.discount_strategy = new_strategy
        assert furniture.discount_strategy == new_strategy

    def test_discount_strategy_setter_invalid_type(self):
        """Test that setting a non-DiscountStrategy
        object as strategy raises a TypeError."""
        furniture = self.ConcreteFurniture(name="test", price=100.0)
        with pytest.raises(
            TypeError, match="Strategy must be a DiscountStrategy object"
        ):
            furniture.discount_strategy = "not a strategy"

    def test_get_discounted_price_no_discount(self):
        """Test that get_discounted_price returns the correct price with no discount."""
        furniture = self.ConcreteFurniture(name="test", price=100.0)
        assert furniture.get_discounted_price() == 100.0

    def test_get_discounted_price_with_percentage_discount(self):
        """Test that get_discounted_price applies percentage discount correctly."""
        furniture = self.ConcreteFurniture(name="test", price=100.0)
        furniture.discount_strategy = PercentageDiscountStrategy(20)
        assert furniture.get_discounted_price() == 80.0

    def test_get_discounted_price_with_fixed_amount_discount(self):
        """Test that get_discounted_price applies fixed amount discount correctly."""
        furniture = self.ConcreteFurniture(name="test", price=100.0)
        furniture.discount_strategy = FixedAmountDiscountStrategy(25.0)
        assert furniture.get_discounted_price() == 75.0

    def test_get_final_price(self):
        """Test that get_final_price applies both discount and tax correctly."""
        furniture = self.ConcreteFurniture(name="test", price=100.0)
        furniture.discount_strategy = PercentageDiscountStrategy(20)
        expected_final_price = 80.0 * (1 + TAX_RATE)
        assert furniture.get_final_price() == expected_final_price

    def test_to_dict(self):
        """Test that to_dict returns the correct dictionary representation."""
        furniture = self.ConcreteFurniture(
            name="test",
            price=100.0,
            furniture_id="F123",
            description="Test description",
        )
        expected_dict = {
            "id": "F123",
            "name": "test",
            "price": 100.0,
            "description": "Test description",
            "attributes": {"test_attr": "test_value"},
        }
        assert furniture.to_dict() == expected_dict


class TestChair:
    """Tests for the Chair class."""

    @pytest.mark.parametrize("material", [m.value for m in ChairMaterial])
    def test_init_valid_material(self, material):
        """Test that a chair can be created with valid material."""
        chair = Chair(price=100.0, material=material)
        assert chair.name == "chair"
        assert chair.price == 100.0
        assert chair.material == material

    def test_init_invalid_material(self):
        """Test that creating a chair with an invalid material raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid chair material"):
            Chair(price=100.0, material="invalid")

    def test_init_non_string_material(self):
        """Test that creating a chair with a non-string material raises a ValueError."""
        with pytest.raises(ValueError):
            Chair(price=100.0, material=123)

    def test_material_normalization(self):
        """Test that material string is normalized to lowercase."""
        chair = Chair(price=100.0, material="WOOD")
        assert chair.material == "wood"

    def test_get_specific_attributes(self):
        """Test that get_specific_attributes returns the correct dictionary."""
        chair = Chair(price=100.0, material="wood")
        assert chair.get_specific_attributes() == {"material": "wood"}


class TestTable:
    """Tests for the Table class."""

    @pytest.mark.parametrize("shape", [s.value for s in TableShape])
    def test_init_valid_shape(self, shape):
        """Test that a table can be created with valid shape."""
        table = Table(price=200.0, shape=shape)
        assert table.name == "table"
        assert table.price == 200.0
        assert table.shape == shape
        assert table.size == "medium"  # Default size

    @pytest.mark.parametrize("size", [s.value for s in FurnitureSize])
    def test_init_valid_size(self, size):
        """Test that a table can be created with valid size."""
        table = Table(price=200.0, shape="round", size=size)
        assert table.size == size

    def test_init_invalid_shape(self):
        """Test that creating a table with an invalid shape raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid table shape"):
            Table(price=200.0, shape="invalid")

    def test_init_non_string_shape(self):
        """Test that creating a table with a non-string shape raises a ValueError."""
        with pytest.raises(ValueError):
            Table(price=200.0, shape=123)

    def test_init_invalid_size(self):
        """Test that creating a table with an invalid size raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid table size"):
            Table(price=200.0, shape="round", size="invalid")

    def test_init_non_string_size(self):
        """Test that creating a table with a non-string size raises a ValueError."""
        with pytest.raises(ValueError):
            Table(price=200.0, shape="round", size=123)

    def test_shape_size_normalization(self):
        """Test that shape and size strings are normalized to lowercase."""
        table = Table(price=200.0, shape="ROUND", size="LARGE")
        assert table.shape == "round"
        assert table.size == "large"

    def test_get_specific_attributes(self):
        """Test that get_specific_attributes returns the correct dictionary."""
        table = Table(price=200.0, shape="oval", size="small")
        assert table.get_specific_attributes() == {"shape": "oval", "size": "small"}


class TestSofa:
    """Tests for the Sofa class."""

    def test_init_valid_defaults(self):
        """Test that a sofa can be created with default values."""
        sofa = Sofa(price=300.0)
        assert sofa.name == "sofa"
        assert sofa.price == 300.0
        assert sofa.seats == 3  # Default seats
        assert sofa.color == "gray"  # Default color

    @pytest.mark.parametrize("seats", [2, 3, 4, 5])
    def test_init_valid_seats(self, seats):
        """Test that a sofa can be created with valid seat counts."""
        sofa = Sofa(price=300.0, seats=seats)
        assert sofa.seats == seats

    @pytest.mark.parametrize("color", [c.value for c in SofaColor])
    def test_init_valid_color(self, color):
        """Test that a sofa can be created with valid colors."""
        sofa = Sofa(price=300.0, color=color)
        assert sofa.color == color

    def test_init_invalid_seats_low(self):
        """Test that creating a sofa with too few seats raises a ValueError."""
        with pytest.raises(ValueError, match="Sofa seats must be between 2 and 5"):
            Sofa(price=300.0, seats=1)

    def test_init_invalid_seats_high(self):
        """Test that creating a sofa with too many seats raises a ValueError."""
        with pytest.raises(ValueError, match="Sofa seats must be between 2 and 5"):
            Sofa(price=300.0, seats=6)

    def test_init_invalid_seats_type(self):
        """Test that creating a sofa with non-integer seats raises a TypeError."""
        with pytest.raises(TypeError, match="Seats must be an integer"):
            Sofa(price=300.0, seats="3")

    def test_init_invalid_color(self):
        """Test that creating a sofa with an invalid color raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid sofa color"):
            Sofa(price=300.0, color="invalid")

    def test_init_non_string_color(self):
        """Test that creating a sofa with a non-string color raises a ValueError."""
        with pytest.raises(ValueError):
            Sofa(price=300.0, color=123)

    def test_color_normalization(self):
        """Test that color string is normalized to lowercase."""
        sofa = Sofa(price=300.0, color="BLACK")
        assert sofa.color == "black"

    def test_get_specific_attributes(self):
        """Test that get_specific_attributes returns the correct dictionary."""
        sofa = Sofa(price=300.0, seats=4, color="beige")
        assert sofa.get_specific_attributes() == {"seats": 4, "color": "beige"}


class TestBed:
    """Tests for the Bed class."""

    @pytest.mark.parametrize("size", [s.value for s in BedSize])
    def test_init_valid_size(self, size):
        """Test that a bed can be created with valid size."""
        bed = Bed(price=400.0, size=size)
        assert bed.name == "bed"
        assert bed.price == 400.0
        assert bed.size == size

    def test_init_invalid_size(self):
        """Test that creating a bed with an invalid size raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid bed size"):
            Bed(price=400.0, size="invalid")

    def test_init_non_string_size(self):
        """Test that creating a bed with a non-string size raises a ValueError."""
        with pytest.raises(ValueError):
            Bed(price=400.0, size=123)

    def test_size_normalization(self):
        """Test that size string is normalized to lowercase."""
        bed = Bed(price=400.0, size="KING")
        assert bed.size == "king"

    def test_get_specific_attributes(self):
        """Test that get_specific_attributes returns the correct dictionary."""
        bed = Bed(price=400.0, size="queen")
        assert bed.get_specific_attributes() == {"size": "queen"}


class TestBookcase:
    """Tests for the Bookcase class."""

    def test_init_valid_defaults(self):
        """Test that a bookcase can be created with default size."""
        bookcase = Bookcase(price=150.0, shelves=3)
        assert bookcase.name == "bookcase"
        assert bookcase.price == 150.0
        assert bookcase.shelves == 3
        assert bookcase.size == "medium"  # Default size

    @pytest.mark.parametrize("shelves", [1, 5, 10])
    def test_init_valid_shelves(self, shelves):
        """Test that a bookcase can be created with valid shelf counts."""
        bookcase = Bookcase(price=150.0, shelves=shelves)
        assert bookcase.shelves == shelves

    @pytest.mark.parametrize("size", [s.value for s in FurnitureSize])
    def test_init_valid_size(self, size):
        """Test that a bookcase can be created with valid size."""
        bookcase = Bookcase(price=150.0, shelves=3, size=size)
        assert bookcase.size == size

    def test_init_invalid_shelves_low(self):
        """Test that creating a bookcase with too few shelves raises a ValueError."""
        with pytest.raises(
            ValueError, match="Bookcase shelves must be between 1 and 10"
        ):
            Bookcase(price=150.0, shelves=0)

    def test_init_invalid_shelves_high(self):
        """Test that creating a bookcase with too many shelves raises a ValueError."""
        with pytest.raises(
            ValueError, match="Bookcase shelves must be between 1 and 10"
        ):
            Bookcase(price=150.0, shelves=11)

    def test_init_invalid_shelves_type(self):
        """Test that creating a bookcase with non-integer shelves raises a TypeError."""
        with pytest.raises(TypeError, match="Shelves must be an integer"):
            Bookcase(price=150.0, shelves="3")

    def test_init_invalid_size(self):
        """Test that creating a bookcase with an invalid size raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid bookcase size"):
            Bookcase(price=150.0, shelves=3, size="invalid")

    def test_init_non_string_size(self):
        """Test that creating a bookcase with a non-string size raises a ValueError."""
        with pytest.raises(ValueError):
            Bookcase(price=150.0, shelves=3, size=123)

    def test_size_normalization(self):
        """Test that size string is normalized to lowercase."""
        bookcase = Bookcase(price=150.0, shelves=3, size="LARGE")
        assert bookcase.size == "large"

    def test_get_specific_attributes(self):
        """Test that get_specific_attributes returns the correct dictionary."""
        bookcase = Bookcase(price=150.0, shelves=4, size="small")
        assert bookcase.get_specific_attributes() == {"shelves": 4, "size": "small"}
