import pytest

from app import create_app


@pytest.fixture
def app_instance():
    app = create_app()
    app.config["TESTING"] = True
    return app


def test_app_creation(app_instance):
    # Check that the app instance was created
    assert app_instance is not None
    # Verify that the blueprint named "api" is registered
    assert "api" in app_instance.blueprints
