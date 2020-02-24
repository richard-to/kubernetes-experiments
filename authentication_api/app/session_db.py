import redis

from .config import SESSION_DB_NAME, SESSION_DB_HOST, SESSION_DB_PORT


def get_session_db():
    return redis.Redis(host=SESSION_DB_HOST, port=SESSION_DB_PORT, db=SESSION_DB_NAME, decode_responses=True)
