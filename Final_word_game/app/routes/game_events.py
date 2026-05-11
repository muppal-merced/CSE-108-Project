import json
import os
from flask import session
from flask_socketio import emit, join_room
from app.extensions import socketio, db
from app.models import Game, Lobby


def _get_wordbank():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, 'data', 'answers.txt')) as f:
        return {
            w.strip().upper()
            for w in f
            if w.strip() and len(w.strip()) == 5
        }

def _score_guess(guess, secret):
    guess, secret = guess.upper(), secret.upper()
    result = [{'letter': g, 'status': 'absent'} for g in guess]
    counts = {}
    for i, (g, s) in enumerate(zip(guess, secret)):
        if g == s:
            result[i]['status'] = 'correct'
        else:
            counts[s] = counts.get(s, 0) + 1
    for i, (g, s) in enumerate(zip(guess, secret)):
        if result[i]['status'] != 'correct' and g in counts and counts[g] > 0:
            result[i]['status'] = 'present'
            counts[g] -= 1
    return result

def register_game_events():

    @socketio.on('join_game')
    def on_join_game(data):
        game_id = data.get('game_id')
        uid = session.get('user_id')
        game = Game.query.get(game_id)
        if not game:
            emit('error', {'msg': 'Game not found'}); return
        join_room(f'game_{game_id}')

        is_p1 = (uid == game.player1_id)
        my_guesses = json.loads(game.player1_guesses or '[]') if is_p1 else json.loads(game.player2_guesses or '[]')
        opp_guesses_raw = json.loads(game.player2_guesses or '[]') if is_p1 else json.loads(game.player1_guesses or '[]')
        opp_colors = [[{'status': t['status']} for t in row] for row in opp_guesses_raw]

        emit('game_state', {
            'game_id': game_id,
            'my_guesses': my_guesses,
            'opp_colors': opp_colors,
            'player1': game.player1.username,
            'player2': game.player2.username,
            'is_player1': is_p1,
            'status': game.status,
            'word_length': len(game.secret_word),
        })

    @socketio.on('submit_guess')
    def on_submit_guess(data):
        game_id = data.get('game_id')
        guess = data.get('guess', '').strip().upper()
        uid = session.get('user_id')
        game = Game.query.get(game_id)

        if not game or game.status != 'playing':
            emit('error', {'msg': 'Game not active'}); return
        if uid not in (game.player1_id, game.player2_id):
            emit('error', {'msg': 'Not in this game'}); return
        if len(guess) != len(game.secret_word):
            emit('error', {'msg': f'Guess must be {len(game.secret_word)} letters'}); return
        if guess not in _get_wordbank():
            emit('error', {'msg': 'Not a valid word'}); return

        is_p1 = (uid == game.player1_id)
        guesses_attr = 'player1_guesses' if is_p1 else 'player2_guesses'
        solved_attr  = 'player1_solved'  if is_p1 else 'player2_solved'

        my_guesses = json.loads(getattr(game, guesses_attr) or '[]')
        if len(my_guesses) >= 6:
            emit('error', {'msg': 'No guesses remaining'}); return
        if guess in {''.join(t['letter'] for t in row).upper() for row in my_guesses}:
            emit('error', {'msg': 'You already guessed that word'}); return

        scored = _score_guess(guess, game.secret_word)
        my_guesses.append(scored)
        setattr(game, guesses_attr, json.dumps(my_guesses))

        if all(t['status'] == 'correct' for t in scored):
            setattr(game, solved_attr, True)

        p1_solved = game.player1_solved
        p2_solved = game.player2_solved
        p1_guesses = json.loads(game.player1_guesses or '[]')
        p2_guesses = json.loads(game.player2_guesses or '[]')
        p1_out = len(p1_guesses) >= 6 and not p1_solved
        p2_out = len(p2_guesses) >= 6 and not p2_solved

        game_over, result_msg, winner_id = False, None, None
        if p1_solved and p2_solved:
            game_over, result_msg = True, 'both_win'
        elif p1_solved:
            game_over, result_msg, winner_id = True, 'player1_wins', game.player1_id
        elif p2_solved:
            game_over, result_msg, winner_id = True, 'player2_wins', game.player2_id
        elif p1_out and p2_out:
            game_over, result_msg = True, 'both_lose'

        if game_over:
            game.status = 'finished'
            game.winner_id = winner_id
            game.lobby.status = 'finished'

        db.session.commit()

        socketio.emit('guess_result', {
            'player_id': uid,
            'is_player1': is_p1,
            'scored_row': scored,
            'opp_color_row': [{'status': t['status']} for t in scored],
            'game_over': game_over,
            'result': result_msg,
            'secret_word': game.secret_word if game_over else None,
            'winner_id': winner_id,
            'player1_id': game.player1_id,
            'player2_id': game.player2_id,
        }, room=f'game_{game_id}')

    @socketio.on('timer_expired')
    def on_timer_expired(data):
        game = Game.query.get(data.get('game_id'))
        if game and game.status == 'playing':
            game.status = 'finished'
            game.lobby.status = 'finished'
            db.session.commit()
            socketio.emit('game_over', {
                'result': 'time_up',
                'secret_word': game.secret_word,
                'player1_id': game.player1_id,
                'player2_id': game.player2_id,
            }, room=f'game_{data["game_id"]}')

    @socketio.on('player_disconnected_game')
    def on_disconnect_game(data):
        game_id = data.get('game_id')
        game = Game.query.get(game_id)
        if game and game.status == 'playing':
            game.status = 'finished'
            game.lobby.status = 'finished'
            db.session.commit()
        socketio.emit('opponent_disconnected', {
            'msg': f"{data.get('username', 'Opponent')} disconnected. Game ended."
        }, room=f'game_{game_id}')