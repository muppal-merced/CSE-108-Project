from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import app, db, User, Lobby, Game, socketio
from flask_socketio import emit, join_room, leave_room
from threading import Timer
import random
import string
import json

socket_user_map = {}
user_socket_counts = {}
disconnect_timers = {}

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["logged_in"] = True
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("lobby"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required."
        elif User.query.filter_by(username=username).first():
            error = "Username already exists."
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session["logged_in"] = True
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("lobby"))

    return render_template("signup.html", error=error)

@app.route("/lobby")
def lobby():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    
    # No auto-join - users must explicitly join lobbies

    public_lobbies = Lobby.query.filter_by(status='waiting_public').all()
    private_lobbies = Lobby.query.filter_by(status='waiting_private').all()
    pending_requests = Lobby.query.filter_by(creator_id=user_id, status='request_pending').all()
    pending_lobby = Lobby.query.filter_by(player2_id=user_id, status='request_pending').first()
    
    # Get active lobbies created by the user
    active_created_lobbies = Lobby.query.filter_by(creator_id=user_id).filter(Lobby.status.in_(['selecting_words', 'playing', 'finished'])).all()

    seen = set()
    dedup_public = []
    for lobby in public_lobbies:
        if lobby.code not in seen:
            seen.add(lobby.code)
            dedup_public.append(lobby)

    seen = set()
    dedup_private = []
    for lobby in private_lobbies:
        if lobby.code not in seen:
            seen.add(lobby.code)
            dedup_private.append(lobby)

    return render_template(
        "lobby.html",
        username=session.get("username", "Player"),
        public_lobbies=dedup_public,
        private_lobbies=dedup_private,
        private_lobby_count=len(dedup_private),
        pending_requests=pending_requests,
        pending_lobby=pending_lobby,
        active_created_lobbies=active_created_lobbies,
        user_id=user_id
    )

@app.route("/create_lobby", methods=["POST"])
def create_lobby():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Ensure unique code
    while Lobby.query.filter_by(code=code).first():
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    visibility = request.form.get("visibility", "public")
    status = 'waiting_public' if visibility == 'public' else 'waiting_private'

    lobby = Lobby(code=code, creator_id=user_id, status=status, word_length=5)  # Default to 5, will be set later
    db.session.add(lobby)
    db.session.commit()

    return redirect(url_for("lobby"))

@app.route("/join_lobby", methods=["POST"])
def join_lobby():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    room_code = request.form.get("room_code", "").strip().upper()
    lobby = Lobby.query.filter_by(code=room_code).first()

    if not lobby:
        flash("Lobby not found.")
        return redirect(url_for("lobby"))

    if lobby.creator_id == session["user_id"]:
        return redirect(url_for("game", lobby_code=room_code))

    if lobby.status == 'active' or lobby.status == 'playing' or lobby.status == 'selecting_words':
        flash("Lobby is already in a game.")
        return redirect(url_for("lobby"))

    if lobby.status == 'request_pending':
        flash("Lobby already has a pending join request.")
        return redirect(url_for("lobby"))

    if lobby.status in ['waiting', 'waiting_public']:
        lobby.player2_id = session["user_id"]
        lobby.status = 'selecting_words'
        db.session.add(lobby)

        game = Game(
            lobby_id=lobby.id,
            player1_id=lobby.creator_id,
            player2_id=lobby.player2_id,
            word_length=lobby.word_length,
            player1_word=None,
            player2_word=None,
            status='selecting_words'
        )
        db.session.add(game)
        db.session.commit()

        socketio.emit(
            'lobby_update',
            {
                'lobby_code': room_code,
                'status': 'selecting_words'
            },
            room='lobby-list'
        )

        return redirect(url_for("game", lobby_code=room_code))

    if lobby.status == 'waiting_private':
        lobby.player2_id = session["user_id"]
        lobby.status = 'request_pending'
        db.session.commit()

        socketio.emit(
            'join_request',
            {
                'lobby_code': room_code,
                'requester': session["username"],
                'owner_id': lobby.creator_id
            },
            room=f'user-{lobby.creator_id}'
        )
        socketio.emit(
            'lobby_update',
            {
                'lobby_code': room_code,
                'status': 'request_pending'
            },
            room='lobby-list'
        )

        flash("Join request sent. Waiting for the lobby owner to accept.")
        return redirect(url_for("lobby"))

    flash("Lobby is not available.")
    return redirect(url_for("lobby"))

@app.route("/approve_join/<lobby_code>", methods=["POST"])
def approve_join(lobby_code):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    lobby = Lobby.query.filter_by(code=lobby_code).first()
    if not lobby or lobby.creator_id != session["user_id"]:
        flash("Invalid lobby or permission denied.")
        return redirect(url_for("lobby"))

    if lobby.status != 'request_pending' or not lobby.player2_id:
        flash("There is no pending request to approve.")
        return redirect(url_for("lobby"))

    game = Game(
        lobby_id=lobby.id,
        player1_id=lobby.creator_id,
        player2_id=lobby.player2_id,
        word_length=lobby.word_length,
        player1_word=None,
        player2_word=None,
        status='selecting_words'
    )
    db.session.add(game)
    lobby.status = 'selecting_words'
    db.session.commit()

    socketio.emit(
        'join_request_response',
        {
            'lobby_code': lobby_code,
            'status': 'accepted'
        },
        room=f'user-{lobby.player2_id}'
    )
    socketio.emit(
        'lobby_update',
        {
            'lobby_code': lobby_code,
            'status': 'selecting_words'
        },
        room='lobby-list'
    )

    flash("Player accepted. Game is starting.")
    return redirect(url_for("game", lobby_code=lobby_code))

@app.route("/reject_join/<lobby_code>", methods=["POST"])
def reject_join(lobby_code):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    lobby = Lobby.query.filter_by(code=lobby_code).first()
    if not lobby or lobby.creator_id != session["user_id"]:
        flash("Invalid lobby or permission denied.")
        return redirect(url_for("lobby"))

    if lobby.status != 'request_pending' or not lobby.player2_id:
        flash("There is no pending request to reject.")
        return redirect(url_for("lobby"))

    requester_id = lobby.player2_id
    lobby.player2_id = None
    lobby.status = 'waiting_private'
    db.session.commit()

    socketio.emit(
        'join_request_response',
        {
            'lobby_code': lobby_code,
            'status': 'rejected'
        },
        room=f'user-{requester_id}'
    )
    socketio.emit(
        'lobby_update',
        {
            'lobby_code': lobby_code,
            'status': 'waiting'
        },
        room='lobby-list'
    )

    flash("Join request rejected.")
    return redirect(url_for("lobby"))

@app.route("/game/<lobby_code>")
def game(lobby_code):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    lobby = Lobby.query.filter_by(code=lobby_code).first()
    if not lobby:
        flash("Lobby not found.")
        return redirect(url_for("lobby"))

    if session["user_id"] not in [lobby.creator_id, lobby.player2_id]:
        flash("You are not part of this lobby.")
        return redirect(url_for("lobby"))

    game = Game.query.filter_by(lobby_id=lobby.id).first()
    if not game:
        flash("The game has not been created yet.")
        return redirect(url_for("lobby"))

    if game.status not in ['selecting_words', 'playing', 'finished']:
        flash("The game is not ready yet.")
        return redirect(url_for("lobby"))

    return render_template("game.html", lobby=lobby, game=game, username=session["username"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# SocketIO events
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{data["username"]} has entered the room.'}, room=room)

@socketio.on('set_word')
def on_set_word(data):
    lobby_code = data['lobby_code']
    word = data['word'].upper()
    word_length = data.get('word_length', 5)
    user_id = session.get('user_id')

    lobby = Lobby.query.filter_by(code=lobby_code).first()
    if not lobby:
        return

    game = Game.query.filter_by(lobby_id=lobby.id).first()
    if not game or game.status != 'selecting_words':
        return

    # Set word length if this is the first word being set
    if not game.word_length or game.word_length == 5:  # Default was 5
        game.word_length = word_length
        lobby.word_length = word_length
        db.session.commit()

    if user_id == game.player1_id:
        game.player1_word = word
    elif user_id == game.player2_id:
        game.player2_word = word
    else:
        return

    db.session.commit()

    if game.player1_word and game.player2_word:
        game.status = 'playing'
        db.session.commit()
        socketio.emit('game_start', {
            'lobby_code': lobby_code,
            'player1_word': game.player1_word,
            'player2_word': game.player2_word,
            'word_length': game.word_length
        }, room=lobby_code)
    else:
        socketio.emit('word_set', {'lobby_code': lobby_code}, room=lobby_code)


def remove_inactive_lobbies(user_id):
    with app.app_context():
        lobbies = Lobby.query.filter(Lobby.creator_id == user_id, Lobby.status.in_(['waiting_public', 'waiting_private', 'request_pending'])).all()
        for lobby in lobbies:
            lobby.status = 'inactive'
            lobby.player2_id = None
        db.session.commit()
        socketio.emit('lobby_update', {'status': 'inactive'}, room='lobby-list')
    disconnect_timers.pop(user_id, None)

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

@socketio.on('join_lobby_list')
def on_join_lobby_list():
    join_room('lobby-list')

@socketio.on('disconnect')
def on_disconnect():
    user_id = socket_user_map.pop(request.sid, None)
    if not user_id:
        return

    user_socket_counts[user_id] = user_socket_counts.get(user_id, 1) - 1
    if user_socket_counts[user_id] <= 0:
        user_socket_counts.pop(user_id, None)
        timer = Timer(3.0, remove_inactive_lobbies, args=(user_id,))
        disconnect_timers[user_id] = timer
        timer.start()

@socketio.on('make_guess')
def on_make_guess(data):
    lobby_code = data['lobby_code']
    guess = data['guess'].upper()
    time_taken = data.get('time_taken', 0)
    user_id = session.get('user_id')

    lobby = Lobby.query.filter_by(code=lobby_code).first()
    game = Game.query.filter_by(lobby_id=lobby.id).first()

    if game.status != 'playing':
        return

    if game.current_turn == 1:  # Player 1 guessing Player 2's word
        if user_id != game.player1_id:
            return
        target_word = game.player2_word
        guesses = json.loads(game.player1_guesses or '[]')
        guesses.append(guess)
        game.player1_guesses = json.dumps(guesses)
    else:  # Player 2 guessing Player 1's word
        if user_id != game.player2_id:
            return
        target_word = game.player1_word
        guesses = json.loads(game.player2_guesses or '[]')
        guesses.append(guess)
        game.player2_guesses = json.dumps(guesses)

    def calculate_points(attempts, seconds):
        time_points = max(0, 180 - seconds)
        attempt_points = max(0, 70 - (attempts - 1) * 10)
        return time_points + attempt_points

    if guess == target_word:
        points = calculate_points(len(guesses), time_taken)
        if game.current_turn == 1:
            game.player1_score = points
            player1_points = points
            player2_points = game.player2_score or 0
        else:
            game.player2_score = points
            player2_points = points
            player1_points = game.player1_score or 0

        if game.current_turn == 1:
            game.current_turn = 2
        else:
            game.status = 'finished'
            if game.player1_score > game.player2_score:
                game.winner_id = game.player1_id
            elif game.player2_score > game.player1_score:
                game.winner_id = game.player2_id

        db.session.commit()
        socketio.emit('guess_result', {
            'lobby_code': lobby_code,
            'guess': guess,
            'result': 'correct',
            'guesses': guesses,
            'player1_guesses': json.loads(game.player1_guesses or '[]'),
            'player2_guesses': json.loads(game.player2_guesses or '[]'),
            'turn': game.current_turn,
            'status': game.status,
            'player1_score': game.player1_score,
            'player2_score': game.player2_score,
            'player1_points': player1_points,
            'player2_points': player2_points,
            'time_taken': time_taken
        }, room=lobby_code)
    elif len(guesses) >= 6:
        if game.current_turn == 1:
            game.player1_score = 0
            player1_points = 0
            player2_points = game.player2_score or 0
            game.current_turn = 2
        else:
            game.player2_score = 0
            player1_points = game.player1_score or 0
            player2_points = 0
            game.status = 'finished'
            if game.player1_score > game.player2_score:
                game.winner_id = game.player1_id
            elif game.player2_score > game.player1_score:
                game.winner_id = game.player2_id

        db.session.commit()
        socketio.emit('guess_result', {
            'lobby_code': lobby_code,
            'guess': guess,
            'result': 'game_over',
            'guesses': guesses,
            'player1_guesses': json.loads(game.player1_guesses or '[]'),
            'player2_guesses': json.loads(game.player2_guesses or '[]'),
            'turn': game.current_turn,
            'status': game.status,
            'player1_score': game.player1_score,
            'player2_score': game.player2_score,
            'player1_points': player1_points,
            'player2_points': player2_points,
            'time_taken': time_taken
        }, room=lobby_code)
    else:
        db.session.commit()
        socketio.emit('guess_result', {
            'lobby_code': lobby_code,
            'guess': guess,
            'result': 'wrong',
            'guesses': guesses,
            'player1_guesses': json.loads(game.player1_guesses or '[]'),
            'player2_guesses': json.loads(game.player2_guesses or '[]'),
            'turn': game.current_turn,
            'player1_score': game.player1_score,
            'player2_score': game.player2_score,
            'player1_points': 0,
            'player2_points': 0,
            'time_taken': time_taken
        }, room=lobby_code)

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

@socketio.on('pause_game')
def on_pause_game(data):
    lobby_code = data['lobby_code']
    paused = data['paused']

    lobby = Lobby.query.filter_by(code=lobby_code).first()
    if lobby:
        # Here you could store pause state in the database if needed
        # For now, just broadcast the pause state
        emit('game_paused', {'paused': paused}, room=lobby_code)

if __name__ == "__main__":
    socketio.run(app, debug=True)
