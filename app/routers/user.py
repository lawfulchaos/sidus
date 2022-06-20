import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_403_FORBIDDEN

from app.database.deps import get_async_session
from app.database.models.user import User
from app.internal import user as user_internal
from app.internal.auth import get_current_user
from app.schemas.message import Message
from app.schemas.user import GetUserScheme, PutUserScheme

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "/{user_id}",
    response_model=GetUserScheme,
    responses={404: {"model": Message}},
    summary="Получение конкретного пользователя",
)
async def get_user(
    user_id: int = Query(0, description="ID пользователя"),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await user_internal.get_by_id(session, user_id)
    except HTTPException as http_error:
        logging.error(http_error.args)
        raise http_error
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} does not exist",
        )
    except Exception as error:
        logging.error(error.args)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренная ошибка сервера",
        )


@router.get(
    "",
    response_model=List[GetUserScheme],
    summary="Получение списка всех пользователей",
)
async def get_user_all(
    session: AsyncSession = Depends(get_async_session),
    id__gt: int = Query(0, description="Пропустить N значений"),
):
    try:
        return await user_internal.get_all(session, id__gt)
    except HTTPException as http_error:
        logging.error(http_error.args)
        raise http_error
    except Exception as error:
        logging.error(error.args)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренная ошибка сервера",
        )


@router.put(
    "/{user_id}",
    response_model=GetUserScheme,
    responses={404: {"model": Message}, 403: {"model": Message}},
    summary="Получение конкретного пользователя",
)
async def put_user(
    user_id: int,
    user_info: PutUserScheme,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    if user.id != user_id:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Unautorized"
        )
    try:
        return await user_internal.change_user(session, user, user_info)
    except HTTPException as http_error:
        logging.error(http_error.args)
        raise http_error
    except Exception as error:
        logging.error(error.args)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренная ошибка сервера",
        )
