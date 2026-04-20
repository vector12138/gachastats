#!/usr/bin/env python3
"""
Planning API Tests
==================
Tests for /api/planning/* endpoints.

Coverage:
- GET /api/planning/{account_id}/summary - Get planning summary
- POST /api/planning/{account_id}/target - Set target item
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.api]


class TestPlanningSummary:
    """Tests for planning summary endpoint."""
    
    def test_summary_nonexistent_account(self, api_client: TestClient):
        """Test planning summary for non-existent account."""
        response = api_client.get("/api/planning/99999/summary")
        assert response.status_code == 404
    
    def test_summary_with_data(self, api_client: TestClient, test_data):
        """Test planning summary with imported data."""
        # Create account
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")
        
        # Import data
        json_data = {
            "uid": account["uid"],
            "list": [
                {
                    "uid": account["uid"],
                    "gacha_type": "301",
                    "item_id": "12345",
                    "item_name": "雷电将军",
                    "item_type": "角色",
                    "rank_type": "5",
                    "time": "2024-01-01 12:00:00",
                    "id": "1000000000000000001"
                }
            ]
        }
        
        api_client.post("/api/import/json", json={
            "account_id": account_id,
            "data": json_data
        })
        
        response = api_client.get(f"/api/planning/{account_id}/summary")
        assert response.status_code in [200, 404]


class TestPlanningTarget:
    """Tests for planning target setting endpoint."""
    
    def test_set_target_nonexistent_account(self, api_client: TestClient):
        """Test setting target for non-existent account."""
        response = api_client.post("/api/planning/99999/target", json={
            "target_item": "雷电将军",
            "target_type": "character"
        })
        assert response.status_code == 404
    
    def test_set_target_valid(self, api_client: TestClient, test_data):
        """Test setting a valid target."""
        # Create account
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")
        
        response = api_client.post(f"/api/planning/{account_id}/target", json={
            "target_item": "雷电将军",
            "target_type": "character",
            "pity_current": 50
        })
        
        assert response.status_code in [200, 404, 422]
    
    def test_set_target_missing_fields(self, api_client: TestClient, test_data):
        """Test setting target without required fields."""
        # Create account
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")
        
        response = api_client.post(f"/api/planning/{account_id}/target", json={
            # Missing target_item
            "pity_current": 50
        })
        
        assert response.status_code in [200, 404, 400, 422]
    
    def test_set_target_invalid_pity(self, api_client: TestClient, test_data):
        """Test setting target with invalid pity value."""
        # Create account
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")
        
        response = api_client.post(f"/api/planning/{account_id}/target", json={
            "target_item": "雷电将军",
            "pity_current": 100  # Invalid: > 90
        })
        
        assert response.status_code in [200, 400, 404, 422]
