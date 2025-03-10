import pytest

from run import app  # Import `app` from `app.py` (ensuring it runs)


@pytest.fixture
def client():
    """Create a test client for making API requests."""
    app.config["TESTING"] = True
    return app.test_client()


def test_app_creation():
    """Test that the app instance is created successfully."""
    assert app is not None
    assert "api" in app.blueprints


def test_root_endpoint(client):
    """Test that the root endpoint returns a valid response."""
    response = client.get("/api/")
    assert response.status_code in [200, 404]
