from flask_socketio import emit
from app.extensions import socketio
from flask import session

def register_chat_events():

    @socketio.on('send_chat')
    def on_send_chat(data):
        lobby_code = data['lobby_code']
        message = data['message']
        username = session.get('username', 'Anonymous')

        # Broadcast chat message to all players in the lobby
        emit('chat_message', {
            'username': username,
            'message': message
        }, room=lobby_code)