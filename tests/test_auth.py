"""Authentication behavior without loading the LLM/RAG application stack."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.api.v1.auth import router
from backend.database.connection import Base, get_session


@pytest.mark.asyncio
async def test_signup_login_and_me(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'auth.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def test_session():
        async with sessions() as session:
            yield session

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_session] = test_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        signup = await client.post("/api/v1/auth/signup", json={
            "name": "Test Student", "email": "student@example.com", "password": "password123"
        })
        assert signup.status_code == 201
        token = signup.json()["access_token"]

        duplicate = await client.post("/api/v1/auth/signup", json={
            "name": "Duplicate", "email": "student@example.com", "password": "password123"
        })
        assert duplicate.status_code == 409

        denied = await client.get("/api/v1/auth/me")
        assert denied.status_code == 401

        me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "student@example.com"

        login = await client.post("/api/v1/auth/login", json={
            "email": "student@example.com", "password": "password123"
        })
        assert login.status_code == 200

        bad_login = await client.post("/api/v1/auth/login", json={
            "email": "student@example.com", "password": "wrong"
        })
        assert bad_login.status_code == 401

    await engine.dispose()
