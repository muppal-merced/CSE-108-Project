import random, string, os
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app.extensions import db, socketio
from app.models import Lobby, Game

DEMO_WORD = "LEMON"

def _get_wordbank():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, 'data', 'answers.txt')) as f:
        return [w.strip().upper() for w in f if w.strip() and len(w.strip()) == 5]

def _pick_word(lobby_type):
    return DEMO_WORD if lobby_type == 'private' else random.choice(_get_wordbank())

def _gen_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Lobby.query.filter_by(code=code).first():
            return code

def register_lobby_routes(app):

    @app.route("/lobby")
    def lobby():
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        uid = session["user_id"]
        public_lobbies = Lobby.query.filter_by(status='waiting', lobby_type='public').all()
        return render_template("lobby.html",
                               username=session.get("username"),
                               public_lobbies=public_lobbies,
                               user_id=uid)

    @app.route("/create_lobby", methods=["POST"])
    def create_lobby():
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        uid = session["user_id"]

        # One active lobby per user
        existing = Lobby.query.filter(
            Lobby.creator_id == uid,
            Lobby.status.in_(['waiting', 'active'])
        ).first()
        if existing:
            flash("You already have an active lobby. Delete it first.")
            return redirect(url_for("lobby"))

        visibility = request.form.get("visibility", "public")
        name = request.form.get("name", "").strip() or f"{session['username']}'s Lobby"
        lobby = Lobby(code=_gen_code(), name=name, lobby_type=visibility,
                      creator_id=uid, status='waiting')
        db.session.add(lobby)
        db.session.commit()
        socketio.emit('lobby_list_changed', {}, room='lobby-list')
        return redirect(url_for("lobby"))

    @app.route("/delete_lobby/<lobby_code>", methods=["POST"])
    def delete_lobby(lobby_code):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        uid = session["user_id"]
        lobby = Lobby.query.filter_by(code=lobby_code).first()
        if not lobby or lobby.creator_id != uid:
            flash("Cannot delete that lobby.")
            return redirect(url_for("lobby"))
        if lobby.status == 'active':
            flash("Cannot delete an active game.")
            return redirect(url_for("lobby"))
        db.session.delete(lobby)
        db.session.commit()
        socketio.emit('lobby_list_changed', {}, room='lobby-list')
        return redirect(url_for("lobby"))

    @app.route("/join_lobby", methods=["POST"])
    def join_lobby():
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        uid = session["user_id"]
        room_code = request.form.get("room_code", "").strip().upper()
        lobby = Lobby.query.filter_by(code=room_code).first()

        if not lobby:
            flash("Lobby not found.")
            return redirect(url_for("lobby"))
        if lobby.creator_id == uid:
            flash("You cannot join your own lobby.")
            return redirect(url_for("lobby"))
        if lobby.status != 'waiting':
            flash("Lobby is not open.")
            return redirect(url_for("lobby"))

        # Create game with auto-chosen word
        word = _pick_word(lobby.lobby_type)
        lobby.player2_id = uid
        lobby.status = 'active'
        game = Game(lobby_id=lobby.id, player1_id=lobby.creator_id,
                    player2_id=uid, secret_word=word, status='playing')
        db.session.add(game)
        db.session.commit()

        socketio.emit('game_starting', {'lobby_code': room_code, 'game_id': game.id},
                      room=f'lobby_{room_code}')
        socketio.emit('lobby_list_changed', {}, room='lobby-list')
        return redirect(url_for("game", lobby_code=room_code))

    @app.route("/lobby/list")
    def list_lobbies():
        if not session.get("logged_in"):
            return jsonify({'error': 'Not logged in'}), 401
        uid = session["user_id"]
        lobbies = Lobby.query.filter_by(status='waiting', lobby_type='public').all()
        return jsonify([{
            'code': lb.code, 'name': lb.name,
            'creator': lb.creator.username, 'creator_id': lb.creator_id
        } for lb in lobbies])