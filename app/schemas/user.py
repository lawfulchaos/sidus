from typing import Optional

from pydantic import BaseModel


class GetUserScheme(BaseModel):
    id: int
    name: str
    phone: str

    class Config:
        orm_mode = True


class PutUserScheme(BaseModel):
    name: Optional[str]
    phone: Optional[str]
