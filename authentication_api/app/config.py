import os

# Auth DB (Postgres)
AUTH_DB_NAME = "auth"
AUTH_DB_USER = os.environ.get("AUTH_DB_USER")
AUTH_DB_PASSWORD = os.environ.get("AUTH_DB_PASSWORD")
AUTH_DB_URL = f"postgres://{AUTH_DB_USER}:{AUTH_DB_PASSWORD}@auth-db:5432/{AUTH_DB_NAME}"

# Session DB (Redis)
SESSION_DB_NAME = 0
SESSION_DB_HOST = "session-db"
SESSION_DB_PORT = 6379
SESSION_DB_TOKEN_KEY = "secret"

# OAuth2
ACCESS_TOKEN_EXPIRE_MINUTES = 10
TOKEN_URL = "http://auth.books.test/accounts/token"
