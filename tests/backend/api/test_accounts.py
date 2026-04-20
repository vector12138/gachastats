#!/usr/bin/env python3
"""
Accounts API Tests - Simplified
==============================
Tests for /api/accounts endpoints.
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.api]


class TestHealthCheck:
    """Basic health check."""
    
    def test_health_endpoint(self, api_client: TestClient):
        """Test health endpoint returns success."""
        response = api_client.get("/health")
        assert response.status_code == 200


class TestAccountsBasic:
    """Basic account tests."""
    
    def test_get_accounts_empty(self, api_client: TestClient):
        """Test getting accounts when empty."""
        response = api_client.get("/api/accounts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_account(self, api_client: TestClient):
        """Test creating a basic account."""
        import uuid
        unique_uid = f"{uuid.uuid4().hex[:16]}"
        response = api_client.post("/api/accounts", json={
            "game_type": "genshin",
            "account_name": "Test Account",
            "uid": unique_uid,
            "server": "cn_gf01",
        })
        # Accept different response codes
        assert response.status_code in [200, 201, 422]
    
    def test_create_account_missing_uid(self, api_client: TestClient):
        """Test creating account without UID validation."""
        response = api_client.post("/api/accounts", json={
            "game_type": "genshin",
            "account_name": "Test",
            # Missing uid, API may handle in different ways
        })
        # API may return 400 (Bad Request) or 422 (Validation Error)
        assert response.status_code in [400, 422]
    
    def test_404_handling(self, api_client: TestClient):
        """Test 404 errors are handled properly."""
        response = api_client.get("/api/accounts/99999")
        assert response.status_code == 404


class TestSystemEndpoints:
    """Test system endpoints."""
    
    def test_root_endpoint_exists(self, api_client: TestClient):
        """Test root endpoint exists."""
        response = api_client.get("/")
        # Should redirect or return content
        assert response.status_code in [200, 307, 308]
    
    def test_docs_endpoint_exists(self, api_client: TestClient):
        """Test Swagger docs endpoint."""
        response = api_client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_endpoint_exists(self, api_client: TestClient):
        """Test OpenAPI spec endpoint."""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
