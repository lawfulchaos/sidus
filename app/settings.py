from functools import lru_cache
from os import environ
from urllib.parse import quote_plus


class Settings:
    def __init__(self):
        self.host = environ.get("POSTGRES_HOST", None)
        self.port = environ.get("POSTGRES_PORT", None)
        self.database = environ.get("POSTGRES_DB", None)
        self.database_test = environ.get("POSTGRES_DB_TEST", None)
        self.user = environ.get("POSTGRES_USER", None)
        self.password = quote_plus(environ.get("POSTGRES_PASSWORD", ""))
        self.redis_host = environ.get("REDIS_URL", None)

        self.async_driver = "asyncpg"

        self.sync_connection_url = (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

        self.async_connection_url = (
            f"postgresql+{self.async_driver}://{self.user}:"
            f"{self.password}@{self.host}:{self.port}/{self.database}"
        )
        self.test_async_connection_url = (
            f"postgresql+{self.async_driver}://{self.user}:"
            f"{self.password}@{self.host}:{self.port}/{self.database_test}"
        )
        self.test_sync_connection_url = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database_test}"
        )

    @classmethod
    @lru_cache()
    def get(cls):
        return cls()
