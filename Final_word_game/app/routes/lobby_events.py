from flask_socketio import emit, join_room
from app.extensions import socketio

def register_lobby_events():

    @socketio.on('join_lobby_list')
    def on_join_lobby_list():
        join_room('lobby-list')

    @socketio.on('join_lobby_room')
    def on_join_lobby_room(data):
        code = data.get('code', '').upper()
        join_room(f'lobby_{code}')