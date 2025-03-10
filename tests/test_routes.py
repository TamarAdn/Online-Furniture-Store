from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.routes import get_authenticated_user
from app.utils import AuthenticationError

# =============================================================================
# Fixtures & Dummy Objects
# =============================================================================


@pytest.fixture
def client():
    """
    Create and configure a new Flask app instance for each test.

    Registers the blueprint from app.routes and sets the app to testing mode.
    """
    from flask import Flask

    from app.routes import api  # assumes your blueprint is in app/routes.py

    app = Flask(__name__)
    app.register_blueprint(api)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def dummy_user():
    """
    Create a dummy user object with required attributes and a shopping cart.

    Returns:
        MagicMock: A dummy user with preset attributes and shopping_cart methods.
    """
    user = MagicMock()
    user.id = "user123"
    user.username = "testuser"
    user.full_name = "Test User"
    user.email = "test@example.com"
    user.shipping_address = "123 Test St"

    # Set up a dummy shopping cart with required methods/attributes.
    shopping_cart = MagicMock()
    shopping_cart.get_subtotal.return_value = 150.0
    shopping_cart.get_total.return_value = 140.0
    shopping_cart.__len__.return_value = 1
    shopping_cart.clear = MagicMock()
    shopping_cart.add_item = MagicMock()
    shopping_cart.remove_item = MagicMock(return_value=True)

    user.shopping_cart = shopping_cart
    user.view_cart.return_value = []
    return user


def create_dummy_furniture():
    """
    Create a dummy furniture object with a to_dict() method.

    Returns:
        MagicMock: A dummy furniture object.
    """
    furniture = MagicMock()
    furniture.to_dict.return_value = {"name": "Chair", "price": 50}
    return furniture


# =============================================================================
# Furniture Routes Tests
# =============================================================================


class TestFurnitureRoutes:
    """Tests for the furniture-related routes."""

    @patch("app.routes.inventory.get_all_furniture")
    def test_get_all_furniture_no_filters(self, mock_get_all, client):
        """
        Test GET /api/furniture without any filters.

        The dummy furniture is returned and the response
        should include the furniture details.
        """
        dummy_item = {"furniture": create_dummy_furniture(), "quantity": 5}
        mock_get_all.return_value = [dummy_item]
        response = client.get("/api/furniture")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert data[0]["name"] == "Chair"
        assert data[0]["price"] == 50
        assert data[0]["quantity"] == 5

    @patch("app.routes.inventory.search")
    @pytest.mark.parametrize(
        "query,param,expected_quantity",
        [
            ("furniture_name=chair", "furniture_name", 3),
            ("furniture_name=chair", "furniture_name", 4),
        ],
    )
    def test_get_all_furniture_with_filters(
        self, mock_search, client, query, param, expected_quantity
    ):
        """
        Test GET /api/furniture with a furniture_name filter.

        The mocked search returns an item with the given quantity.
        """
        dummy_item = {
            "furniture": create_dummy_furniture(),
            "quantity": expected_quantity,
        }
        mock_search.return_value = [dummy_item]
        response = client.get(f"/api/furniture?{query}")
        assert response.status_code == 200
        data = response.get_json()
        assert data[0]["quantity"] == expected_quantity

    def test_get_all_furniture_invalid_price(self, client):
        """
        Test GET /api/furniture with an invalid price format.

        Should return a 400 status code with an appropriate error message.
        """
        response = client.get("/api/furniture?min_price=invalid&max_price=100")
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid price format" in data["error"]

    @patch("app.routes.inventory.get_furniture")
    @patch("app.routes.inventory.get_quantity")
    def test_get_furniture_by_id_found(
        self, mock_get_quantity, mock_get_furniture, client
    ):
        """
        Test GET /api/furniture/<furniture_id> for a furniture that exists.

        The endpoint should return a furniture object with its quantity.
        """
        dummy_furniture = create_dummy_furniture()
        mock_get_furniture.return_value = dummy_furniture
        mock_get_quantity.return_value = 10
        response = client.get("/api/furniture/123")
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Chair"
        assert data["quantity"] == 10

    @patch("app.routes.inventory.get_furniture")
    def test_get_furniture_by_id_not_found(self, mock_get_furniture, client):
        """
        Test GET /api/furniture/<furniture_id> for a furniture that does not exist.

        The endpoint should return a 404 status code.
        """
        mock_get_furniture.return_value = None
        response = client.get("/api/furniture/invalid")
        assert response.status_code == 404

    @patch("app.routes.inventory.search")
    def test_get_all_furniture_min_price_only(self, mock_search, client):
        """
        Test GET /api/furniture with only min_price provided.

        The search strategy should have min_price set and max_price as infinity.
        """
        dummy_item = {"furniture": create_dummy_furniture(), "quantity": 2}
        mock_search.return_value = [dummy_item]
        response = client.get("/api/furniture?min_price=10")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        args, kwargs = mock_search.call_args
        strategy = args[0]
        assert strategy.min_price == 10.0
        assert strategy.max_price == float("inf")

    @patch("app.routes.inventory.search")
    def test_get_all_furniture_value_error(self, mock_search, client):
        """
        Test GET /api/furniture where inventory.search raises a ValueError.

        Should return a 400 status code with the ValueError message.
        """
        mock_search.side_effect = ValueError("Test ValueError")
        response = client.get("/api/furniture?furniture_name=chair")
        assert response.status_code == 400
        data = response.get_json()
        assert "Test ValueError" in data["error"]

    @patch("app.routes.inventory.search")
    def test_get_all_furniture_generic_exception(self, mock_search, client):
        """
        Test GET /api/furniture where inventory.search raises a generic Exception.

        Should return a 500 status code with the exception message.
        """
        mock_search.side_effect = Exception("Test Exception")
        response = client.get("/api/furniture?furniture_name=chair")
        assert response.status_code == 500
        data = response.get_json()
        assert "Test Exception" in data["error"]

    @patch("app.routes.inventory.search")
    def test_get_all_furniture_with_attribute_name(self, mock_search, client):
        """
        Test GET /api/furniture with attribute_name & attribute_value.
        This covers the branch where attribute_name is not None.
        """
        dummy_item = {"furniture": create_dummy_furniture(), "quantity": 2}
        mock_search.return_value = [dummy_item]

        # Query with ?attribute_name=material&attribute_value=wood
        response = client.get(
            "/api/furniture?attribute_name=material&attribute_value=wood"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["quantity"] == 2

        # Verify the search was called with the correct strategy
        args, _ = mock_search.call_args
        search_strategy = args[0]
        assert search_strategy.attribute_name == "material"
        assert search_strategy.attribute_value == "wood"

    # POST /api/furniture tests

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.add_furniture")
    def test_add_furniture_valid(self, mock_add_furniture, mock_auth, client):
        """
        Test POST /api/furniture with valid furniture data.

        Should return a 201 status code and the new furniture id.
        """
        mock_auth.return_value = dummy_user()
        mock_add_furniture.return_value = "furn123"
        payload = {
            "name": "chair", 
            "price": 100,
            "quantity": 2,
            "material": "wood",
            "description": "Comfortable chair",
        }
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["id"] == "furn123"
        assert data["quantity"] == 2

    @patch("app.routes.get_authenticated_user")
    def test_add_furniture_missing_data(self, mock_auth, client):
        """
        Test POST /api/furniture with missing data.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.post("/api/furniture", json={})
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    def test_add_furniture_unsupported_type(self, mock_auth, client):
        """
        Test POST /api/furniture with an unsupported furniture type.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        # Use "name": "unknown" + a valid "description" so the route
        # doesn't fail earlier for missing fields
        payload = {
            "name": "unknown",
            "price": 100,
            "quantity": 1,
            "description": "Some description",
        }
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        # Optional: check the specific error
        assert "Unsupported furniture type: unknown" in data["error"]

    @patch(
        "app.routes.get_authenticated_user",
        side_effect=AuthenticationError("Unauthorized"),
    )
    def test_add_furniture_unauthorized(self, mock_auth, client):
        """
        Test POST /api/furniture when authentication fails.

        Should return a 401 status code.
        """
        payload = {"type": "chair", "price": 100}
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 401

    # Specific furniture creation branches

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.add_furniture")
    @patch("app.routes.Table")
    def test_add_furniture_table(
        self, mock_table, mock_add_furniture, mock_auth, client
    ):
        """
        Test POST /api/furniture for adding a table.

        Should return a 201 status code with table-specific attributes.
        """
        mock_auth.return_value = dummy_user()
        dummy_table = MagicMock()
        dummy_table.to_dict.return_value = {
            "name": "Table",
            "price": 200,
            "description": "A round table",
        }
        mock_table.return_value = dummy_table
        mock_add_furniture.return_value = "table123"
        payload = {
            "name": "table",
            "price": "200",
            "quantity": 1,
            "shape": "round",
            "size": "large",
            "description": "A round table",
        }
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["id"] == "table123"
        assert data["quantity"] == 1

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.add_furniture")
    @patch("app.routes.Sofa")
    def test_add_furniture_sofa(self, mock_sofa, mock_add_furniture, mock_auth, client):
        """
        Test POST /api/furniture for adding a sofa.

        Should return a 201 status code with sofa-specific attributes.
        """
        mock_auth.return_value = dummy_user()
        dummy_sofa = MagicMock()
        dummy_sofa.to_dict.return_value = {
            "name": "Sofa",
            "price": 300,
            "description": "A comfy sofa",
        }
        mock_sofa.return_value = dummy_sofa
        mock_add_furniture.return_value = "sofa123"
        payload = {
            "name": "sofa",
            "price": "300",
            "quantity": 2,
            "seats": "3",
            "color": "blue",
            "description": "A comfy sofa",
        }
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["id"] == "sofa123"
        assert data["quantity"] == 2

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.add_furniture")
    @patch("app.routes.Bed")
    def test_add_furniture_bed(self, mock_bed, mock_add_furniture, mock_auth, client):
        """
        Test POST /api/furniture for adding a bed.

        Should return a 201 status code with bed-specific attributes.
        """
        mock_auth.return_value = dummy_user()
        dummy_bed = MagicMock()
        dummy_bed.to_dict.return_value = {
            "name": "Bed",
            "price": 400,
            "description": "A queen bed",
        }
        mock_bed.return_value = dummy_bed
        mock_add_furniture.return_value = "bed123"
        payload = {
            "name": "bed",
            "price": "400",
            "quantity": 1,
            "size": "queen",
            "description": "A queen bed",
        }
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["id"] == "bed123"
        assert data["quantity"] == 1

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.add_furniture")
    @patch("app.routes.Bookcase")
    def test_add_furniture_bookcase(
        self, mock_bookcase, mock_add_furniture, mock_auth, client
    ):
        """
        Test POST /api/furniture for adding a bookcase.

        Should return a 201 status code with bookcase-specific attributes.
        """
        mock_auth.return_value = dummy_user()
        dummy_bookcase = MagicMock()
        dummy_bookcase.to_dict.return_value = {
            "name": "Bookcase",
            "price": 150,
            "description": "A bookcase",
        }
        mock_bookcase.return_value = dummy_bookcase
        mock_add_furniture.return_value = "bookcase123"
        payload = {
            "name": "bookcase",
            "price": "150",
            "quantity": 1,
            "shelves": "4",
            "size": "medium",
            "description": "A bookcase",
        }
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["id"] == "bookcase123"
        assert data["quantity"] == 1

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.add_furniture")
    def test_add_furniture_value_error(self, mock_add_furniture, mock_auth, client):
        """
        Test POST /api/furniture with non-numeric price to trigger a ValueError.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        payload = {
            "name": "chair",  # changed from "type"
            "price": "not-a-number",
            "quantity": 1,
            "material": "wood",
            "description": "A chair",
        }
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert (
            "could not convert" in data["error"] or "invalid literal" in data["error"]
        )

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.add_furniture")
    def test_add_furniture_generic_exception(
        self, mock_add_furniture, mock_auth, client
    ):
        """
        Test POST /api/furniture where add_furniture raises a generic Exception.

        Should return a 500 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_add_furniture.side_effect = Exception("Generic error")
        payload = {
            "name": "chair",
            "price": "100",
            "quantity": 1,
            "material": "wood",
            "description": "A chair",
        }
        response = client.post("/api/furniture", json=payload)
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    # PUT /api/furniture/<furniture_id> tests

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.update_quantity")
    def test_update_furniture_quantity_success(self, mock_update, mock_auth, client):
        """
        Test PUT /api/furniture/<furniture_id>
        to update furniture quantity successfully.

        Should return a 200 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_update.return_value = True
        payload = {"quantity": 15}
        response = client.put("/api/furniture/123", json=payload)
        assert response.status_code == 200

    @patch("app.routes.get_authenticated_user")
    def test_update_furniture_quantity_missing(self, mock_auth, client):
        """
        Test PUT /api/furniture/<furniture_id> with missing quantity.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.put("/api/furniture/123", json={})
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.update_quantity")
    def test_update_furniture_quantity_not_found(self, mock_update, mock_auth, client):
        """
        Test PUT /api/furniture/<furniture_id> when the furniture is not found.

        Should return a 404 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_update.return_value = False
        payload = {"quantity": 5}
        response = client.put("/api/furniture/123", json=payload)
        assert response.status_code == 404

    @patch("app.routes.get_authenticated_user")
    def test_update_furniture_quantity_auth_error(self, mock_auth, client):
        """
        Test PUT /api/furniture/<furniture_id> when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        response = client.put("/api/furniture/123", json={"quantity": 10})
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_update_furniture_quantity_value_error(self, mock_auth, client):
        """
        Test PUT /api/furniture/<furniture_id> with non-numeric quantity.

        Should return a 400 status code with a conversion error message.
        """
        mock_auth.return_value = dummy_user()
        response = client.put("/api/furniture/123", json={"quantity": "abc"})
        assert response.status_code == 400
        data = response.get_json()
        assert "invalid literal" in data["error"]

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.update_quantity")
    def test_update_furniture_quantity_generic_exception(
        self, mock_update, mock_auth, client
    ):
        """
        Test PUT /api/furniture/<furniture_id>
        where update_quantity raises a generic Exception.

        Should return a 500 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_update.side_effect = Exception("Generic error")
        response = client.put("/api/furniture/123", json={"quantity": 10})
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    # DELETE /api/furniture/<furniture_id> tests

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.remove_furniture")
    def test_remove_furniture_success(self, mock_remove, mock_auth, client):
        """
        Test DELETE /api/furniture/<furniture_id> for successful removal.

        Should return a 200 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_remove.return_value = True
        response = client.delete("/api/furniture/123")
        assert response.status_code == 200

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.remove_furniture")
    def test_remove_furniture_not_found(self, mock_remove, mock_auth, client):
        """
        Test DELETE /api/furniture/<furniture_id> when furniture is not found.

        Should return a 404 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_remove.return_value = False
        response = client.delete("/api/furniture/invalid")
        assert response.status_code == 404

    def test_remove_furniture_auth_error(self, client, mocker):
        """
        Test DELETE /api/furniture/<furniture_id> when authentication fails.

        Should return a 401 status code.
        """
        mocker.patch(
            "app.routes.get_authenticated_user",
            side_effect=AuthenticationError("Auth error"),
        )
        response = client.delete("/api/furniture/123")
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    def test_remove_furniture_generic_exception(self, client, mocker):
        """
        Test DELETE /api/furniture/<furniture_id>
        where removal raises a generic Exception.

        Should return a 500 status code.
        """
        dummy = dummy_user()
        mocker.patch("app.routes.get_authenticated_user", return_value=dummy)
        mocker.patch(
            "app.routes.inventory.remove_furniture",
            side_effect=Exception("Generic error"),
        )
        response = client.delete("/api/furniture/123")
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]


# =============================================================================
# User Routes Tests
# =============================================================================


class TestUserRoutes:
    """
    Tests for the user-related routes
    (registration, login, profile, password, logout).
    """

    @patch("app.routes.user_manager.register_user")
    def test_register_user_valid(self, mock_register, client):
        """
        Test POST /api/users/register with valid user registration data.

        Should return a 201 status code with user details.
        """
        dummy = dummy_user()
        dummy.id = "user1"
        dummy.username = "user1"
        dummy.full_name = "User One"
        dummy.email = "user1@example.com"
        dummy.shipping_address = "Address 1"
        mock_register.return_value = dummy
        payload = {
            "username": "user1",
            "full_name": "User One",
            "email": "user1@example.com",
            "password": "password",
            "shipping_address": "Address 1",
        }
        response = client.post("/api/users/register", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["id"] == "user1"
        assert data["username"] == "user1"

    def test_register_user_missing_data(self, client):
        """
        Test POST /api/users/register with missing data.

        Should return a 400 status code.
        """
        response = client.post("/api/users/register", json={})
        assert response.status_code == 400

    @patch("app.routes.user_manager.login")
    def test_login_user_valid(self, mock_login, client):
        """
        Test POST /api/users/login with valid credentials.

        Should return a 200 status code and include user and token data.
        """
        dummy = dummy_user()
        dummy.username = "user1"
        tokens = {"access": "token", "refresh": "rtoken"}
        mock_login.return_value = (dummy, tokens)
        payload = {"username": "user1", "password": "password"}
        response = client.post("/api/users/login", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert "user" in data and "tokens" in data

    def test_login_user_missing_fields(self, client):
        """
        Test POST /api/users/login with missing password.

        Should return a 400 status code.
        """
        response = client.post("/api/users/login", json={"username": "user1"})
        assert response.status_code == 400

    @patch(
        "app.routes.user_manager.login",
        side_effect=AuthenticationError("Invalid credentials"),
    )
    def test_login_user_auth_error(self, mock_login, client):
        """
        Test POST /api/users/login with invalid credentials.

        Should return a 401 status code.
        """
        payload = {"username": "user1", "password": "wrong"}
        response = client.post("/api/users/login", json=payload)
        assert response.status_code == 401

    @patch("app.routes.user_manager.refresh_access_token")
    def test_refresh_token_valid(self, mock_refresh, client):
        """
        Test POST /api/users/refresh-token with a valid refresh token.

        Should return a 200 status code and the new access token.
        """
        mock_refresh.return_value = "newtoken"
        payload = {"refresh_token": "rtoken"}
        response = client.post("/api/users/refresh-token", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["access_token"] == "newtoken"

    def test_refresh_token_missing(self, client):
        """
        Test POST /api/users/refresh-token with missing data.

        Should return a 400 status code.
        """
        response = client.post("/api/users/refresh-token", json={})
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    def test_get_user_profile(self, mock_auth, client):
        """
        Test GET /api/users/profile with a valid user.

        Should return a 200 status code and user details.
        """
        dummy = dummy_user()
        dummy.id = "user1"
        dummy.username = "user1"
        dummy.full_name = "User One"
        dummy.email = "user1@example.com"
        dummy.shipping_address = "Address 1"
        mock_auth.return_value = dummy
        response = client.get("/api/users/profile")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == "user1"

    @patch(
        "app.routes.get_authenticated_user",
        side_effect=AuthenticationError("Unauthorized"),
    )
    def test_get_user_profile_unauthorized(self, mock_auth, client):
        """
        Test GET /api/users/profile when authentication fails.

        Should return a 401 status code.
        """
        response = client.get("/api/users/profile")
        assert response.status_code == 401

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.update_user")
    def test_update_user_profile_success(self, mock_update, mock_auth, client):
        """
        Test PUT /api/users/profile for successful profile update.

        Should return a 200 status code.
        """
        dummy = dummy_user()
        dummy.username = "user1"
        mock_auth.return_value = dummy
        mock_update.return_value = True
        payload = {
            "full_name": "New Name",
            "email": "new@example.com",
            "shipping_address": "New Address",
        }
        response = client.put("/api/users/profile", json=payload)
        assert response.status_code == 200

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.update_user")
    def test_update_user_profile_failure(self, mock_update, mock_auth, client):
        """
        Test PUT /api/users/profile when profile update fails.

        Should return a 400 status code.
        """
        dummy = dummy_user()
        dummy.username = "user1"
        mock_auth.return_value = dummy
        mock_update.return_value = False
        payload = {"full_name": "New Name"}
        response = client.put("/api/users/profile", json=payload)
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.update_password")
    def test_update_password_success(self, mock_update, mock_auth, client):
        """
        Test PUT /api/users/password for a successful password update.

        Should return a 200 status code.
        """
        dummy = dummy_user()
        dummy.username = "user1"
        mock_auth.return_value = dummy
        mock_update.return_value = True
        payload = {"current_password": "old", "new_password": "new"}
        response = client.put("/api/users/password", json=payload)
        assert response.status_code == 200

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.update_password")
    def test_update_password_failure(self, mock_update, mock_auth, client):
        """
        Test PUT /api/users/password when password update fails.

        Should return a 400 status code.
        """
        dummy = dummy_user()
        dummy.username = "user1"
        mock_auth.return_value = dummy
        mock_update.return_value = False
        payload = {"current_password": "old", "new_password": "new"}
        response = client.put("/api/users/password", json=payload)
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.logout")
    def test_logout_user(self, mock_logout, mock_auth, client):
        """
        Test POST /api/users/logout for successful logout.

        Should return a 200 status code.
        """
        dummy = dummy_user()
        mock_auth.return_value = dummy
        response = client.post("/api/users/logout")
        assert response.status_code == 200

    @patch("app.routes.get_authenticated_user")
    def test_update_password_auth_error(self, mock_auth, client):
        """
        Test PUT /api/users/password when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        payload = {"current_password": "oldpass", "new_password": "newpass"}
        response = client.put("/api/users/password", json=payload)
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.update_password")
    def test_update_password_value_error(self, mock_update, mock_auth, client):
        """
        Test PUT /api/users/password where update_password raises a ValueError.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_update.side_effect = ValueError("Test ValueError")
        payload = {"current_password": "oldpass", "new_password": "newpass"}
        response = client.put("/api/users/password", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "Test ValueError" in data["error"]

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.update_password")
    def test_update_password_generic_exception(self, mock_update, mock_auth, client):
        """
        Test PUT /api/users/password where update_password raises a generic Exception.

        Should return a 500 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_update.side_effect = Exception("Generic error")
        payload = {"current_password": "oldpass", "new_password": "newpass"}
        response = client.put("/api/users/password", json=payload)
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_update_user_profile_auth_error(self, mock_auth, client):
        """
        Test PUT /api/users/profile when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        payload = {
            "full_name": "New Name",
            "email": "new@example.com",
            "shipping_address": "New Address",
        }
        response = client.put("/api/users/profile", json=payload)
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.update_user")
    def test_update_user_profile_value_error(self, mock_update, mock_auth, client):
        """
        Test PUT /api/users/profile where update_user raises a ValueError.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_update.side_effect = ValueError("Test ValueError")
        payload = {
            "full_name": "New Name",
            "email": "new@example.com",
            "shipping_address": "New Address",
        }
        response = client.put("/api/users/profile", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "Test ValueError" in data["error"]

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.update_user")
    def test_update_user_profile_generic_exception(
        self, mock_update, mock_auth, client
    ):
        """
        Test PUT /api/users/profile where update_user raises a generic Exception.

        Should return a 500 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_update.side_effect = Exception("Generic error")
        payload = {
            "full_name": "New Name",
            "email": "new@example.com",
            "shipping_address": "New Address",
        }
        response = client.put("/api/users/profile", json=payload)
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_logout_user_auth_error(self, mock_auth, client):
        """
        Test POST /api/users/logout when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        response = client.post("/api/users/logout")
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.user_manager.logout")
    def test_logout_user_generic_exception(self, mock_logout, mock_auth, client):
        """
        Test POST /api/users/logout where logout raises a generic Exception.

        Should return a 500 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_logout.side_effect = Exception("Generic error")
        response = client.post("/api/users/logout")
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.user_manager.refresh_access_token")
    def test_refresh_token_auth_error(self, mock_refresh, client):
        """
        Test POST /api/users/refresh-token when refresh_access_token
        raises AuthenticationError.

        Should return a 401 status code.
        """
        payload = {"refresh_token": "sometoken"}
        mock_refresh.side_effect = AuthenticationError("Auth error")
        response = client.post("/api/users/refresh-token", json=payload)
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.user_manager.refresh_access_token")
    def test_refresh_token_generic_exception(self, mock_refresh, client):
        """
        Test POST /api/users/refresh-token when refresh_access_token
        raises a generic Exception.

        Should return a 500 status code.
        """
        payload = {"refresh_token": "sometoken"}
        mock_refresh.side_effect = Exception("Generic error")
        response = client.post("/api/users/refresh-token", json=payload)
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.user_manager.register_user")
    def test_register_user_value_error(self, mock_register, client):
        """
        Test POST /api/users/register when register_user raises a ValueError.

        Should return a 400 status code.
        """
        mock_register.side_effect = ValueError("Test ValueError")
        payload = {
            "username": "user1",
            "full_name": "User One",
            "email": "user1@example.com",
            "password": "password",
            "shipping_address": "Address 1",
        }
        response = client.post("/api/users/register", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "Test ValueError" in data["error"]

    @patch("app.routes.user_manager.register_user")
    def test_register_user_generic_exception(self, mock_register, client):
        """
        Test POST /api/users/register when register_user raises a generic Exception.

        Should return a 500 status code.
        """
        mock_register.side_effect = Exception("Generic error")
        payload = {
            "username": "user1",
            "full_name": "User One",
            "email": "user1@example.com",
            "password": "password",
            "shipping_address": "Address 1",
        }
        response = client.post("/api/users/register", json=payload)
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.user_manager.login")
    def test_login_user_generic_exception(self, mock_login, client):
        """
        Test POST /api/users/login when login raises a generic Exception.

        Should return a 500 status code.
        """
        mock_login.side_effect = Exception("Generic error")
        payload = {"username": "user1", "password": "pass"}
        response = client.post("/api/users/login", json=payload)
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    def test_login_user_no_data(self, client):
        """
        Test POST /api/users/login with no data provided.

        Should return a 400 status code with an error message.
        """
        response = client.post("/api/users/login", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "No data provided" in data["error"]

    def test_register_user_missing_required_fields(self, client):
        """
        Test POST /api/users/register with missing required fields.

        Should return a 400 status code.
        """
        payload = {"username": "user1"}
        response = client.post("/api/users/register", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "Missing required fields" in data["error"]

    def test_get_user_profile_generic_exception(self, client, mocker):
        """
        Test GET /api/users/profile where an exception
        occurs while accessing user attributes.

        Should return a 500 status code.
        """

        class ErrorUser:
            username = "testuser"
            full_name = "Test User"
            email = "test@example.com"
            shipping_address = "123 Test St"

            @property
            def id(self):
                raise Exception("Generic error")

        mocker.patch("app.routes.get_authenticated_user", return_value=ErrorUser())
        response = client.get("/api/users/profile")
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_update_password_no_data(self, mock_auth, client):
        """
        Test PUT /api/users/password with no JSON data provided.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.put("/api/users/password", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "No data provided" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_update_password_missing_fields(self, mock_auth, client):
        """
        Test PUT /api/users/password with missing current or new password fields.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        # Missing current_password.
        response = client.put("/api/users/password", json={"new_password": "newpass"})
        assert response.status_code == 400
        data = response.get_json()
        assert "Missing current or new password" in data["error"]

        # Missing new_password.
        response = client.put(
            "/api/users/password", json={"current_password": "oldpass"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Missing current or new password" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_update_user_profile_no_data(self, mock_auth, client):
        """
        Test PUT /api/users/profile with no data provided.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.put("/api/users/profile", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "No data provided" in data["error"]


# =============================================================================
# Cart Routes Tests
# =============================================================================


class TestCartRoutes:
    """Tests for the shopping cart related routes."""

    @patch("app.routes.get_authenticated_user")
    def test_get_cart(self, mock_auth, client):
        """
        Test GET /api/cart returns the current user's cart details.

        Validates the presence of items, subtotal, total, and item_count.
        """
        dummy = dummy_user()
        dummy.shopping_cart.get_subtotal.return_value = 150.0
        dummy.shopping_cart.get_total.return_value = 140.0
        dummy.shopping_cart.__len__.return_value = 1
        dummy.view_cart.return_value = [(create_dummy_furniture(), 2)]
        mock_auth.return_value = dummy
        response = client.get("/api/cart")
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert data["subtotal"] == 150.0
        assert data["total"] == 140.0
        assert data["item_count"] == 1

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.get_furniture")
    def test_add_to_cart_success(self, mock_get_furniture, mock_auth, client):
        """
        Test POST /api/cart/add successfully adds an item to the cart.

        Validates that the furniture is found and added with the specified quantity.
        """
        dummy = dummy_user()
        mock_auth.return_value = dummy
        furniture = create_dummy_furniture()
        mock_get_furniture.return_value = furniture
        payload = {"furniture_id": "furn1", "quantity": 3}
        response = client.post("/api/cart/add", json=payload)
        assert response.status_code == 200
        dummy.shopping_cart.add_item.assert_called_with(furniture, 3)

    @patch("app.routes.get_authenticated_user")
    def test_add_to_cart_missing_id(self, mock_auth, client):
        """
        Test POST /api/cart/add with missing furniture_id.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.post("/api/cart/add", json={"quantity": 2})
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.inventory.get_furniture")
    def test_add_to_cart_not_found(self, mock_get_furniture, mock_auth, client):
        """
        Test POST /api/cart/add when the furniture is not found.

        Should return a 404 status code.
        """
        mock_auth.return_value = dummy_user()
        mock_get_furniture.return_value = None
        payload = {"furniture_id": "nonexistent", "quantity": 1}
        response = client.post("/api/cart/add", json=payload)
        assert response.status_code == 404

    @pytest.mark.parametrize("description_keyword", [None, "outdoor"])
    @patch("app.routes.cart_locator.find_and_add_to_cart")
    @patch("app.routes.get_authenticated_user")
    def test_find_and_add_to_cart_success(
        self, mock_get_user, mock_find_and_add, client, description_keyword
    ):
        """
        Test POST /api/cart/find-and-add successfully
        finds and adds an item to the cart.

        Parametrized to handle both:
        - description_keyword=None (not provided)
        - description_keyword="outdoor" (provided)
        """
        dummy = dummy_user()
        mock_get_user.return_value = dummy

        payload = {"name": "chair", "quantity": 1, "color": "red"}

        # If we want to test the route's "kwargs['description_keyword']" line,
        # we add "description_keyword" only if it's not None.
        if description_keyword is not None:
            payload["description_keyword"] = description_keyword

        response = client.post("/api/cart/find-and-add", json=payload)
        assert response.status_code == 200

        # Build expected kwargs for the assertion
        expected_kwargs = {"color": "red"}
        if description_keyword is not None:
            expected_kwargs["description_keyword"] = description_keyword

        # Now we check that the call matches exactly
        mock_find_and_add.assert_called_with(
            dummy.shopping_cart,
            "chair",  # furniture_type
            1,  # quantity
            **expected_kwargs,
        )

    @patch("app.routes.get_authenticated_user")
    def test_find_and_add_to_cart_missing_type(self, mock_auth, client):
        """
        Test POST /api/cart/find-and-add with missing furniture type.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.post("/api/cart/find-and-add", json={"quantity": 1})
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    def test_remove_from_cart_success(self, mock_auth, client):
        """
        Test DELETE /api/cart/remove/<furniture_id> successfully removes an item.

        Should call remove_item on the shopping cart.
        """
        dummy = dummy_user()
        dummy.shopping_cart.remove_item.return_value = True
        mock_auth.return_value = dummy
        response = client.delete("/api/cart/remove/furn1?quantity=2")
        assert response.status_code == 200
        dummy.shopping_cart.remove_item.assert_called_with("furn1", 2)

    @patch("app.routes.get_authenticated_user")
    def test_remove_from_cart_not_found(self, mock_auth, client):
        """
        Test DELETE /api/cart/remove/<furniture_id> when item removal fails.

        Should return a 404 status code.
        """
        dummy = dummy_user()
        dummy.shopping_cart.remove_item.return_value = False
        mock_auth.return_value = dummy
        response = client.delete("/api/cart/remove/furn1")
        assert response.status_code == 404

    @patch("app.routes.get_authenticated_user")
    def test_clear_cart(self, mock_auth, client):
        """
        Test DELETE /api/cart/clear successfully clears the cart.

        Should call the clear method on the shopping cart.
        """
        dummy = dummy_user()
        mock_auth.return_value = dummy
        response = client.delete("/api/cart/clear")
        assert response.status_code == 200
        dummy.shopping_cart.clear.assert_called()

    @patch("app.routes.get_authenticated_user")
    def test_apply_discount_percentage(self, mock_auth, client):
        """
        Test POST /api/cart/discount applying a percentage discount.

        Validates that the discount amount is returned.
        """
        dummy = dummy_user()
        dummy.shopping_cart.get_subtotal.return_value = 200
        dummy.shopping_cart.get_total.return_value = 180
        mock_auth.return_value = dummy

        # FIX: use "discountstrategy" to match the route
        payload = {"discountstrategy": "percentage", "value": 10}

        response = client.post("/api/cart/discount", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert "discount_amount" in data

    @patch("app.routes.get_authenticated_user")
    def test_apply_discount_fixed(self, mock_auth, client):
        """
        Test POST /api/cart/discount applying a fixed discount.

        Validates that the discount amount matches the fixed value.
        """
        dummy = dummy_user()
        dummy.shopping_cart.get_subtotal.return_value = 200
        dummy.shopping_cart.get_total.return_value = 150
        mock_auth.return_value = dummy
        payload = {"discountstrategy": "fixed", "value": 50}
        response = client.post("/api/cart/discount", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["discount_amount"] == 50

    @patch("app.routes.get_authenticated_user")
    def test_apply_discount_invalid_type(self, mock_auth, client):
        """
        Test POST /api/cart/discount with an invalid discount type.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        payload = {"discountstrategy": "invalid", "value": 10}
        response = client.post("/api/cart/discount", json=payload)
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    def test_apply_discount_no_data(self, mock_auth, client):
        """
        Test POST /api/cart/discount with no data provided.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.post("/api/cart/discount", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "No data provided" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_apply_discount_missing_fields(self, mock_auth, client):
        """
        Test POST /api/cart/discount with missing discount type or value.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        # Missing discount type.
        response = client.post("/api/cart/discount", json={"value": 10})
        assert response.status_code == 400
        data = response.get_json()
        assert "Missing discount type or value" in data["error"]

        # Missing discount value.
        response = client.post("/api/cart/discount", json={"type": "fixed"})
        assert response.status_code == 400
        data = response.get_json()
        assert "Missing discount type or value" in data["error"]

    # Exception branches for /cart/add /cart/find-and-add,
    # /cart/remove, /cart/clear, /cart/discount

    @patch("app.routes.get_authenticated_user")
    def test_add_to_cart_auth_error(self, mock_auth, client):
        """
        Test POST /api/cart/add when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        payload = {"furniture_id": "furn1", "quantity": 1}
        response = client.post("/api/cart/add", json=payload)
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_add_to_cart_value_error(self, mock_auth, client):
        """
        Test POST /api/cart/add with non-numeric quantity causing a ValueError.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        payload = {"furniture_id": "furn1", "quantity": "non-numeric"}
        response = client.post("/api/cart/add", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "invalid literal" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_add_to_cart_generic_exception(self, mock_auth, client):
        """
        Test POST /api/cart/add where a generic exception is raised.

        Should return a 500 status code.
        """
        dummy = dummy_user()
        mock_auth.return_value = dummy
        from app.routes import inventory

        with patch.object(
            inventory, "get_furniture", side_effect=Exception("Generic error")
        ):
            payload = {"furniture_id": "furn1", "quantity": 1}
            response = client.post("/api/cart/add", json=payload)
            assert response.status_code == 500
            data = response.get_json()
            assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_find_and_add_no_data(self, mock_auth, client):
        """
        Test POST /api/cart/find-and-add with no data provided.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.post("/api/cart/find-and-add", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "No data provided" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_find_and_add_missing_type(self, mock_auth, client):
        """
        Test POST /api/cart/find-and-add with missing furniture type.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        payload = {"quantity": 1, "color": "red"}
        response = client.post("/api/cart/find-and-add", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "Missing furniture type" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_find_and_add_auth_error(self, mock_auth, client):
        """
        Test POST /api/cart/find-and-add when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        payload = {"type": "chair", "quantity": 1}
        response = client.post("/api/cart/find-and-add", json=payload)
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_find_and_add_value_error(self, mock_auth, client):
        """
        Test POST /api/cart/find-and-add with non-numeric quantity causing a ValueError.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        payload = {"type": "chair", "quantity": "non-numeric"}
        response = client.post("/api/cart/find-and-add", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "invalid literal" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_find_and_add_generic_exception(self, mock_auth, client):
        """
        Test POST /api/cart/find-and-add where a generic exception is raised.

        Should return a 500 status code.
        """
        dummy = dummy_user()
        mock_auth.return_value = dummy
        from app.routes import cart_locator

        with patch.object(
            cart_locator, "find_and_add_to_cart", side_effect=Exception("Generic error")
        ):
            payload = {"name": "chair", "quantity": 1, "color": "red"}
            response = client.post("/api/cart/find-and-add", json=payload)
            assert response.status_code == 500
            data = response.get_json()
            assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_remove_from_cart_auth_error(self, mock_auth, client):
        """
        Test DELETE /api/cart/remove/<furniture_id> when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        response = client.delete("/api/cart/remove/furn1?quantity=2")
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_remove_from_cart_value_error(self, mock_auth, client):
        """
        Test DELETE /api/cart/remove/<furniture_id>
        with non-numeric quantity causing a ValueError.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.delete("/api/cart/remove/furn1?quantity=nonnumeric")
        assert response.status_code == 400
        data = response.get_json()
        assert "invalid literal" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_remove_from_cart_generic_exception(self, mock_auth, client):
        """
        Test DELETE /api/cart/remove/<furniture_id>
        where remove_item raises a generic Exception.

        Should return a 500 status code.
        """
        dummy = dummy_user()
        dummy.shopping_cart.remove_item.side_effect = Exception("Generic error")
        mock_auth.return_value = dummy
        response = client.delete("/api/cart/remove/furn1?quantity=2")
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_clear_cart_auth_error(self, mock_auth, client):
        """
        Test DELETE /api/cart/clear when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        response = client.delete("/api/cart/clear")
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_clear_cart_generic_exception(self, mock_auth, client):
        """
        Test DELETE /api/cart/clear where clear raises a generic Exception.

        Should return a 500 status code.
        """
        dummy = dummy_user()
        dummy.shopping_cart.clear.side_effect = Exception("Generic error")
        mock_auth.return_value = dummy
        response = client.delete("/api/cart/clear")
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_get_cart_auth_error(self, mock_auth, client):
        """
        Test GET /api/cart when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        response = client.get("/api/cart")
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_get_cart_generic_exception(self, mock_auth, client):
        """
        Test GET /api/cart when get_total raises a generic Exception.

        Should return a 500 status code.
        """
        dummy = dummy_user()
        mock_auth.return_value = dummy
        dummy.shopping_cart.get_total.side_effect = Exception("Generic error")
        response = client.get("/api/cart")
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_apply_discount_auth_error(self, mock_auth, client):
        """
        Test POST /api/cart/discount when authentication fails.

        Should return a 401 status code.
        """
        mock_auth.side_effect = AuthenticationError("Auth error")
        payload = {"type": "percentage", "value": 10}
        response = client.post("/api/cart/discount", json=payload)
        assert response.status_code == 401
        data = response.get_json()
        assert "Auth error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_apply_discount_value_error(self, mock_auth, client):
        """
        Test POST /api/cart/discount with non-numeric
        discount value causing a ValueError.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        payload = {"discountstrategy": "percentage", "value": "invalid"}
        response = client.post("/api/cart/discount", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert (
            "could not convert" in data["error"] or "invalid literal" in data["error"]
        )

    @patch("app.routes.get_authenticated_user")
    def test_apply_discount_generic_exception(self, mock_auth, client):
        """
        Test POST /api/cart/discount when get_total raises a generic Exception.

        Should return a 500 status code.
        """
        dummy = dummy_user()
        mock_auth.return_value = dummy
        dummy.shopping_cart.get_total.side_effect = Exception("Generic error")
        payload = {"discountstrategy": "fixed", "value": 10}
        response = client.post("/api/cart/discount", json=payload)
        assert response.status_code == 500
        data = response.get_json()
        assert "Generic error" in data["error"]

    @patch("app.routes.get_authenticated_user")
    def test_add_to_cart_no_data(self, mock_auth, client):
        """
        Test POST /api/cart/add with an empty JSON object.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.post("/api/cart/add", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "No data provided" in data["error"]


# =============================================================================
# Checkout & Orders Routes Tests
# =============================================================================


class TestCheckoutOrdersRoutes:
    """Tests for checkout and order routes."""

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.checkout_system.process_checkout")
    @patch("app.routes.PaymentMethod", return_value=MagicMock(value="CreditCard"))
    def test_process_checkout_valid(
        self, mock_payment_method, mock_checkout, mock_auth, client
    ):
        """
        Test POST /api/checkout with valid payment method.

        Should return a 201 status code and order details.
        """
        dummy = dummy_user()
        mock_auth.return_value = dummy
        dummy_order = MagicMock()
        dummy_order.order_id = "order1"
        dummy_order.user_id = dummy.id
        dummy_order.total_price = 100
        dummy_order.payment_method = MagicMock(value="CreditCard")
        dummy_order.date.isoformat.return_value = "2025-03-08T00:00:00"
        dummy_order.items = [1, 2]
        mock_checkout.return_value = dummy_order
        payload = {"payment_method": "CreditCard"}
        response = client.post("/api/checkout", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["order_id"] == "order1"

    @patch("app.routes.get_authenticated_user")
    def test_process_checkout_invalid_payment(self, mock_auth, client):
        """
        Test POST /api/checkout with an invalid payment method.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        payload = {"payment_method": "InvalidMethod"}
        response = client.post("/api/checkout", json=payload)
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    def test_process_checkout_no_data(self, mock_auth, client):
        """
        Test POST /api/checkout with no data provided.

        Should return a 400 status code.
        """
        mock_auth.return_value = dummy_user()
        response = client.post("/api/checkout", json={})
        assert response.status_code == 400

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.order_manager.get_user_orders")
    def test_get_user_orders(self, mock_get_orders, mock_auth, client):
        """
        Test GET /api/orders returns the orders for the authenticated user.

        Should return a 200 status code and a list of orders.
        """
        dummy = dummy_user()
        dummy.id = "user1"
        mock_auth.return_value = dummy
        orders = [{"order_id": "order1"}]
        mock_get_orders.return_value = orders
        response = client.get("/api/orders")
        assert response.status_code == 200
        data = response.get_json()
        assert data == orders

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.order_manager.get_order")
    def test_get_order_details_success(self, mock_get_order, mock_auth, client):
        """
        Test GET /api/orders/<order_id> for a valid order.

        Should return a 200 status code with order details.
        """
        dummy = dummy_user()
        dummy.id = "user1"
        mock_auth.return_value = dummy
        order = {"order_id": "order1", "user_id": "user1"}
        mock_get_order.return_value = order
        response = client.get("/api/orders/order1")
        assert response.status_code == 200
        data = response.get_json()
        assert data["order_id"] == "order1"

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.order_manager.get_order")
    def test_get_order_details_not_found(self, mock_get_order, mock_auth, client):
        """
        Test GET /api/orders/<order_id> when the order is not found.

        Should return a 404 status code.
        """
        dummy = dummy_user()
        dummy.id = "user1"
        mock_auth.return_value = dummy
        mock_get_order.return_value = None
        response = client.get("/api/orders/nonexistent")
        assert response.status_code == 404

    @patch("app.routes.get_authenticated_user")
    @patch("app.routes.order_manager.get_order")
    def test_get_order_details_access_denied(self, mock_get_order, mock_auth, client):
        """
        Test GET /api/orders/<order_id> when the order does not belong to the user.

        Should return a 403 status code.
        """
        dummy = dummy_user()
        dummy.id = "user1"
        mock_auth.return_value = dummy
        order = {"order_id": "order1", "user_id": "otheruser"}
        mock_get_order.return_value = order
        response = client.get("/api/orders/order1")
        assert response.status_code == 403

    @patch("app.routes.get_authenticated_user")
    def test_process_checkout_missing_payment_method(self, mock_auth, client):
        """
        Test POST /api/checkout when payment_method is missing.

        Should return a 400 status code with an error message.
        """
        mock_auth.return_value = dummy_user()
        response = client.post("/api/checkout", json={"some": "data"})
        assert response.status_code == 400
        data = response.get_json()
        assert "Missing payment method" in data["error"]


# Parameterized test for checkout exception branches
@pytest.mark.parametrize(
    "auth_exception, payment_exception, checkout_exception,\
        expected_status, expected_error_substring",
    [
        (AuthenticationError("Test auth error"), None, None, 401, "Test auth error"),
        (None, ValueError("Test ValueValue"), None, 400, "Invalid payment method."),
        (None, None, Exception("Generic error"), 500, "Generic error"),
        (None, None, ValueError("Test outer ValueError"), 400, "Test outer ValueError"),
    ],
)
@patch("app.routes.checkout_system.process_checkout")
@patch("app.routes.PaymentMethod")
@patch("app.routes.get_authenticated_user")
def test_process_checkout_exceptions(
    mock_get_authenticated_user,
    mock_payment_method,
    mock_checkout,
    client,
    auth_exception,
    payment_exception,
    checkout_exception,
    expected_status,
    expected_error_substring,
):
    """
    Parameterized test for POST /api/checkout that covers various exception scenarios.

    Depending on which exception is raised in authentication, payment method,
    or checkout processing, the endpoint should return
    the expected status code and error message.
    """
    if auth_exception:
        mock_get_authenticated_user.side_effect = auth_exception
    else:
        mock_get_authenticated_user.return_value = dummy_user()

    if payment_exception:
        mock_payment_method.side_effect = payment_exception
    else:
        dummy_payment = MagicMock()
        dummy_payment.value = "CreditCard"
        mock_payment_method.return_value = dummy_payment

    if checkout_exception:
        mock_checkout.side_effect = checkout_exception

    payload = {"payment_method": "CreditCard"}
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == expected_status
    data = response.get_json()
    assert expected_error_substring in data["error"]


# =============================================================================
# Enum Routes Tests
# =============================================================================


@pytest.mark.parametrize(
    "url",
    [
        "/api/enums/payment-methods",
        "/api/enums/chair-materials",
        "/api/enums/table-shapes",
        "/api/enums/furniture-sizes",
        "/api/enums/sofa-colors",
        "/api/enums/bed-sizes",
    ],
)
def test_enum_routes(client, url):
    """
    Test various enum routes to ensure they return a list.

    Should return a 200 status code and the response data must be a list.
    """
    response = client.get(url)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


# =============================================================================
# Helper Function Tests
# =============================================================================


def test_get_authenticated_user_valid():
    """
    Test that a valid 'Authorization' header returns a user.

    Patches the authenticate_with_token method to return a dummy user.
    """
    app = Flask(__name__)
    with app.test_request_context("/", headers={"Authorization": "Bearer validtoken"}):
        dummy_user_obj = MagicMock()
        dummy_user_obj.id = "user1"
        with patch(
            "app.routes.user_manager.authenticate_with_token",
            return_value=dummy_user_obj,
        ) as mock_auth:
            user = get_authenticated_user()
            assert user.id == "user1"
            mock_auth.assert_called_once_with("validtoken")


def test_get_authenticated_user_missing_header():
    """
    Test that a missing Authorization header raises an AuthenticationError.
    """
    app = Flask(__name__)
    with app.test_request_context("/"):
        with pytest.raises(AuthenticationError) as excinfo:
            get_authenticated_user()
        assert "Missing or invalid Authorization header" in str(excinfo.value)


def test_get_authenticated_user_invalid_header():
    """
    Test that an invalid Authorization header format raises an AuthenticationError.
    """
    app = Flask(__name__)
    with app.test_request_context(
        "/", headers={"Authorization": "InvalidToken sometoken"}
    ):
        with pytest.raises(AuthenticationError) as excinfo:
            get_authenticated_user()
        assert "Missing or invalid Authorization header" in str(excinfo.value)


def test_get_furniture_by_id_exception(client, mocker):
    """
    Test GET /api/furniture/<furniture_id>
    when inventory.get_furniture raises an exception.

    Should return a 500 status code.
    """
    mocker.patch(
        "app.routes.inventory.get_furniture", side_effect=Exception("Test error")
    )
    response = client.get("/api/furniture/123")
    assert response.status_code == 500
    data = response.get_json()
    assert "Test error" in data["error"]


def test_add_furniture_missing_required_fields(client, mocker):
    """
    Test POST /api/furniture with missing required fields.

    Should return a 400 status code with an appropriate error message.
    """
    mocker.patch("app.routes.get_authenticated_user", return_value=dummy_user())
    payload = {
        "name": "",
        "quantity": 2,
        "material": "wood",
        "description": "A comfy chair",
    }
    response = client.post("/api/furniture", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "Missing one of the required fields: name, price, description" in data["error"]


def test_get_order_details_auth_error(client, mocker):
    """
    Test GET /api/orders/<order_id> when authentication fails.

    Should return a 401 status code.
    """
    mocker.patch(
        "app.routes.get_authenticated_user",
        side_effect=AuthenticationError("Auth error"),
    )
    response = client.get("/api/orders/someorder")
    assert response.status_code == 401
    data = response.get_json()
    assert "Auth error" in data["error"]


def test_get_order_details_exception(client, mocker):
    """
    Test GET /api/orders/<order_id> when order_manager.get_order raises an exception.

    Should return a 500 status code.
    """
    dummy = dummy_user()
    mocker.patch("app.routes.get_authenticated_user", return_value=dummy)
    mocker.patch(
        "app.routes.order_manager.get_order", side_effect=Exception("Test error")
    )
    response = client.get("/api/orders/someorder")
    assert response.status_code == 500
    data = response.get_json()
    assert "Test error" in data["error"]


def test_get_user_orders_auth_error(client, mocker):
    """
    Test GET /api/orders when authentication fails.

    Should return a 401 status code.
    """
    mocker.patch(
        "app.routes.get_authenticated_user",
        side_effect=AuthenticationError("Auth error"),
    )
    response = client.get("/api/orders")
    assert response.status_code == 401
    data = response.get_json()
    assert "Auth error" in data["error"]


def test_get_user_orders_exception(client, mocker):
    """
    Test GET /api/orders when order_manager.get_user_orders raises an exception.

    Should return a 500 status code.
    """
    dummy = dummy_user()
    mocker.patch("app.routes.get_authenticated_user", return_value=dummy)
    mocker.patch(
        "app.routes.order_manager.get_user_orders", side_effect=Exception("Test error")
    )
    response = client.get("/api/orders")
    assert response.status_code == 500
    data = response.get_json()
    assert "Test error" in data["error"]