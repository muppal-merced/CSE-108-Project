# database config

import os

# container for all app settings
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
        # on Railway: SECRET_KEY
        # locally: dev-key

    SQLALCHEMY_TRACK_MODIFICATIONS = False      #turns off feature we don't need

    db_url = os.environ.get("DATABASE_URL")     # tries to read database_url from environment
        # Railway: DB_URL: POSTGRES
        # locally: DB_URL: None

    # fixes Postgres URL format for SQLAlchemy
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = db_url or "sqlite:///local.db"
        # if on Railway: use PostgreSQL
        # if on local: use SQLite