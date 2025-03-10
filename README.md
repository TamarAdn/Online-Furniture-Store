# Online-Furniture-Store

A backend system for an online furniture store, providing a RESTful API for inventory management, user authentication, shopping cart functionality, and order processing, built with Flask. This project focuses on backend logic only, without a user interface.

## **Project Description**
This project implements a complete backend for an online furniture store. It supports user authentication, inventory management, a shopping cart system with discount functionality, and order processing—all exposed via a well-structured RESTful API.

### **User Management**  
- **JWT authentication** with **bcrypt password hashing**.  
- **User registration, login, and profile updates** (name, email, address).  
- **Shopping cart & favorites management**.  
- **Users can view past orders and their statuses.**  

### **Furniture Inventory Management**  
- **Singleton-based inventory system** with **five furniture types**.  
- Handles adding, updating, and removing furniture items.  
 
### **Shopping Cart System**  
- **Add, remove, and update items** 
- **Discount strategies**: No discount, percentage-based, and fixed amount.  
- **CartItemLocator** allows adding items by attributes (e.g., color, material) and description keywords, enabling partial matches with furniture descriptions (e.g., "office" or "coffee table").
- **Cart auto-clears** after checkout.  

### **Order & Checkout Management**  
- **Inventory validation & stock updates** before order processing.  
- **Supports multiple payment methods** (Enum-based).  
- **Mock payment processing** with final cart clearance.  

### **Advanced Search System**  
- Uses the **Strategy Pattern** for flexible furniture searches:  
  - **Search by Name** (case-insensitive) - filtering by **furniture type** (Chair, Sofa, Table, etc.).
  - **Search by Price Range**.  
  - **Search by Specific Attributes** (e.g., color, material, size).  

### **Enumerations for Standardization**  
 Fetching available options for payment methods, chair materials, table shapes, furniture sizes, sofa colors, and bed sizes.

## Design Patterns and OOP Principles

This project implements several key design patterns and object-oriented programming principles to ensure maintainability, flexibility, and adherence to SOLID principles:

### Creational Patterns

- **Factory Method**: The _create_furniture_from_dict method follows the Factory Method pattern by dynamically instantiating the correct Furniture subclass (Chair, Table, Sofa, Bed, Bookcase) based on the provided dictionary data. This method is primarily used in _load_inventory, which reads furniture data from a JSON file and ensures that each item is correctly instantiated with its specific attributes before being stored in the inventory.

- **Singleton Pattern**: Implemented in UserManager and Inventory to ensure only one instance of these classes exists throughout the application. This prevents redundant object creation and provides a single source of truth for inventory and user management.

### Behavioral Patterns

- **Strategy Pattern**:
  - `SearchStrategy` with concrete implementations (`NameSearchStrategy`, `PriceRangeSearchStrategy`, `AttributeSearchStrategy`) for different furniture search methods.
  - `DiscountStrategy` with implementations (`PercentageDiscountStrategy`, `FixedAmountDiscountStrategy`) for applying different discount types to the shopping cart.
- **Iterator**: Used in cart operations for iterating through cart items.

### Additional Design Patterns
- **Repository Pattern**: Implemented in the `Inventory`, `UserDatabase`, and `OrderManager` classes for data access abstraction.
- **Dependency Injection**: Services are injected into components that need them, enhancing testability and loose coupling.


### Object-Oriented Programming Principles and Language Features

The project leverages several key OOP principles and Python language features:

- **Enums**: Used throughout the project (e.g., `PaymentMethod`, `ChairMaterial`, `TableShape`, `FurnitureSize`, `SofaColor`, `BedSize`) to create type-safe, self-documenting code with predefined sets of values.
- **Data Classes**: Employed in the `Order` class to create a concise, immutable data container with built-in functionality.
- **Static Methods**: Used where appropriate for utility functions that don't require instance state.
- **Polymorphism**: Implemented in the furniture class hierarchy, allowing different furniture types to be treated through a common interface.
- **Abstraction**: Applied to hide implementation details and expose only necessary functionality to clients.
- **Inheritance**: Used in the furniture class hierarchy, where specific furniture types inherit from base classes.
- **Encapsulation**: Applied throughout the codebase to bundle data and methods, restricting direct access to some components.


## Project Structure

```
Online-Furniture-Store/
├── .github/workflows/         # CI/CD workflows
├── app/                       # Main application directory
│   ├── __init__.py            # Application factory & package initialization
│   ├── routes.py              # API endpoints (blueprint)
│   ├── config.py              # Application configuration
│   ├── utils.py               # Utility functions
│   ├── data/                  # Data storage files (inventory.json, orders.json, users.json)
│   └── models/                
│       ├── __init__.py
│       ├── cart_item_locator.py
│       ├── checkout_system.py
│       ├── discount_strategy.py
│       ├── enums.py
│       ├── furniture.py
│       ├── inventory.py
│       ├── jwt_manager.py
│       ├── order.py
│       ├── order_manager.py
│       ├── search_strategy.py
│       ├── shopping_cart.py
│       ├── user.py
│       ├── user_database.py
│       └── user_manager.py
├── tests/                  
│       ├── __init__.py            
│       ├── test_routes.py              
│       ├── test_run.py             
│       ├── test_utils.py              
│       ├── regression/        # Regression test for purchase flow      
│       └── models/            # Unit tests for all models 
├── tools/                     # Development utilities
│   └── precommit_runner.py    # Interactive pre-commit script
├── .flake8                    # Flake8 configuration for style checks
├── .gitignore                 # Files and directories to ignore in git
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── LICENSE                    # Project license (MIT)
├── README.md                  # Project documentation (this file)
├── pyproject.toml             # Python project configuration
├── run.py                     # Entry point to run the Flask server
└── requirements.txt           # Project dependencies
```

## Setup instructions 

1. **Clone the Repository**

   ```bash
   git clone https://github.com/TamarAdn/Online-Furniture-Store.git
   cd Online-Furniture-Store
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

To run the API server:
```bash
python run.py
```

## API Endpoints

### Authentication

- **POST** `/api/users/register`  
Register a new user. Provide a json like this - 
{"username": "rachel1",
"full_name": "rachel green ",
"email": "rachelgreen@gmail.com",
"password": "rachel123$",
"shipping_address": "central perk 1"}

- **POST** `/api/users/login`  
  Authenticate a user and obtain auth tokens. Provide username/email, password in body as json.

- **POST** `/api/users/refresh-token`  
  Refresh the access token using a provided refresh token. In a json file, example: { "refresh_token": "edgslowdla" }

- **POST** `/api/users/logout`  
  Log out the current user (invalidate token). In access token as authorization, Bearer.

### User Profile

- **GET** `/api/users/profile`  
  Retrieve the authenticated user's profile. Provide access token.

- **PUT** `/api/users/profile`  
  Update the authenticated user's profile. Provide changes in body. You can provide full_name / email / shipping_address in the body.

- **PUT** `/api/users/password`
  Change the authenticated user's password. Provide current_password and new_password in body, example -
  {
    "new_password" : "Miley123%",
    "current_password": "Selena123$"
  }

### Furniture Inventory

- **GET** `/api/furniture`
  List all furniture items.
  
- **GET** `/api/furniture?furniture_name=<name>⁠`
  Filter by name.

- **GET** `/api/furniture?min_price=<min_price>&max_price=<max_price>`
  Filter by price range.

- **GET** `/api/furniture?attribute_name=<attribute>&attribute_value=<value>`
  Filter by attribute.

- **GET** `/api/furniture/<furniture_id>`  
  Get details for a specific furniture item.

- **POST** `/api/furniture`  
  Add a new furniture item to the inventory (admin functionality). Provide - {
                                                                               "name": "chair",
                                                                               "price": "167.0",
                                                                               "quantity": = 2, (optional)
                                                                               "material": "wood"
                                                                             }

- **PUT** `/api/furniture/<furniture_id>`  
  Update the quantity of a furniture item (admin functionality). Provide - { "quantity": 6 }

- **DELETE** `/api/furniture/<furniture_id>`  
  Remove a furniture item from the inventory (admin functionality).

### Shopping Cart

- **GET** `/api/cart`  
  View the contents of the authenticated user's shopping cart.

- **POST** `/api/cart/add`                                        
  Add an item to the cart by furniture ID. Provide ID in body, example - 
  { "furniture_id": "8cce4d29-c8a0-4c53-9b75-739ed3031e30" }

- **POST** `/api/cart/find-and-add`                     
Finds a furniture item by its attributes and adds it to the shopping cart. In request Body (JSON):
- Provide the `name` of the furniture and any additional attributes (e.g., `color`, `material`).
- Optionally, you can include a `description_keyword` to refine the search by matching a word or phrase in the furniture’s description.
example 1:
{
  "name": "chair",
  "material": "leather"
}
example 2: 
{
  "name": "chair",
  "material": "leather",
  "description_keyword": "office"
}

- **DELETE** `/api/cart/remove/<furniture_id>`  
  Remove an item from the cart (optional - specify a quantity).

- **DELETE** `/api/cart/clear`  
  Clear the entire shopping cart.

- **POST** `/api/cart/discount` 
  Apply a discount to the shopping cart. Provide - {
                                                    "discountstrategy" = "Percentage",
                                                    "value" = "20"
                                                   }

### Checkout & Orders

- **POST** `/api/checkout`  
  Process the checkout and create a new order. Provide - {
                                                          "payment_method": "Credit Card"
                                                         }

- **GET** `/api/orders`  
  Retrieve all orders for the authenticated user.

- **GET** `/api/orders/<order_id>`  
  Get details for a specific order.

### Enumerations & Attributes

- **GET** `/api/enums/payment-methods`
  List all available payment methods.

- **GET** `/api/enums/chair-materials`  
  List all available chair materials.

- **GET** `/api/enums/table-shapes`  
  List all available table shapes.

- **GET** `/api/enums/furniture-sizes`  
  List all available furniture sizes.

- **GET** `/api/enums/sofa-colors`  
  List all available sofa colors.

- **GET** `/api/enums/bed-sizes`  
  List all available bed sizes.

## Data Storage
The project uses JSON files:
- **inventory.json**: Stores furniture items along with inventory quantities.
- **users.json**: Stores user account information.
- **orders.json**: Stores order history details.

## Architecture

### Application Design

- **Flask & Blueprints**: The API is implemented using Flask, with endpoints organized in `app/routes.py` and registered as a blueprint.
- **Application Factory**: The application factory (in `app/__init__.py`) creates and configures the Flask app, improving modularity and testability.
- **Error Handling**: Consistent error handling across endpoints returns appropriate HTTP status codes and JSON error messages.

## Development Tools

### Pre-commit Runner

The repository includes an interactive pre-commit hook runner in the `tools/` directory:

```bash
# Run pre-commit checks on all Python files
python tools/precommit_runner.py

# Run pre-commit checks on specific files
python tools/precommit_runner.py app/models/user.py app/routes.py

# Interactive mode: Review and fix issues file by file
python tools/precommit_runner.py --interactive

# Run a specific formatting tool directly 
python tools/precommit_runner.py --tool black  # Options: black, isort, flake8
```

This tool helps maintain code quality by running style checks and formatting tools on your code. Features include:

- Creating backups before modifying files
- Running individual tools (black, isort, flake8) directly
- Interactive mode for fixing issues one by one
- Running on specific files or the entire codebase

## Running Tests

To run the tests locally using pytest with code coverage report:

```bash
python -m pytest --cov=app --cov-report=term-missing
```


## License

This project is licensed under the [MIT License](LICENSE).

## **Project Contributors**
- **[Tamar Adani]** 
- **[Almog Alfamon]** 
- **[Ziv Laitman]** 
- **[Ofri Bracha]**