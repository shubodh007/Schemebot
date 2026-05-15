from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_liveness(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_version(client: AsyncClient):
    response = await client.get("/api/v1/health/version")
    assert response.status_code == 200
    assert "version" in response.json()
    assert response.json()["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "GovScheme AI"


@pytest.mark.asyncio
async def test_list_schemes(client: AsyncClient):
    response = await client.get("/api/v1/schemes")
    assert response.status_code == 200
    assert "schemes" in response.json()


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient):
    response = await client.get("/api/v1/schemes/categories")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_search_schemes(client: AsyncClient):
    response = await client.get("/api/v1/search?q=education")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_search_suggestions(client: AsyncClient):
    response = await client.get("/api/v1/search/suggestions?q=kisan")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_route_without_auth(client: AsyncClient):
    response = await client.post("/api/v1/chat/sessions", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_document_upload_without_auth(client: AsyncClient):
    response = await client.post("/api/v1/documents/upload")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_route_as_citizen(client: AsyncClient, auth_headers):
    response = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert response.status_code == 403
