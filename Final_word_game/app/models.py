from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

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
    name = db.Column(db.String(80), default='')
    lobby_type = db.Column(db.String(10), default='public')  # 'public' or 'private'
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='created_lobbies', foreign_keys='Lobby.creator_id')
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    player2 = db.relationship('User', backref='joined_lobbies', foreign_keys='Lobby.player2_id')
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
    secret_word = db.Column(db.String(10), nullable=False)      # shared word both players guess
    player1_guesses = db.Column(db.Text, default='')            # JSON list
    player2_guesses = db.Column(db.Text, default='')
    player1_solved = db.Column(db.Boolean, default=False)
    player2_solved = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='playing')        # playing, finished
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    winner = db.relationship('User', backref='won_games', foreign_keys=[winner_id])
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Game {self.id} in Lobby {self.lobby.code}>'