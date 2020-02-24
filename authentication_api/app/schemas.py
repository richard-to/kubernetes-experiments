from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


class AccountBase(BaseModel):
    email: str


class AccountCreate(AccountBase):
    password: str


class Account(AccountBase):
    id: int
    active: bool

    class Config:
        orm_mode = True
