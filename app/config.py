# ----- File Paths -----
USERS_FILE = "app/data/users.json"
INVENTORY_FILE = "app/data/inventory.json"
ORDERS_FILE = "app/data/orders.json"

# ----- JWT Authentication -----
JWT_SECRET_KEY = "your_secret_key_here"
JWT_ALGORITHM = "HS256"

# Token expiration settings
ACCESS_TOKEN_EXPIRY_MINUTES = 30  # Access tokens expire after 30 minutes
REFRESH_TOKEN_EXPIRY_DAYS = 7  # Refresh tokens expire after 7 days

# ---- Other Default Values ----
TAX_RATE = 0.18
