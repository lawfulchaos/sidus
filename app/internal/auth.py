import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseSettings, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.deps import get_async_session
from app.database.models.user import User
from app.schemas.auth import AuthStatus, LoginScheme, PostUserScheme
from app.schemas.user import GetUserScheme

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_PURPOSE = "access"
REFRESH_PURPOSE = "refresh"

CREDENTIAL_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class Settings(BaseSettings):
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(
        ..., env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        ..., env="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    algorithm: str = Field(..., env="ALGORITHM")


settings = Settings()


async def register(
    session: AsyncSession, user_data: PostUserScheme
) -> GetUserScheme:
    user_dict: dict = user_data.dict(exclude_unset=True)
    user_dict["password"] = bytes(
        pwd_context.hash(user_dict["password"]), encoding="utf-8"
    )
    user = User(**user_dict)
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return GetUserScheme.from_orm(user)


async def login(session: AsyncSession, login_data: LoginScheme) -> AuthStatus:
    user = (
        await session.execute(
            select(User).filter(User.phone == login_data.login).limit(1)
        )
    ).scalar()
    if not user:
        raise CREDENTIAL_EXCEPTION
    if pwd_context.verify(login_data.password, user.password):
        tokens = await _create_tokens(user)
        if user.refresh_token is None:
            user.refresh_token = tokens["refresh"]
            session.add(user)
            await session.commit()

        return AuthStatus(
            access_token=tokens["access"],
            refresh_token=tokens["refresh"],
        )
    raise CREDENTIAL_EXCEPTION


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=settings.algorithm
        )
    except JWTError:
        raise CREDENTIAL_EXCEPTION
    user = await session.get(User, int(payload.get("sub")))
    if user is None or payload.get("purpose") != ACCESS_PURPOSE:
        raise CREDENTIAL_EXCEPTION
    else:
        return user


async def refresh(
    session: AsyncSession,
    user: User,
) -> AuthStatus:
    tokens = await _create_tokens(user)
    user.refresh_token = tokens["refresh"]
    session.add(user)
    await session.commit()
    return AuthStatus(
        access_token=tokens["access"],
        refresh_token=tokens["refresh"],
    )


async def get_refresh_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=settings.algorithm
        )
    except JWTError:
        raise CREDENTIAL_EXCEPTION
    user = await session.get(User, int(payload.get("sub")))
    if user is None or payload.get("purpose") != REFRESH_PURPOSE:
        raise CREDENTIAL_EXCEPTION
    else:
        return user


async def _create_token(data: dict, expires_delta: datetime.timedelta) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": datetime.datetime.utcnow() + expires_delta})
    token = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.algorithm
    )
    return token


async def _create_tokens(user: User) -> dict:
    access = await _create_token(
        data={"sub": str(user.id), "purpose": ACCESS_PURPOSE},
        expires_delta=datetime.timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    )
    refresh = await _create_token(
        data={"sub": str(user.id), "purpose": REFRESH_PURPOSE},
        expires_delta=datetime.timedelta(
            days=settings.refresh_token_expire_days
        ),
    )
    return {"access": access, "refresh": refresh}
