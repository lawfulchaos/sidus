import pickle
from typing import List

import aioredis
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

import app.internal.deps as internal_deps
from app.database.models.user import User
from app.schemas.user import GetUserScheme, PutUserScheme

PAGINATION_SIZE = 10


async def change_user(
    session: AsyncSession,
    user: User,
    user_info: PutUserScheme,
) -> GetUserScheme:
    redis: aioredis.Redis = await internal_deps.get_async_redis()
    user_dict = user_info.dict(exclude_unset=True)
    for key in user_dict:
        setattr(user, key, user_dict[key])
    session.add(user)
    await session.commit()
    await session.refresh(user)
    await redis.delete(str(user.id))
    return GetUserScheme.from_orm(user)


async def get_by_id(
    session: AsyncSession,
    user_id: int,
) -> GetUserScheme:
    redis: aioredis.Redis = await internal_deps.get_async_redis()
    cache = await redis.get(str(user_id))
    if cache:
        user_info = pickle.loads(cache)
    else:
        user = await session.get(User, user_id)
        if not user:
            raise NoResultFound
        user_info = GetUserScheme.from_orm(user)
        await redis.set(str(user_id), pickle.dumps(user_info))

    return user_info


async def get_all(session: AsyncSession, id__gt: int) -> List[GetUserScheme]:
    users = await session.execute(
        select(User).offset(id__gt).limit(PAGINATION_SIZE)
    )

    return [
        GetUserScheme.from_orm(db_user) for db_user in users.unique().scalars()
    ]
