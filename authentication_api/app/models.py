from sqlalchemy import Boolean, Column, Integer, String

from .db import Base


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    active = Column(Boolean, default=True)
