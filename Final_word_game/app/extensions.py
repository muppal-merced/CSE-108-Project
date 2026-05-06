# creates tools all at once, init later


from flask_sqlalchemy import SQLAlchemy
    #lets app use a database easily (models)

from flask_socketio import SocketIO
    #lets app do real-time communitcation(game updates)

db = SQLAlchemy()  
    #creates a database object (not connected to Flask app uet)

socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")
    #creates a Socket.IO server object (not connected yet)

