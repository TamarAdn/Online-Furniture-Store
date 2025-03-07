import datetime

import pytest
from flask import Flask

from app.routes import api

# Dummy classes to simulate dependencies


class DummyFurniture:
    def __init__(
        self, id="dummy_furniture", price=100, description="Dummy Furniture", **kwargs
    ):
        self.id = id
        self.price = price
        self.description = description
        self.attributes = kwargs

    def to_dict(self):
        d = {"id": self.id, "price": self.price, "description": self.description}
        d.update(self.attributes)
        return d


class DummyShoppingCart:
    def __init__(self):
        self.items = []
        self.discount_strategy = None

    def add_item(self, furniture, quantity):
        self.items.append((furniture, quantity))

    def get_subtotal(self):
        return 100

    def get_total(self):
        return 90

    def __len__(self):
        return len(self.items)

    def clear(self):
        self.items = []

    def remove_item(self, furniture_id, quantity=None):
        for i, (furniture, qty) in enumerate(self.items):
            if furniture.id == furniture_id:
                del self.items[i]
                return True
        return False

    def view_cart(self):
        return self.items


class DummyUser:
    def __init__(self):
        self.id = "dummy_id"
        self.username = "dummy"
        self.full_name = "Dummy User"
        self.email = "dummy@example.com"
        self.shipping_address = "123 Dummy St"
        self.shopping_cart = DummyShoppingCart()

    # Added view_cart method to mimic real User behavior.
    def view_cart(self):
        return self.shopping_cart.view_cart()


def dummy_get_authenticated_user():
    return DummyUser()


# Flask app and test client fixtures


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# ----- Furniture Routes Tests -----


def test_get_all_furniture(client, monkeypatch):
    # Patch inventory.get_all_furniture to return a dummy furniture list
    def dummy_get_all_furniture():
        return [{"furniture": DummyFurniture(), "quantity": 5}]

    monkeypatch.setattr(
        "app.routes.inventory.get_all_furniture", dummy_get_all_furniture
    )

    response = client.get("/api/furniture")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "dummy_furniture"
    assert data[0]["quantity"] == 5


def test_get_furniture_by_id(client, monkeypatch):
    # Patch inventory.get_furniture and inventory.get_quantity
    def dummy_get_furniture(furniture_id):
        if furniture_id == "dummy_furniture":
            return DummyFurniture(id=furniture_id)
        return None

    def dummy_get_quantity(furniture_id):
        return 10 if furniture_id == "dummy_furniture" else 0

    monkeypatch.setattr("app.routes.inventory.get_furniture", dummy_get_furniture)
    monkeypatch.setattr("app.routes.inventory.get_quantity", dummy_get_quantity)

    response = client.get("/api/furniture/dummy_furniture")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "dummy_furniture"
    assert data["quantity"] == 10


def test_add_furniture(client, monkeypatch):
    # Patch authentication and inventory.add_furniture
    monkeypatch.setattr(
        "app.routes.get_authenticated_user", dummy_get_authenticated_user
    )

    def dummy_add_furniture(furniture, quantity):
        return "new_furniture_id"

    monkeypatch.setattr("app.routes.inventory.add_furniture", dummy_add_furniture)

    payload = {
        "type": "chair",
        "price": 150,
        "quantity": 2,
        "material": "wood",
        "description": "A wooden chair",
    }
    response = client.post("/api/furniture", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["price"] == 150
    assert data["description"] == "A wooden chair"
    assert data["quantity"] == 2


def test_update_furniture_quantity(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.get_authenticated_user", dummy_get_authenticated_user
    )
    monkeypatch.setattr("app.routes.inventory.update_quantity", lambda fid, qty: True)

    response = client.put("/api/furniture/dummy_furniture", json={"quantity": 10})
    assert response.status_code == 200
    data = response.get_json()
    assert "Quantity updated successfully" in data["message"]


def test_remove_furniture(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.get_authenticated_user", dummy_get_authenticated_user
    )
    monkeypatch.setattr("app.routes.inventory.remove_furniture", lambda fid: True)

    response = client.delete("/api/furniture/dummy_furniture")
    assert response.status_code == 200
    data = response.get_json()
    assert "Furniture removed successfully" in data["message"]


# ----- User Routes Tests -----


def test_register_user(client, monkeypatch):
    def dummy_register_user(username, full_name, email, password, shipping_address):
        user = DummyUser()
        user.id = "registered_user_id"
        user.username = username
        user.full_name = full_name
        user.email = email
        user.shipping_address = shipping_address
        return user

    monkeypatch.setattr("app.routes.user_manager.register_user", dummy_register_user)

    payload = {
        "username": "newuser",
        "full_name": "New User",
        "email": "newuser@example.com",
        "password": "securepassword",
        "shipping_address": "456 New St",
    }
    response = client.post("/api/users/register", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == "registered_user_id"
    assert data["username"] == "newuser"


def test_login_user(client, monkeypatch):
    def dummy_login(username_or_email, password):
        user = DummyUser()
        user.id = "login_user_id"
        tokens = {"access_token": "dummy_access", "refresh_token": "dummy_refresh"}
        return user, tokens

    monkeypatch.setattr("app.routes.user_manager.login", dummy_login)

    payload = {"username": "dummy", "password": "dummy_password"}
    response = client.post("/api/users/login", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["id"] == "login_user_id"
    assert "tokens" in data


def test_get_user_profile(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.get_authenticated_user", dummy_get_authenticated_user
    )
    response = client.get("/api/users/profile")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "dummy_id"


def test_logout_user(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.get_authenticated_user", dummy_get_authenticated_user
    )
    monkeypatch.setattr("app.routes.user_manager.logout", lambda user: None)
    response = client.post("/api/users/logout")
    assert response.status_code == 200
    data = response.get_json()
    assert "Logged out successfully" in data["message"]


# ----- Cart Routes Tests -----


def test_get_cart(client, monkeypatch):
    dummy_user = DummyUser()
    # Add an item so that view_cart() returns at least one item
    dummy_user.shopping_cart.add_item(DummyFurniture(), 1)
    monkeypatch.setattr("app.routes.get_authenticated_user", lambda: dummy_user)

    response = client.get("/api/cart")
    assert response.status_code == 200
    data = response.get_json()
    assert "items" in data
    assert data["subtotal"] == 100
    assert data["total"] == 90
    assert "item_count" in data


def test_add_to_cart(client, monkeypatch):
    dummy_user = DummyUser()
    monkeypatch.setattr("app.routes.get_authenticated_user", lambda: dummy_user)
    monkeypatch.setattr(
        "app.routes.inventory.get_furniture",
        lambda fid: DummyFurniture(id=fid) if fid == "dummy_furniture" else None,
    )

    payload = {"furniture_id": "dummy_furniture", "quantity": 2}
    response = client.post("/api/cart/add", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "Item added to cart successfully" in data["message"]


def test_remove_from_cart(client, monkeypatch):
    dummy_user = DummyUser()
    # Add an item first
    dummy_item = DummyFurniture(id="dummy_furniture")
    dummy_user.shopping_cart.add_item(dummy_item, 2)
    monkeypatch.setattr("app.routes.get_authenticated_user", lambda: dummy_user)

    response = client.delete("/api/cart/remove/dummy_furniture?quantity=1")
    assert response.status_code == 200
    data = response.get_json()
    assert "Item removed from cart successfully" in data["message"]


def test_clear_cart(client, monkeypatch):
    dummy_user = DummyUser()
    dummy_user.shopping_cart.add_item(DummyFurniture(), 1)
    monkeypatch.setattr("app.routes.get_authenticated_user", lambda: dummy_user)

    response = client.delete("/api/cart/clear")
    assert response.status_code == 200
    data = response.get_json()
    assert "Cart cleared successfully" in data["message"]


def test_apply_discount(client, monkeypatch):
    dummy_user = DummyUser()
    monkeypatch.setattr("app.routes.get_authenticated_user", lambda: dummy_user)

    payload = {"type": "percentage", "value": 10}
    response = client.post("/api/cart/discount", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "Discount applied successfully" in data["message"]
    # discount_amount should equal subtotal minus total (dummy values defined above)
    assert (
        data["discount_amount"]
        == dummy_user.shopping_cart.get_subtotal()
        - dummy_user.shopping_cart.get_total()
    )


# ----- Checkout & Order Routes Tests -----


def test_process_checkout(client, monkeypatch):
    dummy_user = DummyUser()
    monkeypatch.setattr("app.routes.get_authenticated_user", lambda: dummy_user)

    # Monkeypatch PaymentMethod so it doesn't raise ValueError.
    monkeypatch.setattr(
        "app.routes.PaymentMethod",
        lambda x: type("DummyPaymentMethod", (), {"value": x}),
    )

    # Create a dummy order object
    class DummyOrder:
        order_id = "order123"
        user_id = dummy_user.id
        total_price = 100
        payment_method = type("DummyPaymentMethod", (), {"value": "credit_card"})
        date = datetime.datetime.now()
        items = [("item1", 1)]

    monkeypatch.setattr(
        "app.routes.checkout_system.process_checkout", lambda user, pm: DummyOrder()
    )

    payload = {"payment_method": "credit_card"}
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["order_id"] == "order123"


def test_get_user_orders(client, monkeypatch):
    dummy_user = DummyUser()
    monkeypatch.setattr("app.routes.get_authenticated_user", lambda: dummy_user)
    monkeypatch.setattr(
        "app.routes.order_manager.get_user_orders",
        lambda user_id: [{"order_id": "order1", "user_id": dummy_user.id}],
    )

    response = client.get("/api/orders")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data[0]["order_id"] == "order1"


def test_get_order_details(client, monkeypatch):
    dummy_user = DummyUser()

    def monkeypatch_user():
        return dummy_user

    monkeypatch.setattr("app.routes.get_authenticated_user", monkeypatch_user)
    dummy_order = {"order_id": "order123", "user_id": dummy_user.id, "items": []}
    monkeypatch.setattr(
        "app.routes.order_manager.get_order",
        lambda oid: dummy_order if oid == "order123" else None,
    )

    response = client.get("/api/orders/order123")
    assert response.status_code == 200
    data = response.get_json()
    assert data["order_id"] == "order123"


# ----- Helper Enum Routes Tests -----


def test_get_payment_methods(client):
    response = client.get("/api/enums/payment-methods")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # At least one payment method should be returned.
    assert len(data) > 0


def test_get_chair_materials(client):
    response = client.get("/api/enums/chair-materials")
    assert response.status_code == 200


def test_get_table_shapes(client):
    response = client.get("/api/enums/table-shapes")
    assert response.status_code == 200


def test_get_furniture_sizes(client):
    response = client.get("/api/enums/furniture-sizes")
    assert response.status_code == 200


def test_get_sofa_colors(client):
    response = client.get("/api/enums/sofa-colors")
    assert response.status_code == 200


def test_get_bed_sizes(client):
    response = client.get("/api/enums/bed-sizes")
    assert response.status_code == 200
