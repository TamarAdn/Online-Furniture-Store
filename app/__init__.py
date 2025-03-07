from flask import Flask
from flask_cors import CORS

from app.routes import api  # Import your routes (blueprint) at the module level


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config")
    CORS(app)
    app.register_blueprint(api)  # Register the API blueprint
    return app
