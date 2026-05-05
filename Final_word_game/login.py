from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import app, db, User, Lobby, Game, socketio
from flask_socketio import emit, join_room, leave_room
import random
import string
import json

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
    return render_template("lobby.html", username=session.get("username", "Player"))

@app.route("/create_lobby", methods=["POST"])
def create_lobby():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Ensure unique code
    while Lobby.query.filter_by(code=code).first():
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    lobby = Lobby(code=code, creator_id=user_id)
    db.session.add(lobby)
    db.session.commit()

    return redirect(url_for("game", lobby_code=code))

@app.route("/join_lobby", methods=["POST"])
def join_lobby():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    room_code = request.form.get("room_code", "").strip().upper()
    lobby = Lobby.query.filter_by(code=room_code).first()

    if not lobby:
        flash("Lobby not found.")
        return redirect(url_for("lobby"))

    if lobby.status != 'waiting':
        flash("Lobby is not available.")
        return redirect(url_for("lobby"))

    if lobby.creator_id == session["user_id"]:
        return redirect(url_for("game", lobby_code=room_code))

    if lobby.player2_id:
        flash("Lobby is full.")
        return redirect(url_for("lobby"))

    lobby.player2_id = session["user_id"]
    lobby.status = 'active'
    db.session.commit()

    # Create game
    game = Game(lobby_id=lobby.id, player1_id=lobby.creator_id, player2_id=lobby.player2_id)
    db.session.add(game)
    db.session.commit()

    # Notify players
    socketio.emit('lobby_joined', {'lobby_code': room_code}, room=room_code)

    return redirect(url_for("game", lobby_code=room_code))

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
    user_id = session.get('user_id')

    lobby = Lobby.query.filter_by(code=lobby_code).first()
    game = Game.query.filter_by(lobby_id=lobby.id).first()

    if user_id == game.player1_id:
        game.player1_word = word
    elif user_id == game.player2_id:
        game.player2_word = word

    db.session.commit()

    # Check if both words are set
    if game.player1_word and game.player2_word:
        game.status = 'playing'
        db.session.commit()
        socketio.emit('game_start', {'lobby_code': lobby_code}, room=lobby_code)

@socketio.on('make_guess')
def on_make_guess(data):
    lobby_code = data['lobby_code']
    guess = data['guess'].upper()
    user_id = session.get('user_id')

    lobby = Lobby.query.filter_by(code=lobby_code).first()
    game = Game.query.filter_by(lobby_id=lobby.id).first()

    if game.status != 'playing':
        return

    # Determine whose turn and whose word
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

    # Check if guess is correct
    if guess == target_word:
        if game.current_turn == 1:
            game.player1_score = len(guesses)
        else:
            game.player2_score = len(guesses)

        # Switch turns or end game
        if game.current_turn == 1:
            game.current_turn = 2
        else:
            # Game finished
            game.status = 'finished'
            if game.player1_score < game.player2_score:
                game.winner_id = game.player1_id
            elif game.player2_score < game.player1_score:
                game.winner_id = game.player2_id
            # Tie if equal

        db.session.commit()
        socketio.emit('guess_result', {
            'lobby_code': lobby_code,
            'guess': guess,
            'result': 'correct',
            'guesses': guesses,
            'turn': game.current_turn,
            'status': game.status
        }, room=lobby_code)
    elif len(guesses) >= 6:
        # Out of guesses
        if game.current_turn == 1:
            game.player1_score = 7  # Max score
            game.current_turn = 2
        else:
            game.player2_score = 7
            game.status = 'finished'
            if game.player1_score < game.player2_score:
                game.winner_id = game.player1_id
            elif game.player2_score < game.player1_score:
                game.winner_id = game.player2_id

        db.session.commit()
        socketio.emit('guess_result', {
            'lobby_code': lobby_code,
            'guess': guess,
            'result': 'game_over',
            'guesses': guesses,
            'turn': game.current_turn,
            'status': game.status
        }, room=lobby_code)
    else:
        # Wrong guess, continue
        db.session.commit()
        socketio.emit('guess_result', {
            'lobby_code': lobby_code,
            'guess': guess,
            'result': 'wrong',
            'guesses': guesses,
            'turn': game.current_turn
        }, room=lobby_code)

if __name__ == "__main__":
    socketio.run(app, debug=True)
