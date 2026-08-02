import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.db import engine
from app.core.redis_client import redis_client

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers(client):
    import uuid
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    resp = await client.post("/auth/register", json={"username": username, "password": "testpass123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
async def cleanup_connections_after_test():
    yield
    await engine.dispose()
    await redis_client.connection_pool.disconnect()
