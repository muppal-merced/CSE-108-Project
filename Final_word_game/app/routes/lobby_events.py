from flask_socketio import join_room
from app.extensions import socketio


def register_lobby_events():

    # everyone joins this room so lobby list updates work
    @socketio.on('join_lobby_list')
    def on_join_lobby_list():
        join_room('lobby-list')
        print("USER JOINED lobby-list")

    # host joins their specific lobby room
    @socketio.on('join_lobby_room')
    def on_join_lobby_room(data):

        code = data.get('code')

        if not code:
            return

        room_name = f'lobby_{code}'

        join_room(room_name)

        print(f"USER JOINED ROOM: {room_name}")