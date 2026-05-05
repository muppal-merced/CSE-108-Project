# 2-Player Wordle Game

A real-time multiplayer Wordle game built with Flask, SQLAlchemy, and SocketIO.

## Features

- User registration and login with hashed passwords
- Create and join lobbies with unique codes
- Real-time 1v1 Wordle duels
- Synchronized gameplay using WebSockets
- SQLite database for persistence

## Game Rules

1. Two players join a lobby
2. Each player sets a secret 5-letter word
3. Player 1 guesses Player 2's word (up to 6 attempts)
4. Player 2 guesses Player 1's word (up to 6 attempts)
5. Winner is the player who guesses correctly in fewer attempts
6. Points are awarded based on number of attempts (fewer attempts = better score)

## How to Play Locally
1. Install dependencies
pip install -r requirements.txt

2. Run the application:
python run.py

3. Go to ports table and click the link

## How To Play Online
go to: wor2le-production.up.railway.app

1. **Sign Up**: Create an account with a username and password
2. **Login**: Sign in with your credentials
3. **Create Lobby**: Generate a unique lobby code and share it with a friend
4. **Join Lobby**: Enter a lobby code to join a friend's game
5. **Set Word**: Each player enters a 5-letter secret word
6. **Play**: Take turns guessing each other's words
7. **Win**: The player with fewer correct guesses wins!

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-SocketIO
- **Frontend**: HTML, CSS, JavaScript, SocketIO client
- **Database**: SQLite
- **Real-time Communication**: WebSockets

## Project Structure

```
Final_word_game/
│
├── app/
│   ├── __init__.py              # creates app (Flask factory, registers routes + sockets)
│   ├── extensions.py            # shared tools (db + socketio instances)
│   ├── models.py                # database structure (User, Lobby, Game)
│
│   ├── routes/                  # backend logic (HTTP + Socket events)
│   │   ├── login_signup.py         # login & signup system (HTTP routes)
│   │   ├── lobby.py                # lobby creation/joining (HTTP routes)
│   │   ├── game.py                 # game page loading (HTTP routes)
│   │   ├── socket_connection.py    # socket connection tracking + rooms
│   │   ├── lobby_events.py         # real-time lobby updates (SocketIO)
│   │   ├── game_events.py          # core game logic (guessing, scoring, turns)
│   │   └── chat_events.py          # in-game chat system (SocketIO)
│
│   ├── templates/               # frontend HTML pages
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── lobby.html
│   │   └── game.html
│
│   └── static/                  # frontend styling
│       └── style.css
│
├── config.py                    # app configuration (database, secrets, settings)
├── run.py                       # entry point (starts Flask + SocketIO server)
│
├── instance/                    # database storage (SQLite or local DB files)
├── requirements.txt             # Python dependencies (libraries needed to run app)
└── README.md
```

## Database Models

- **User**: Stores user accounts with hashed passwords
- **Lobby**: Manages game rooms and player connections
- **Game**: Tracks game state, words, guesses, and scores

## Deployment

For production deployment:
- Using a production WSGI server (Gunicorn)
- Setting up a proper database (PostgreSQL)
- Configuring environment variables for secrets
- Setting up HTTPS
- Hosting on a cloud platform (Railray)

## Security Features

- Password hashing with Werkzeug
- Session management
- Input validation
- SQL injection prevention via SQLAlchemy</content>
<parameter name="filePath">/workspaces/CSE-108-Project/Final_word_game/README.md
