# creates app & connects everything
    # creates Flask app, connects db + socketio, registeres routes

from flask import Flask
from config import Config
from app.extensions import db, socketio

# ROUTES
from app.routes.login_signup import register_auth_routes
from app.routes.lobby import register_lobby_routes
from app.routes.game import register_game_routes

# SOCKET EVENTS
from app.routes.game_events import register_game_events
from app.routes.lobby_events import register_lobby_events
from app.routes.chat_events import register_chat_events
from app.routes.socket_connection import register_socket_events


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    socketio.init_app(app)

    # register HTTP routes
    register_auth_routes(app)
    register_lobby_routes(app)
    register_game_routes(app)

    # register socket events
    register_game_events()
    register_lobby_events()
    register_chat_events()
    register_socket_events()

    # create db tables
    with app.app_context():
        db.create_all()

    return app
