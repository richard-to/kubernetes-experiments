from datetime import timedelta
import hashlib
import secrets

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session as DbSession
from starlette.status import HTTP_401_UNAUTHORIZED

from . import crud
from .config import SESSION_DB_TOKEN_KEY
from .core import oauth2_scheme, pwd_context
from .db import get_db
from .models import Account
from .session_db import get_session_db


CREDENTIALS_EXCEPTION = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

LOGIN_EXCEPTION = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_token(token, secret_key):
    return hashlib.sha256(secret_key + token).hexdigest()


def authenticate_account(db: DbSession, email: str, password: str):
    account = crud.get_account_by_email(db, email)
    if not account:
        return False
    if not pwd_context.verify(password, account.password):
        return False
    return account


def create_access_token(*, account: Account, expires_delta: timedelta = None):
    if not expires_delta:
        expires_delta = timedelta(minutes=15)

    token = secrets.token_hex()

    hashed_token = hash_token(token, SESSION_DB_TOKEN_KEY)
    session_db = get_session_db()
    session_db.hmset(hashed_token, {"email": account.email})
    session_db.expire(hashed_token, expires_delta)

    return token


def get_account(token: str = Depends(oauth2_scheme), db: DbSession = Depends(get_db)):
    session_db = get_session_db()
    hashed_token = hash_token(token, SESSION_DB_TOKEN_KEY)
    data = session_db.hgetall(hashed_token)

    if data is None:
        raise CREDENTIALS_EXCEPTION

    account = crud.get_account_by_email(db, data["email"])
    if account is None:
        raise CREDENTIALS_EXCEPTION
    return account
