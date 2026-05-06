from app.extensions import socketio, db
from app.models import Lobby, Game
from flask import session
from app.models import Lobby, Game
from flask_socketio import emit, join_room

import json

def register_game_events():

    @socketio.on('join')
    def handle_join(data):
        room = data['room']
        username = data['username']
        join_room(room)
        emit('message', {'msg': f'{username} joined'}, room=room)

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

    @socketio.on('pause_game')
    def on_pause_game(data):
        lobby_code = data['lobby_code']
        paused = data['paused']

        lobby = Lobby.query.filter_by(code=lobby_code).first()
        if lobby:
            # Here you could store pause state in the database if needed
            # For now, just broadcast the pause state
            socketio.emit('game_paused', {'paused': paused}, room=lobby_code)