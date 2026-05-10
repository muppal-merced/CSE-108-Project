import random, string, os

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from app.extensions import db
from app.models import Lobby, Game

DEMO_WORD = "LEMON"


# =========================
# GET WORD BANK
# =========================
def _get_wordbank():

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with open(os.path.join(base, 'data', 'answers.txt')) as f:
        return [
            w.strip().upper()
            for w in f
            if w.strip() and len(w.strip()) == 5
        ]


# =========================
# PICK WORD
# =========================
def _pick_word(lobby_type):

    if lobby_type == 'private':
        return DEMO_WORD

    return random.choice(_get_wordbank())


# =========================
# GENERATE LOBBY CODE
# =========================
def _gen_code():

    while True:

        code = ''.join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            )
        )

        if not Lobby.query.filter_by(code=code).first():
            return code


# =========================
# REGISTER ROUTES
# =========================
def register_lobby_routes(app):


    # =========================
    # LOBBY PAGE
    # =========================
    @app.route("/lobby")
    def lobby():

        if not session.get("logged_in"):
            return redirect(url_for("login"))

        uid = session["user_id"]

        public_lobbies = Lobby.query.filter_by(
            status='waiting',
            lobby_type='public'
        ).all()

        my_lobby = Lobby.query.filter(
            (
                (Lobby.creator_id == uid) |
                (Lobby.player2_id == uid)
            ),
            Lobby.status.in_(['waiting', 'active'])
        ).first()

        return render_template(
            "lobby.html",
            username=session.get("username"),
            public_lobbies=public_lobbies,
            user_id=uid,
            my_lobby=my_lobby
        )


    # =========================
    # CREATE LOBBY
    # =========================
    @app.route("/create_lobby", methods=["POST"])
    def create_lobby():

        if not session.get("logged_in"):
            return redirect(url_for("login"))

        uid = session["user_id"]

        existing = Lobby.query.filter(
            (
                (Lobby.creator_id == uid) |
                (Lobby.player2_id == uid)
            ),
            Lobby.status.in_(['waiting', 'active'])
        ).first()

        if existing:
            flash("You already have an active lobby.")
            return redirect(url_for("lobby"))

        visibility = request.form.get("visibility", "public")

        name = (
            request.form.get("name", "").strip()
            or f"{session['username']}'s Lobby"
        )

        lobby = Lobby(
            code=_gen_code(),
            name=name,
            lobby_type=visibility,
            creator_id=uid,
            status='waiting',
            creator_ready=False,
            player2_ready=False
        )

        db.session.add(lobby)
        db.session.commit()

        return redirect(url_for("lobby"))


    # =========================
    # DELETE LOBBY
    # =========================
    @app.route("/delete_lobby/<lobby_code>", methods=["POST"])
    def delete_lobby(lobby_code):

        if not session.get("logged_in"):
            return redirect(url_for("login"))

        uid = session["user_id"]

        lobby = Lobby.query.filter_by(code=lobby_code).first()

        if not lobby or lobby.creator_id != uid:
            flash("Cannot delete that lobby.")
            return redirect(url_for("lobby"))

        game = Game.query.filter_by(lobby_id=lobby.id).first()

        if game:
            db.session.delete(game)

        db.session.delete(lobby)
        db.session.commit()

        return redirect(url_for("lobby"))


    # =========================
    # JOIN LOBBY
    # =========================
    @app.route("/join_lobby", methods=["POST"])
    def join_lobby():

        if not session.get("logged_in"):
            return redirect(url_for("login"))

        uid = session["user_id"]

        room_code = request.form.get(
            "room_code",
            ""
        ).strip().upper()

        lobby = Lobby.query.filter_by(code=room_code).first()

        if not lobby:
            flash("Lobby not found.")
            return redirect(url_for("lobby"))

        if lobby.creator_id == uid:
            flash("You cannot join your own lobby.")
            return redirect(url_for("lobby"))

        if lobby.player2_id:
            flash("Lobby is full.")
            return redirect(url_for("lobby"))

        if lobby.status != 'waiting':
            flash("Lobby is not open.")
            return redirect(url_for("lobby"))

        lobby.player2_id = uid
        lobby.player2_ready = False

        db.session.commit()

        return redirect(url_for("lobby"))


    # =========================
    # READY BUTTON
    # =========================
    @app.route("/ready/<lobby_code>", methods=["POST"])
    def ready(lobby_code):

        if not session.get("logged_in"):
            return jsonify({"success": False})

        uid = session["user_id"]

        lobby = Lobby.query.filter_by(code=lobby_code).first()

        if not lobby:
            return jsonify({"success": False})

        # host ready
        if uid == lobby.creator_id:
            lobby.creator_ready = True

        # guest ready
        elif uid == lobby.player2_id:
            lobby.player2_ready = True

        # BOTH READY
        if (
            lobby.creator_ready and
            lobby.player2_ready and
            lobby.player2_id is not None
        ):

            lobby.status = "active"

            existing_game = Game.query.filter_by(
                lobby_id=lobby.id
            ).first()

            if not existing_game:

                word = _pick_word(lobby.lobby_type)

                game = Game(
                    lobby_id=lobby.id,
                    player1_id=lobby.creator_id,
                    player2_id=lobby.player2_id,
                    secret_word=word,
                    status='playing'
                )

                db.session.add(game)

        db.session.commit()

        return jsonify({
            "success": True,
            "creator_ready": lobby.creator_ready,
            "player2_ready": lobby.player2_ready,
            "status": lobby.status
        })


    # =========================
    # LOBBY STATUS
    # =========================
    @app.route("/lobby_status/<lobby_code>")
    def lobby_status(lobby_code):

        lobby = Lobby.query.filter_by(code=lobby_code).first()

        if not lobby:
            return jsonify({"status": "missing"})

        return jsonify({
            "status": lobby.status,
            "creator_ready": lobby.creator_ready,
            "player2_ready": lobby.player2_ready,
            "player2_joined": lobby.player2_id is not None
        })


    # =========================
    # LIST LOBBIES
    # =========================
    @app.route("/lobby/list")
    def list_lobbies():

        if not session.get("logged_in"):
            return jsonify({'error': 'Not logged in'}), 401

        lobbies = Lobby.query.filter_by(
            status='waiting',
            lobby_type='public'
        ).all()

        return jsonify([
            {
                'code': lb.code,
                'name': lb.name,
                'creator': lb.creator.username,
                'creator_id': lb.creator_id
            }
            for lb in lobbies
        ])