from unittest.mock import patch

import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from app.database.models.user import User
from app.internal.auth import _create_tokens, register
from app.schemas.auth import PostUserScheme

TEST_USER = {
    "name": "Alice",
    "phone": "+79999999990",
    "password": "randompassword",
}
TEST_USER2 = {
    "name": "Bob",
    "phone": "+79239999990",
    "password": "notAlicePassword",
}


class FakeRedis:
    def __init__(self):
        self.data = {}

    async def set(self, key, data):
        self.data[key] = data

    async def get(self, key):
        return self.data.get(key, None)

    async def delete(self, key):
        self.data.pop(key, None)


class TestUser:
    pytestmark = pytest.mark.asyncio

    @pytest.mark.parametrize("user_data", [TEST_USER, TEST_USER2])
    @patch("app.internal.deps.get_async_redis")
    async def test_get_user_by_id(
        self, mock_get_redis, client, session, user_data
    ):
        mock_get_redis.return_value = FakeRedis()
        user = await register(session, PostUserScheme(**user_data))
        response = await client.get(f"/api/v1/users/{user.id}")
        received_data = response.json()
        assert response.status_code == HTTP_200_OK
        assert received_data["name"] == user.name

    @patch("app.internal.deps.get_async_redis")
    async def test_get_user_by_id_404(self, mock_get_redis, client, session):
        mock_get_redis.return_value = FakeRedis()
        user = await register(session, PostUserScheme(**TEST_USER))
        response = await client.get(f"/api/v1/users/{user.id + 1}")

        assert response.status_code == HTTP_404_NOT_FOUND
        assert list(response.json()) == ["detail"]

    async def test_get_user_all(self, client, session):
        [
            await register(session, PostUserScheme(**user))
            for user in [TEST_USER, TEST_USER2]
        ]

        response = await client.get("/api/v1/users")
        received_data = response.json()

        assert response.status_code == HTTP_200_OK
        assert len(received_data) == 2
        assert "name" in received_data[0]
        assert "id" in received_data[0]
        assert "phone" in received_data[0]

        assert "name" in received_data[1]
        assert "id" in received_data[1]
        assert "phone" in received_data[1]

    @patch("app.internal.deps.get_async_redis")
    async def test_put_user_by_id(self, mock_get_redis, client, session):
        mock_get_redis.return_value = FakeRedis()
        user = await register(session, PostUserScheme(**TEST_USER))
        user_db = await session.get(User, user.id)
        tokens = await _create_tokens(user_db)
        response = await client.put(
            f"/api/v1/users/{user.id}",
            json={"phone": "89999999990", "name": "Alex"},
            headers={"Authorization": f"Bearer {tokens['access']}"},
        )
        assert response.status_code == HTTP_200_OK
        received_data = response.json()
        assert received_data["phone"] == "89999999990"
        assert received_data["name"] == "Alex"

    @patch("app.internal.deps.get_async_redis")
    async def test_put_user_by_id_403(self, mock_get_redis, client, session):
        mock_get_redis.return_value = FakeRedis()
        user = await register(session, PostUserScheme(**TEST_USER))
        user_db = await session.get(User, user.id)
        tokens = await _create_tokens(user_db)
        response = await client.put(
            f"/api/v1/users/{user.id}",
            json={"phone": "89999999990", "name": "Alex"},
            headers={"Authorization": f"Bearer {tokens['refresh']}"},
        )
        assert response.status_code == HTTP_403_FORBIDDEN
        assert list(response.json()) == ["detail"]

    @patch("app.internal.deps.get_async_redis")
    async def test_put_user_by_id_no_token(
        self, mock_get_redis, client, session
    ):
        mock_get_redis.return_value = FakeRedis()
        user = await register(session, PostUserScheme(**TEST_USER))
        response = await client.put(f"/api/v1/users/{user.id + 1}")

        assert response.status_code == HTTP_401_UNAUTHORIZED
        assert list(response.json()) == ["detail"]
