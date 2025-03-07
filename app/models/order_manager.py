from typing import Any, Dict, List, Optional, cast

from app.config import ORDERS_FILE
from app.utils import JsonFileManager


class OrderManager:
    """
    Manages order operations including saving, retrieving, and querying orders.

    This class handles the persistence of order data to a JSON file and provides
    methods to interact with the order database. It handles serialization of order
    objects to JSON format and provides query capabilities by order ID and user ID.

    Attributes:
        _file_path (str): Path to the JSON file used for storing orders.
                         Defaults to the value defined in ORDERS_FILE.
    """

    def __init__(self, file_path: str = ORDERS_FILE) -> None:
        self._file_path = file_path
        JsonFileManager.ensure_file_exists(file_path)

    def save_order(self, order: Any) -> bool:
        """
        Save order to orders.json file.

        Args:
            order: An order object with required attributes for serialization.

        Returns:
            bool: True if the order was successfully saved.

        Raises:
            AttributeError: If the order object is missing required attributes.
            TypeError: If the file contents cannot be processed.
        """
        orders = cast(List[Dict[str, Any]], JsonFileManager.read_json(self._file_path))

        # Convert order to serializable format
        order_data: Dict[str, Any] = {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "date": order.date.isoformat(),
            "total_price": order.total_price,
            "payment_method": order.payment_method.value,
            "shipping_address": order.shipping_address,
            "items": [
                {
                    "furniture_id": item[0].id,
                    "name": item[0].name,
                    "quantity": item[1],
                    "unit_price": item[0].get_final_price(),
                }
                for item in order.items
            ],
        }
        orders.append(order_data)
        JsonFileManager.write_json(self._file_path, orders)
        return True

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order by ID.

        Args:
            order_id: The ID of the order to retrieve.

        Returns:
            The order dictionary if found, None otherwise.

        Raises:
            TypeError: If the file contents cannot be processed.
        """
        orders = cast(List[Dict[str, Any]], JsonFileManager.read_json(self._file_path))

        if not isinstance(orders, list):
            raise TypeError("Expected orders data to be a list")

        for order in orders:
            if order["order_id"] == order_id:
                return order
        return None

    def get_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all orders for a specific user.

        Args:
            user_id: The ID of the user whose orders to retrieve.

        Returns:
            A list of order dictionaries belonging to the user.

        Raises:
            TypeError: If the file contents cannot be processed.
        """
        orders = cast(List[Dict[str, Any]], JsonFileManager.read_json(self._file_path))

        if not isinstance(orders, list):
            raise TypeError("Expected orders data to be a list")

        return [order for order in orders if order["user_id"] == user_id]
