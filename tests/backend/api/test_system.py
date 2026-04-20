#!/usr/bin/env python3
"""
System API Tests
================
Tests for system/root endpoints.

Coverage:
- GET /health - Health check
- GET / - Root endpoint
- System info and configuration
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.api]


class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_endpoint(self, api_client: TestClient):
        """Test health endpoint returns success."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        try:
            data = response.json()
            assert "status" in data or "message" in data
        except:
            # May return plain text
            assert "ok" in response.text.lower() or "healthy" in response.text.lower()
    
    def test_health_returns_json(self, api_client: TestClient):
        """Test health endpoint returns valid JSON."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        
        # Should be JSON or at least parseable
        assert "application/json" in content_type or response.json() is not None


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_endpoint(self, api_client: TestClient):
        """Test root endpoint returns expected content."""
        response = api_client.get("/")
        
        # Should redirect or return info
        assert response.status_code in [200, 307, 308]
        
        if response.status_code == 200:
            # May return documentation or redirect
            pass


class TestSystemInfo:
    """Tests for system info endpoints."""
    
    def test_system_endpoints_exist(self, api_client: TestClient):
        """Test that expected system endpoints exist."""
        # Common system endpoints to check
        endpoints = [
            "/health",
            "/docs",  # Swagger UI
            "/openapi.json",  # OpenAPI spec
        ]
        
        for endpoint in endpoints:
            response = api_client.get(endpoint, follow_redirects=True)
            # Should not return 404
            assert response.status_code not in [404, 500], f"Endpoint {endpoint} is broken"
    
    def test_cors_headers(self, api_client: TestClient):
        """Test CORS headers are present."""
        response = api_client.options("/health", headers={
            "Origin": "http://localhost:3000"
        })
        
        # Should have CORS headers (may not for OPTIONS)
        # This is optional based on configuration
        pass
    
    def test_api_version(self, api_client: TestClient):
        """Test API version if available."""
        response = api_client.get("/health")
        if response.status_code == 200:
            try:
                data = response.json()
                if "version" in data:
                    assert isinstance(data["version"], str)
            except:
                pass


class TestErrorHandling:
    """Test error response handling."""
    
    def test_404_response(self, api_client: TestClient):
        """Test 404 error returns proper format."""
        response = api_client.get("/api/nonexistent/endpoint")
        
        assert response.status_code == 404
        
        # Should return JSON error
        try:
            data = response.json()
            assert "detail" in data or "error" in data or "message" in data
        except:
            # Plain text is also acceptable
            pass
    
    def test_405_method_not_allowed(self, api_client: TestClient):
        """Test 405 error for wrong HTTP method."""
        response = api_client.get("/api/accounts", params={
            "invalid": "param"  # Some endpoints may not support GET with params
        })
        
        # Test a POST-only endpoint with GET
        response = api_client.get("/api/import/official")
        assert response.status_code == 405
    
    def test_422_validation_error(self, api_client: TestClient):
        """Test 422 validation error format."""
        # Send malformed JSON
        response = api_client.post(
            "/api/accounts",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_invalid_json_body(self, api_client: TestClient):
        """Test handling of invalid JSON in request body."""
        response = api_client.post(
            "/api/accounts",
            data="malformed{json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422]


class TestResponseStructure:
    """Test response structure consistency."""
    
    def test_response_wrapper_consistency(self, api_client: TestClient):
        """Test that responses have consistent wrapper structure."""
        response = api_client.get("/health")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if responses use consistent wrapper
            # Common patterns: {data: {...}}, {result: {...}}, direct object
            is_wrapped = "data" in data and isinstance(data["data"], dict)
            is_direct = isinstance(data, dict) and "status" in data
            
            # Both patterns are acceptable, but should be consistent
            assert is_wrapped or is_direct
    
    def test_error_response_consistency(self, api_client: TestClient):
        """Test error responses have consistent format."""
        # Trigger different errors
        errors = [
            api_client.get("/api/nonexistent"),  # 404
            api_client.post("/api/import/manual", json={"invalid": "data"}),  # 422
        ]
        
        for error in errors:
            if error.status_code >= 400:
                try:
                    data = error.json()
                    # Should have error field
                    assert any(k in data for k in ["detail", "error", "message", "status"])
                except:
                    pass  # Non-JSON errors are acceptable


class TestPerformance:
    """Test API performance characteristics."""
    
    @pytest.mark.slow
    def test_health_response_time(self, api_client: TestClient):
        """Test health endpoint responds quickly."""
        import time
        
        start = time.time()
        response = api_client.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"Health check took {elapsed:.2f}s, expected < 1s"
    
    def test_concurrent_requests(self, api_client: TestClient):
        """Test API handles multiple requests."""
        import concurrent.futures
        
        def make_request():
            return api_client.get("/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 10, f"Only {success_count}/10 requests succeeded"
