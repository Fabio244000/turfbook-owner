import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.owner_profile.main import app

# Public contract: FastAPI docs live at the root, outside the API prefix.
OPENAPI_PATH = '/openapi.json'


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client


class TestOpenApi:
    async def test_publishes_the_openapi_document(self, client):
        response = await client.get(OPENAPI_PATH)

        assert response.status_code == 200
        assert response.json()['info']['title'] == 'TurfBook Owner Service'
