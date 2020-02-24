from sqlalchemy.orm import Session

from . import models as m, schemas as s
from .core import pwd_context
from .db import Base


def create_account(db: Session, account: s.AccountCreate):
    account_dict = {
        **account.dict(),
        **{
            "password": pwd_context.hash(account.password),
        },
    }
    return _create(db, m.Account(**account_dict))


def get_account(db: Session, account_id: int):
    return _fetch_by_id(db, m.Account, account_id)


def get_account_by_email(db: Session, email: str):
    return _fetch_by_id(db, m.Account, email, db_col="email")


def _fetch_by_id(db: Session, db_model, db_id: int, db_col: str = "id"):
    return db.query(db_model).filter(getattr(db_model, db_col) == db_id).first()


def _create(db: Session, db_model: Base):
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model
