from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from .config import TOKEN_URL

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)
