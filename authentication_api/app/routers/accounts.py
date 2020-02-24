from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import authenticator, crud, models as m, schemas as s
from ..db import get_db
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


@router.post("/", response_model=s.Account)
def create_account(account: s.AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(db, account)


@router.get("/me", response_model=s.Account)
def read_account_me(account: m.Account = Depends(authenticator.get_account)):
    return account


@router.post("/token", response_model=s.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    account = authenticator.authenticate_account(db, form_data.username, form_data.password)
    if not account:
        raise authenticator.LOGIN_EXCEPTION
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = authenticator.create_access_token(
        account=account,
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
