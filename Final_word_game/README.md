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

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python login.py
```

3. Open http://127.0.0.1:5000 in your browser

## Usage

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
├── login.py              # Main Flask application
├── database.py           # Database models and setup
├── requirements.txt      # Python dependencies
├── templates/
│   ├── login.html        # Login page
│   ├── signup.html       # Registration page
│   ├── lobby.html        # Lobby selection page
│   └── game.html         # Game interface
└── static/
    └── style.css         # Styling
```

## Database Models

- **User**: Stores user accounts with hashed passwords
- **Lobby**: Manages game rooms and player connections
- **Game**: Tracks game state, words, guesses, and scores

## Deployment

For production deployment, consider:
- Using a production WSGI server (Gunicorn, uWSGI)
- Setting up a proper database (PostgreSQL, MySQL)
- Configuring environment variables for secrets
- Setting up HTTPS
- Hosting on a cloud platform (Heroku, AWS, etc.)

## Security Features

- Password hashing with Werkzeug
- Session management
- Input validation
- SQL injection prevention via SQLAlchemy</content>
<parameter name="filePath">/workspaces/CSE-108-Project/Final_word_game/README.md