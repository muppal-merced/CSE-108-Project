# handles lobby page, create lobby, join lobby

from flask import render_template, request, redirect, url_for, session, flash
from app.extensions import db, socketio
from app.models import Lobby, Game
import random, string

def register_lobby_routes(app):

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