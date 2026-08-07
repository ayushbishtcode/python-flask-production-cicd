from flask import Flask

from .config import Config
from .database import db


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    from .routes import api

    app.register_blueprint(api)

    with app.app_context():
        db.create_all()

    return app