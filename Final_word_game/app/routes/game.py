# handles game page

from flask import render_template, session, redirect, url_for, flash
from app.models import Lobby, Game

# HTTP route that protects and loads game page

def register_game_routes(app):

    @app.route("/game/<lobby_code>")           # goes to game w/lobby code
    def game(lobby_code):     
                                                  
        if not session.get("logged_in"):            # check user logged in  
            return redirect(url_for("login"))

        lobby = Lobby.query.filter_by(code=lobby_code).first()      # find lobby w/code
        
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

        return render_template("game.html", lobby=lobby, game=game,
                       username=session["username"],
                       user_id=session["user_id"])
