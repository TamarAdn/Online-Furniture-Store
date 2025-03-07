"""API routes for the furniture store application."""

from typing import Any, Dict, List, Tuple

from flask import Blueprint, Response, jsonify, request

from app.models.cart_item_locator import CartItemLocator
from app.models.checkout_system import CheckoutSystem
from app.models.discount_strategy import (
    FixedAmountDiscountStrategy,
    PercentageDiscountStrategy,
)
from app.models.enums import (
    BedSize,
    ChairMaterial,
    FurnitureSize,
    PaymentMethod,
    SofaColor,
    TableShape,
)
from app.models.furniture import Bed, Bookcase, Chair, Sofa, Table
from app.models.inventory import Inventory
from app.models.jwt_manager import JWTManager
from app.models.order_manager import OrderManager
from app.models.search_strategy import (
    AttributeSearchStrategy,
    NameSearchStrategy,
    PriceRangeSearchStrategy,
)
from app.models.user import User
from app.models.user_database import UserDatabase
from app.models.user_manager import UserManager
from app.utils import AuthenticationError

# Create Blueprint for API routes
api = Blueprint("api", __name__, url_prefix="/api")

# Initialize required services
inventory = Inventory()
order_manager = OrderManager()
user_db = UserDatabase()
jwt_manager = JWTManager()
user_manager = UserManager(user_db, jwt_manager)
checkout_system = CheckoutSystem(inventory, order_manager)
cart_locator = CartItemLocator(inventory)

# ----- Authentication Middleware -----


def get_authenticated_user() -> User:
    """Extract and validate JWT token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]
    return user_manager.authenticate_with_token(token)


# ----- Furniture Routes -----


@api.route("/furniture", methods=["GET"])
def get_all_furniture() -> Tuple[Response, int]:
    """Get furniture items with optional filtering."""
    try:
        # Get query parameters for filtering
        name_filter = request.args.get("name")
        min_price = request.args.get("min_price")
        max_price = request.args.get("max_price")
        furniture_type = request.args.get("type")

        # Choose search strategy based on query parameters
        if name_filter:
            search_strategy = NameSearchStrategy(name_filter)
            search_results = inventory.search(search_strategy)
        elif min_price or max_price:
            try:
                min_price_float = float(min_price) if min_price else 0
                max_price_float = float(max_price) if max_price else float("inf")
                search_strategy = PriceRangeSearchStrategy(
                    min_price_float, max_price_float
                )
                search_results = inventory.search(search_strategy)
            except ValueError:
                return jsonify({"error": "Invalid price format"}), 400
        elif furniture_type:
            # Search by furniture class name
            search_strategy = AttributeSearchStrategy(
                "__class__.__name__", furniture_type.capitalize()
            )
            search_results = inventory.search(search_strategy)
        else:
            # No filters, get all furniture
            search_results = inventory.get_all_furniture()

        # Convert to serializable format
        result: List[Dict[str, Any]] = []
        for item in search_results:
            furniture_dict = item["furniture"].to_dict()
            furniture_dict["quantity"] = item["quantity"]
            result.append(furniture_dict)

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/furniture/<furniture_id>", methods=["GET"])
def get_furniture_by_id(furniture_id: str) -> Tuple[Response, int]:
    """Get a specific furniture item by ID."""
    try:
        furniture = inventory.get_furniture(furniture_id)
        if not furniture:
            return jsonify({"error": "Furniture not found"}), 404

        furniture_dict = furniture.to_dict()
        furniture_dict["quantity"] = inventory.get_quantity(furniture_id)

        return jsonify(furniture_dict), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/furniture", methods=["POST"])
def add_furniture() -> Tuple[Response, int]:
    """Add a new furniture item to inventory."""
    try:
        # Get authenticated user (admin check could be added here)
        get_authenticated_user()

        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        furniture_type = data.get("type", "").lower()
        price = data.get("price")
        quantity = data.get("quantity", 1)

        if not furniture_type or price is None:
            return jsonify({"error": "Missing required fields: type, price"}), 400

        # Create furniture object based on type
        try:
            if furniture_type == "chair":
                material = data.get("material")
                furniture = Chair(
                    price=float(price),
                    material=material,
                    description=data.get("description", ""),
                )

            elif furniture_type == "table":
                shape = data.get("shape")
                size = data.get("size", "medium")
                furniture = Table(
                    price=float(price),
                    shape=shape,
                    size=size,
                    description=data.get("description", ""),
                )

            elif furniture_type == "sofa":
                seats = data.get("seats", 3)
                color = data.get("color", "gray")
                furniture = Sofa(
                    price=float(price),
                    seats=int(seats),
                    color=color,
                    description=data.get("description", ""),
                )

            elif furniture_type == "bed":
                size = data.get("size")
                furniture = Bed(
                    price=float(price),
                    size=size,
                    description=data.get("description", ""),
                )

            elif furniture_type == "bookcase":
                shelves = data.get("shelves")
                size = data.get("size", "medium")
                furniture = Bookcase(
                    price=float(price),
                    shelves=int(shelves),
                    size=size,
                    description=data.get("description", ""),
                )

            else:
                return (
                    jsonify({"error": f"Unsupported furniture type: {furniture_type}"}),
                    400,
                )

            # Add to inventory
            furniture_id = inventory.add_furniture(furniture, int(quantity))

            # Return created furniture with ID
            result = furniture.to_dict()
            result["id"] = furniture_id  # Add the ID to the response
            result["quantity"] = quantity

            return jsonify(result), 201

        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/furniture/<furniture_id>", methods=["PUT"])
def update_furniture_quantity(furniture_id: str) -> Tuple[Response, int]:
    """Update a furniture item's quantity."""
    try:
        # Get authenticated user (admin check could be added here)
        get_authenticated_user()

        data = request.json
        if not data or "quantity" not in data:
            return jsonify({"error": "No quantity provided"}), 400

        quantity = int(data["quantity"])

        # Update inventory
        success = inventory.update_quantity(furniture_id, quantity)

        if not success:
            return jsonify({"error": "Furniture not found"}), 404

        return jsonify({"message": "Quantity updated successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/furniture/<furniture_id>", methods=["DELETE"])
def remove_furniture(furniture_id: str) -> Tuple[Response, int]:
    """Remove a furniture item from inventory."""
    try:
        # Get authenticated user (admin check could be added here)
        get_authenticated_user()

        # Remove from inventory
        success = inventory.remove_furniture(furniture_id)

        if not success:
            return jsonify({"error": "Furniture not found"}), 404

        return jsonify({"message": "Furniture removed successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----- User Routes -----


@api.route("/users/register", methods=["POST"])
def register_user() -> Tuple[Response, int]:
    """Register a new user."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Required fields
        username = data.get("username")
        full_name = data.get("full_name")
        email = data.get("email")
        password = data.get("password")
        shipping_address = data.get("shipping_address")

        if not all([username, full_name, email, password]):
            return jsonify({"error": "Missing required fields"}), 400

        # Register user
        user = user_manager.register_user(
            username=username,
            full_name=full_name,
            email=email,
            password=password,
            shipping_address=shipping_address,
        )

        # Return user data (without sensitive info)
        return (
            jsonify(
                {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "shipping_address": user.shipping_address,
                }
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/users/login", methods=["POST"])
def login_user() -> Tuple[Response, int]:
    """Authenticate a user and get tokens."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        username_or_email = data.get("username") or data.get("email")
        password = data.get("password")

        if not username_or_email or not password:
            return jsonify({"error": "Missing username/email or password"}), 400

        # Authenticate user
        user, tokens = user_manager.login(username_or_email, password)

        # Return tokens and basic user info
        return (
            jsonify(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "email": user.email,
                    },
                    "tokens": tokens,
                }
            ),
            200,
        )

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/users/refresh-token", methods=["POST"])
def refresh_token() -> Tuple[Response, int]:
    """Refresh access token using refresh token."""
    try:
        data = request.json
        if not data or "refresh_token" not in data:
            return jsonify({"error": "No refresh token provided"}), 400

        # Get new access token
        new_access_token = user_manager.refresh_access_token(data["refresh_token"])

        return jsonify({"access_token": new_access_token, "token_type": "Bearer"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/users/profile", methods=["GET"])
def get_user_profile() -> Tuple[Response, int]:
    """Get the authenticated user's profile."""
    try:
        user = get_authenticated_user()

        return (
            jsonify(
                {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "shipping_address": user.shipping_address,
                }
            ),
            200,
        )

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/users/profile", methods=["PUT"])
def update_user_profile() -> Tuple[Response, int]:
    """Update the authenticated user's profile."""
    try:
        user = get_authenticated_user()
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Update user fields
        full_name = data.get("full_name")
        email = data.get("email")
        shipping_address = data.get("shipping_address")

        # Attempt update
        success = user_manager.update_user(
            username=user.username,
            full_name=full_name,
            email=email,
            shipping_address=shipping_address,
        )

        if not success:
            return jsonify({"error": "Profile update failed"}), 400

        return jsonify({"message": "Profile updated successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/users/password", methods=["PUT"])
def update_password() -> Tuple[Response, int]:
    """Update the authenticated user's password."""
    try:
        user = get_authenticated_user()
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not current_password or not new_password:
            return jsonify({"error": "Missing current or new password"}), 400

        # Attempt password update
        success = user_manager.update_password(
            username=user.username,
            current_password=current_password,
            new_password=new_password,
        )

        if not success:
            return jsonify({"error": "Password update failed"}), 400

        return jsonify({"message": "Password updated successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/users/logout", methods=["POST"])
def logout_user() -> Tuple[Response, int]:
    """Log out the current user (invalidate token)."""
    try:
        user = get_authenticated_user()

        # Logout user
        user_manager.logout(user)

        return jsonify({"message": "Logged out successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----- Shopping Cart Routes -----


@api.route("/cart", methods=["GET"])
def get_cart() -> Tuple[Response, int]:
    """Get the contents of the authenticated user's shopping cart."""
    try:
        user = get_authenticated_user()

        # Get cart items
        cart_items = user.view_cart()

        # Transform to serializable format
        items: List[Dict[str, Any]] = []
        for furniture, quantity in cart_items:
            furniture_dict = furniture.to_dict()
            furniture_dict["quantity"] = quantity
            items.append(furniture_dict)

        # Calculate totals
        subtotal = user.shopping_cart.get_subtotal()
        total = user.shopping_cart.get_total()

        return (
            jsonify(
                {
                    "items": items,
                    "subtotal": subtotal,
                    "total": total,
                    "item_count": len(user.shopping_cart),
                }
            ),
            200,
        )

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/cart/add", methods=["POST"])
def add_to_cart() -> Tuple[Response, int]:
    """Add a furniture item to the cart using ID and quantity."""
    try:
        user = get_authenticated_user()
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        furniture_id = data.get("furniture_id")
        quantity = int(data.get("quantity", 1))

        if not furniture_id:
            return jsonify({"error": "Missing furniture_id"}), 400

        # Get furniture from inventory
        furniture = inventory.get_furniture(furniture_id)
        if not furniture:
            return jsonify({"error": "Furniture not found"}), 404

        # Add to cart
        user.shopping_cart.add_item(furniture, quantity)

        return jsonify({"message": "Item added to cart successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/cart/find-and-add", methods=["POST"])
def find_and_add_to_cart() -> Tuple[Response, int]:
    """Find and add furniture to cart using attributes instead of ID."""
    try:
        user = get_authenticated_user()
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        furniture_type = data.get("type")
        quantity = int(data.get("quantity", 1))

        if not furniture_type:
            return jsonify({"error": "Missing furniture type"}), 400

        # Get attributes from request (excluding type and quantity)
        attributes = {k: v for k, v in data.items() if k not in ["type", "quantity"]}

        # Use CartItemLocator to find and add item
        cart_locator.find_and_add_to_cart(
            user.shopping_cart, furniture_type, quantity, **attributes
        )

        return jsonify({"message": "Item added to cart successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/cart/remove/<furniture_id>", methods=["DELETE"])
def remove_from_cart(furniture_id: str) -> Tuple[Response, int]:
    """Remove a furniture item from the cart."""
    try:
        user = get_authenticated_user()

        # Get optional quantity parameter
        quantity = request.args.get("quantity")
        quantity_int = int(quantity) if quantity else None

        # Remove from cart
        success = user.shopping_cart.remove_item(furniture_id, quantity_int)

        if not success:
            return jsonify({"error": "Item not found in cart"}), 404

        return jsonify({"message": "Item removed from cart successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/cart/clear", methods=["DELETE"])
def clear_cart() -> Tuple[Response, int]:
    """Clear all items from the cart."""
    try:
        user = get_authenticated_user()

        # Clear cart
        user.shopping_cart.clear()

        return jsonify({"message": "Cart cleared successfully"}), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/cart/discount", methods=["POST"])
def apply_discount() -> Tuple[Response, int]:
    """Apply a discount to the cart."""
    try:
        user = get_authenticated_user()
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        discount_type = data.get("type")
        value = data.get("value")

        if not discount_type or value is None:
            return jsonify({"error": "Missing discount type or value"}), 400

        # Apply appropriate discount strategy
        if discount_type == "percentage":
            discount = PercentageDiscountStrategy(float(value))
        elif discount_type == "fixed":
            discount = FixedAmountDiscountStrategy(float(value))
        else:
            return jsonify({"error": "Invalid discount type"}), 400

        # Apply to cart
        user.shopping_cart.discount_strategy = discount

        # Get updated cart totals
        subtotal = user.shopping_cart.get_subtotal()
        total = user.shopping_cart.get_total()

        return (
            jsonify(
                {
                    "message": "Discount applied successfully",
                    "subtotal": subtotal,
                    "total": total,
                    "discount_amount": subtotal - total,
                }
            ),
            200,
        )

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----- Checkout & Order Routes -----


@api.route("/checkout", methods=["POST"])
def process_checkout() -> Tuple[Response, int]:
    """Process checkout and create an order."""
    try:
        user = get_authenticated_user()
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Get payment method
        payment_method_str = data.get("payment_method")
        if not payment_method_str:
            return jsonify({"error": "Missing payment method"}), 400

        # Validate payment method
        try:
            payment_method = PaymentMethod(payment_method_str)
        except ValueError:
            valid_methods = [method.value for method in PaymentMethod]
            return (
                jsonify(
                    {
                        "error": f"Invalid payment method."
                        f"Valid options are: {', '.join(valid_methods)}"
                    }
                ),
                400,
            )

        # Process checkout
        order = checkout_system.process_checkout(user, payment_method)

        # Return order details
        return (
            jsonify(
                {
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "total_price": order.total_price,
                    "payment_method": order.payment_method.value,
                    "date": order.date.isoformat(),
                    "items_count": len(order.items),
                }
            ),
            201,
        )

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/orders", methods=["GET"])
def get_user_orders() -> Tuple[Response, int]:
    """Get all orders for the authenticated user."""
    try:
        user = get_authenticated_user()

        # Get orders for the user
        orders = order_manager.get_user_orders(user.id)

        return jsonify(orders), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/orders/<order_id>", methods=["GET"])
def get_order_details(order_id: str) -> Tuple[Response, int]:
    """Get details for a specific order."""
    try:
        user = get_authenticated_user()

        # Get order
        order = order_manager.get_order(order_id)

        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Check if order belongs to user or if user is admin
        if order["user_id"] != user.id:
            return jsonify({"error": "Access denied"}), 403

        return jsonify(order), 200

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----- Helper Enum Routes -----


@api.route("/enums/payment-methods", methods=["GET"])
def get_payment_methods() -> Tuple[Response, int]:
    """Get all available payment methods."""
    methods = [{"value": method.value, "name": method.name} for method in PaymentMethod]
    return jsonify(methods), 200


@api.route("/enums/chair-materials", methods=["GET"])
def get_chair_materials() -> Tuple[Response, int]:
    """Get all available chair materials."""
    materials = [
        {"value": material.value, "name": material.name} for material in ChairMaterial
    ]
    return jsonify(materials), 200


@api.route("/enums/table-shapes", methods=["GET"])
def get_table_shapes() -> Tuple[Response, int]:
    """Get all available table shapes."""
    shapes = [{"value": shape.value, "name": shape.name} for shape in TableShape]
    return jsonify(shapes), 200


@api.route("/enums/furniture-sizes", methods=["GET"])
def get_furniture_sizes() -> Tuple[Response, int]:
    """Get all available furniture sizes."""
    sizes = [{"value": size.value, "name": size.name} for size in FurnitureSize]
    return jsonify(sizes), 200


@api.route("/enums/sofa-colors", methods=["GET"])
def get_sofa_colors() -> Tuple[Response, int]:
    """Get all available sofa colors."""
    colors = [{"value": color.value, "name": color.name} for color in SofaColor]
    return jsonify(colors), 200


@api.route("/enums/bed-sizes", methods=["GET"])
def get_bed_sizes() -> Tuple[Response, int]:
    """Get all available bed sizes."""
    sizes = [{"value": size.value, "name": size.name} for size in BedSize]
    return jsonify(sizes), 200
