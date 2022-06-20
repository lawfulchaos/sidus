import pytest
from sqlalchemy import select
from starlette.status import (
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
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


class TestAuth:
    pytestmark = pytest.mark.asyncio

    async def test_register(self, client, session):
        response = await client.post(
            "/api/v1/auth/register",
            json=TEST_USER,
        )
        assert response.status_code == HTTP_200_OK

        received_data = response.json()
        assert "id" in received_data
        assert received_data["name"] == "Alice"
        assert received_data["phone"] == "+79999999990"

        users_db = (await session.execute(select(User))).scalars().all()

        assert len(users_db) == 1
        assert users_db[0].id == received_data["id"]

    async def test_register_empty(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={},
        )
        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    async def test_login(self, client, session):
        await register(session, PostUserScheme(**TEST_USER2))
        response = await client.post(
            "/api/v1/auth/login",
            json={"login": "+79239999990", "password": "notAlicePassword"},
        )
        assert response.status_code == HTTP_200_OK

    async def test_login_incorrect(self, client, session):
        await register(session, PostUserScheme(**TEST_USER2))
        response = await client.post(
            "/api/v1/auth/login",
            json={"login": "+79239999990", "password": "AlicePassword"},
        )
        assert response.status_code == HTTP_403_FORBIDDEN

    async def test_login_empty(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={},
        )

        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    async def test_refresh(self, client, session):
        await register(session, PostUserScheme(**TEST_USER2))
        user_db = (await session.execute(select(User))).scalars().all()[0]
        tokens = await _create_tokens(user_db)
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {tokens['refresh']}"},
        )
        assert response.status_code == HTTP_200_OK
        received_data = response.json()
        assert list(received_data) == ["access_token", "refresh_token"]
        await session.refresh(user_db)
        assert received_data["refresh_token"] == user_db.refresh_token

    async def test_refresh_wrong(self, client, session):
        await register(session, PostUserScheme(**TEST_USER2))
        user_db = (await session.execute(select(User))).scalars().all()[0]
        tokens = await _create_tokens(user_db)
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {tokens['access']}"},
        )
        assert response.status_code == HTTP_403_FORBIDDEN
        received_data = response.json()
        assert list(received_data) == ["detail"]
