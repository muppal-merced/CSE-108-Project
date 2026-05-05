from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wordle-game-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wordle_game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Lobby(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='created_lobbies', foreign_keys='Lobby.creator_id')
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    player2 = db.relationship('User', backref='joined_lobbies', foreign_keys='Lobby.player2_id')
    word_length = db.Column(db.Integer, default=5)  # Word length for the game
    status = db.Column(db.String(20), default='waiting')  # waiting, active, finished
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Lobby {self.code}>'

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lobby_id = db.Column(db.Integer, db.ForeignKey('lobby.id'), nullable=False)
    lobby = db.relationship('Lobby', backref='game')
    player1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player1 = db.relationship('User', backref='games_as_player1', foreign_keys=[player1_id])
    player2 = db.relationship('User', backref='games_as_player2', foreign_keys=[player2_id])
    word_length = db.Column(db.Integer, default=5)  # Word length for the game
    player1_word = db.Column(db.String(20), nullable=True)  # Increased to support longer words
    player2_word = db.Column(db.String(20), nullable=True)  # Increased to support longer words
    current_turn = db.Column(db.Integer, default=1)  # 1 for player1 guessing player2's word, 2 for player2 guessing player1's word
    player1_guesses = db.Column(db.Text, default='')  # JSON string of guesses
    player2_guesses = db.Column(db.Text, default='')  # JSON string of guesses
    player1_score = db.Column(db.Integer, default=0)
    player2_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='setting_words')  # setting_words, playing, finished
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    winner = db.relationship('User', backref='won_games', foreign_keys=[winner_id])
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Game {self.id} in Lobby {self.lobby.code}>'

# Create database tables
with app.app_context():
    db.create_all()