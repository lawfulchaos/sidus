from typing import Optional

from pydantic import BaseModel


class PostUserScheme(BaseModel):
    name: str
    phone: str
    password: str


class LoginScheme(BaseModel):
    login: str
    password: str


class AuthStatus(BaseModel):
    access_token: Optional[str]
    refresh_token: Optional[str]
