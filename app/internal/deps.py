import aioredis

from app.settings import Settings

settings = Settings.get()


async def get_async_redis(db_num: int = 0) -> aioredis.Redis:
    return aioredis.from_url(settings.redis_host, db=db_num)
