from sqlalchemy import Column, Integer, LargeBinary, String

from app.database import deps as database_deps


class User(database_deps.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String, nullable=False, unique=True, index=True)
    password = Column(LargeBinary, nullable=False)
    refresh_token = Column(String)
