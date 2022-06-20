import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.deps import get_async_session
from app.database.models.user import User
from app.internal import auth as auth_internal
from app.internal.auth import get_refresh_user
from app.schemas.auth import AuthStatus, LoginScheme, PostUserScheme
from app.schemas.message import Message
from app.schemas.user import GetUserScheme

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    summary="Регистрация нового пользователя",
    response_model=GetUserScheme,
)
async def register(
    register_data: PostUserScheme,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await auth_internal.register(session, register_data)
    except HTTPException as http_error:
        logging.error(http_error.args)
        raise http_error
    except Exception as error:
        logging.error(error.args)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренная ошибка сервера",
        )


@router.post(
    "/login",
    response_model=AuthStatus,
    summary="Авторизация существующего пользователя",
    responses={403: {"model": Message}},
)
async def login(
    login_data: LoginScheme,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await auth_internal.login(session, login_data)
    except HTTPException as http_error:
        logging.error(http_error.args)
        raise http_error
    except Exception as error:
        logging.error(error.args)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренная ошибка сервера",
        )


@router.post(
    "/refresh",
    response_model=AuthStatus,
    summary="Получение новых токенов",
    description="Принимает Refresh в качестве Authorization Token",
    responses={403: {"model": Message}},
)
async def refresh(
    user: User = Depends(get_refresh_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await auth_internal.refresh(session, user)
    except HTTPException as http_error:
        logging.error(http_error.args)
        raise http_error
    except Exception as error:
        logging.error(error.args)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренная ошибка сервера",
        )
