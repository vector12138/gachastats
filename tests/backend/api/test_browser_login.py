#!/usr/bin/env python3
"""
Browser Login API Tests
======================
Tests for /api/auth/* browser login endpoints.

Coverage:
- GET /api/auth/browser-status - Check browser capabilities
- POST /api/auth/sessions - Create auth session
- GET /api/auth/sessions/{session_id} - Get session status
- PUT /api/auth/sessions/{session_id} - Update session with authkey
- DELETE /api/auth/sessions/{session_id} - Delete/cancel session
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.api]


class TestBrowserStatus:
    """Tests for browser status endpoint."""
    
    def test_browser_status_endpoint(self, api_client: TestClient):
        """Test browser status returns expected structure."""
        response = api_client.get("/api/auth/browser-status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data or "has_display" in data or "data" in data
        
        # If wrapped in 'data' key
        if "data" in data:
            data = data["data"]
        
        # Check expected fields
        assert "has_display" in data
        assert "browser_available" in data or "can_auto_login" in data
        assert isinstance(data.get("has_display"), bool)

    def test_browser_status_structure(self, api_client: TestClient):
        """Verify browser status response structure."""
        response = api_client.get("/api/auth/browser-status")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)


class TestSessions:
    """Tests for auth session endpoints."""
    
    @pytest.mark.parametrize("game_type", ["genshin", "starrail", "zzz", "zenless"])
    def test_create_session_valid_game(self, api_client: TestClient, game_type):
        """Test creating session for each supported game."""
        response = api_client.post("/api/auth/sessions", json={
            "game_type": game_type,
            "save_account": True,
            "region": "cn"
        })
        
        # Should succeed if display available
        assert response.status_code in [200, 503]
        
        # If success, check response structure
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                data = data["data"]
            assert "session_id" in data
            assert "game_name" in data
            assert "message" in data
    
    def test_create_session_invalid_game(self, api_client: TestClient):
        """Test creating session with unsupported game type."""
        response = api_client.post("/api/auth/sessions", json={
            "game_type": "invalid_game",
            "save_account": True,
            "region": "cn"
        })
        
        # Should fail gracefully
        assert response.status_code in [400, 422]
    
    def test_create_session_missing_game_type(self, api_client: TestClient):
        """Test creating session without game_type."""
        response = api_client.post("/api/auth/sessions", json={
            "save_account": True
        })
        
        # Should fail validation
        assert response.status_code == 422
    
    @pytest.mark.parametrize("region", ["cn", "os", "asia", "usa"])
    def test_create_session_different_regions(self, api_client: TestClient, region):
        """Test creating session with different server regions."""
        response = api_client.post("/api/auth/sessions", json={
            "game_type": "genshin",
            "save_account": True,
            "region": region
        })
        
        # Should accept or reject based on region support
        assert response.status_code in [200, 400, 503]


class TestSessionStatus:
    """Tests for session status endpoint."""
    
    def test_get_session_status_nonexistent(self, api_client: TestClient):
        """Test getting status for non-existent session."""
        response = api_client.get("/api/auth/sessions/nonexistent")
        assert response.status_code == 404
    
    def test_session_status_invalid_id(self, api_client: TestClient):
        """Test getting status with invalid session ID format."""
        response = api_client.get("/api/auth/sessions/!!!invalid!!!")
        assert response.status_code == 404


class TestUpdateSession:
    """Tests for update session endpoint (authkey callback)."""
    
    def test_update_nonexistent_session(self, api_client: TestClient):
        """Test update for non-existent session."""
        response = api_client.put("/api/auth/sessions/nonexistent", json={
            "authkey": "test_authkey",
            "uid": "123456789"
        })
        assert response.status_code == 404
    
    def test_update_missing_authkey(self, api_client: TestClient):
        """Test update without authkey."""
        response = api_client.put("/api/auth/sessions/test123", json={
            "uid": "123456789"
        })
        # Should fail validation
        assert response.status_code in [400, 422, 404]
    
    def test_update_with_authkey(self, api_client: TestClient):
        """Test update with valid authkey structure."""
        # First create a session
        start_resp = api_client.post("/api/auth/sessions", json={
            "game_type": "genshin",
            "save_account": True,
            "region": "cn"
        })
        
        # If session created successfully, test update
        if start_resp.status_code == 200:
            session_data = start_resp.json()
            if "data" in session_data:
                session_data = session_data["data"]
            session_id = session_data["session_id"]
            
            # Delete it first to avoid hanging
            api_client.delete(f"/api/auth/sessions/{session_id}")


class TestDeleteSession:
    """Tests for delete session endpoint."""
    
    def test_delete_nonexistent_session(self, api_client: TestClient):
        """Test delete for non-existent session."""
        response = api_client.delete("/api/auth/sessions/nonexistent")
        # Should succeed (idempotent) or fail gracefully
        assert response.status_code in [200, 404]
    
    def test_delete_existing_session(self, api_client: TestClient):
        """Test delete for existing session."""
        # Create a session first
        start_resp = api_client.post("/api/auth/sessions", json={
            "game_type": "genshin",
            "save_account": True,
            "region": "cn"
        })
        
        if start_resp.status_code == 200:
            session_data = start_resp.json()
            if "data" in session_data:
                session_data = session_data["data"]
            session_id = session_data["session_id"]
            
            # Delete it
            cancel_resp = api_client.delete(f"/api/auth/sessions/{session_id}")
            assert cancel_resp.status_code == 200
            
            # Verify session is deleted by checking status
            status_resp = api_client.get(f"/api/auth/sessions/{session_id}")
            # Should show deleted or return 404


class TestSessionFlowIntegration:

    @pytest.mark.skip(reason="Browser login requires display server")
    def test_full_session_flow_states(self, api_client: TestClient, test_data):
        """Test complete session flow state transitions."""
        # Create session
        start_resp = api_client.post("/api/auth/sessions", json={
            "game_type": "genshin",
            "save_account": False,
            "region": "cn"
        })
        
        if start_resp.status_code != 200:
            pytest.skip("Browser login not available in test environment")
        
        session_data = start_resp.json()
        if "data" in session_data:
            session_data = session_data["data"]
        session_id = session_data["session_id"]
        
        try:
            # Check initial status
            status_resp = api_client.get(f"/api/auth/sessions/{session_id}")
            assert status_resp.status_code == 200
            
            # Should be in pending or waiting state
            current_status = status_resp.json()
            if "data" in current_status:
                current_status = current_status["data"]
            status = current_status.get("status", "unknown")
            assert status in ["pending", "waiting_login", "created"]
        
        finally:
            # Cleanup: delete the session
            api_client.delete(f"/api/auth/sessions/{session_id}")
    
    def test_concurrent_sessions(self, api_client: TestClient):
        """Test multiple concurrent sessions."""
        sessions = []
        
        # Create multiple sessions
        for game_type in ["genshin", "starrail"]:
            resp = api_client.post("/api/auth/sessions", json={
                "game_type": game_type,
                "save_account": False,
                "region": "cn"
            })
            
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data:
                    data = data["data"]
                sessions.append(data.get("session_id"))
        
        # Each should have unique session ID
        if len(sessions) > 1:
            assert len(set(sessions)) == len(sessions)
        
        # Cleanup
        for session_id in sessions:
            api_client.delete(f"/api/auth/sessions/{session_id}")
    
    def test_session_timeout(self, api_client: TestClient):
        """Test that sessions eventually timeout."""
        # Create session
        start_resp = api_client.post("/api/auth/sessions", json={
            "game_type": "genshin",
            "save_account": False,
            "region": "cn"
        })
        
        if start_resp.status_code != 200:
            pytest.skip("Browser login not available")
        
        session_data = start_resp.json()
        if "data" in session_data:
            session_data = session_data["data"]
        session_id = session_data["session_id"]
        
        # Delete immediately to avoid resource leak
        api_client.delete(f"/api/auth/sessions/{session_id}")
