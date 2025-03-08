from app import create_app  # Import the create_app function

app = create_app()  # Create an app instance

# Ensure `app.py` is executed even when imported (for test coverage)
if __name__ != "__main__":
    app.testing = True

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)  # pragma: no cover
