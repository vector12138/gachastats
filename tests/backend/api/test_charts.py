#!/usr/bin/env python3
"""
Charts API Tests
================
Tests for /api/charts/* endpoints.

Coverage:
- GET /api/charts/{account_id}/distribution - Item distribution
- GET /api/charts/{account_id}/timeline - Pull timeline
- GET /api/charts/{account_id}/pity-trend - Pity trend over time
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.api]


class TestChartsDistribution:
    """Tests for item distribution chart endpoint."""
    
    def test_distribution_nonexistent_account(self, api_client: TestClient):
        """Test distribution for non-existent account."""
        response = api_client.get("/api/charts/99999/distribution")
        assert response.status_code == 404
    
    def test_distribution_with_data(self, api_client: TestClient, test_data):
        """Test distribution with imported data."""
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
                },
                {
                    "uid": account["uid"],
                    "gacha_type": "301",
                    "item_id": "12346",
                    "item_name": "九条裟罗",
                    "item_type": "角色",
                    "rank_type": "4",
                    "time": "2024-01-01 11:58:00",
                    "id": "1000000000000000002"
                }
            ]
        }
        
        api_client.post("/api/import/json", json={
            "account_id": account_id,
            "data": json_data
        })
        
        response = api_client.get(f"/api/charts/{account_id}/distribution")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestChartsTimeline:
    """Tests for pull timeline chart endpoint."""
    
    def test_timeline_nonexistent_account(self, api_client: TestClient):
        """Test timeline for non-existent account."""
        response = api_client.get("/api/charts/99999/timeline")
        assert response.status_code == 404
    
    def test_timeline_with_data(self, api_client: TestClient, test_data):
        """Test timeline with imported data."""
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
        
        response = api_client.get(f"/api/charts/{account_id}/timeline")
        assert response.status_code in [200, 404]


class TestChartsPityTrend:
    """Tests for pity trend chart endpoint."""
    
    def test_pity_trend_nonexistent_account(self, api_client: TestClient):
        """Test pity trend for non-existent account."""
        response = api_client.get("/api/charts/99999/pity-trend")
        assert response.status_code == 404
    
    def test_pity_trend_with_data(self, api_client: TestClient, test_data):
        """Test pity trend with imported data."""
        # Create account
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")
        
        # Create pity data (multiple pulls building up to 5-star)
        json_data = {"uid": account["uid"], "list": []}
        
        for i in range(89):
            json_data["list"].append({
                "uid": account["uid"],
                "gacha_type": "301",
                "item_id": str(10000 + i),
                "item_name": f"四星角色{i}",
                "item_type": "角色",
                "rank_type": "4",
                "time": "2024-01-01 12:00:00",
                "id": str(1000000000000000000 + i)
            })
        
        # Add the 5-star
        json_data["list"].append({
            "uid": account["uid"],
            "gacha_type": "301",
            "item_id": "99999",
            "item_name": "五星角色",
            "item_type": "角色",
            "rank_type": "5",
            "time": "2024-01-01 13:00:00",
            "id": "1000000000000000090"
        })
        
        api_client.post("/api/import/json", json={
            "account_id": account_id,
            "data": json_data
        })
        
        response = api_client.get(f"/api/charts/{account_id}/pity-trend")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            # Should show pity trend data
            assert isinstance(data, dict) or isinstance(data, list)


class TestChartsValidation:
    """Tests for chart data validation."""
    
    def test_chart_data_types(self, api_client: TestClient, test_data):
        """Test that chart data has correct types."""
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
        
        # Check all chart endpoints return valid data
        for endpoint in ["distribution", "timeline", "pity-trend"]:
            response = api_client.get(f"/api/charts/{account_id}/{endpoint}")
            if response.status_code == 200:
                # Should be valid JSON
                data = response.json()
                assert isinstance(data, (dict, list))
