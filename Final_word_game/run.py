# builds & exposes flask app, so Gunicorn can run it for Railway

import os
from app import create_app, socketio            #app builder, in __init__.py
from app.extensions import db


# for Railway
app = create_app()                               #builds the app

#socketio.init_app(app, async_mode="gevent")     #forces Flask-SocketIO to use gevent properly

# checks if db exist/ creates missing ones
with app.app_context():
    db.create_all()

# for local host
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)

# start command for railway
# gunicorn -k gevent -w 1 run:app --bind 0.0.0.0:$PORT
    # gunicorn: production web server
    # -k gevent: gunicor w/gevent: supports WebSockets $ async connections
    # -w 1: one instance of app handles all users
    # run:app : tells Gunicorn to import the Flask app from run.py
    # --bind 0.0.0.0:$PORT: controls were server listens, $port: use whatever port Railway gives me

