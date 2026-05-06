# handles: connection tracking + disconnect cleanup

from flask import request
from flask import current_app as app
from threading import Timer
from flask_socketio import join_room, emit
from app.models import Lobby
from app.extensions import db, socketio


# in-memory connection state
socket_user_map = {}        # socket_id: user_id
user_socket_counts = {}     # user_id: num of active socket
disconnect_timers = {}      # user_id: timer object


# helps clear lobby list
def remove_inactive_lobbies(app, user_id):
    with app.app_context():
        lobbies = Lobby.query.filter(Lobby.creator_id == user_id, Lobby.status.in_(['waiting_public', 'waiting_private', 'request_pending'])).all()
        for lobby in lobbies:
            lobby.status = 'inactive'
            lobby.player2_id = None
        db.session.commit()
        socketio.emit('lobby_update', {'status': 'inactive'}, room='lobby-list')
    disconnect_timers.pop(user_id, None)

#Register events (register_user, disconnect)
def register_socket_events():

    @socketio.on('register_user')
    def on_register_user(data):
        user_id = data.get('user_id')
        if user_id:
            join_room(f'user-{user_id}')
            socket_user_map[request.sid] = user_id
            user_socket_counts[user_id] = user_socket_counts.get(user_id, 0) + 1
            if user_id in disconnect_timers:
                disconnect_timers[user_id].cancel()
                disconnect_timers.pop(user_id, None)

    @socketio.on('join')
    def on_join(data):
        room = data['room']
        join_room(room)
        emit('status', {'msg': f'{data["username"]} has entered the room.'}, room=room)


    @socketio.on('disconnect')
    def on_disconnect():
        user_id = socket_user_map.pop(request.sid, None)
        if not user_id:
            return

        user_socket_counts[user_id] = user_socket_counts.get(user_id, 1) - 1
        if user_socket_counts[user_id] <= 0:
            user_socket_counts.pop(user_id, None)
            timer = Timer(3.0, remove_inactive_lobbies, args=(socketio.server.app, user_id)
)
            disconnect_timers[user_id] = timer
            timer.start()