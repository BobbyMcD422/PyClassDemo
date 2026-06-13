import os

from flask import Flask

from classroom_app.activity import register_activity_logging
from classroom_app.extensions import db


def create_app():
    """Configure Flask and connect the shared package extensions."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.secret_key = os.environ.get(
        "FLASK_SECRET_KEY",
        "classroom-demo-secret",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql+psycopg2://{os.environ.get('DATABASE_USER', 'demo')}:"
        f"{os.environ.get('DATABASE_PASSWORD', 'demo')}@"
        f"{os.environ.get('DATABASE_HOST', 'localhost')}:"
        f"{os.environ.get('DATABASE_PORT', '5432')}/"
        f"{os.environ.get('DATABASE_NAME', 'demoapp')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    register_activity_logging(app)
    return app
