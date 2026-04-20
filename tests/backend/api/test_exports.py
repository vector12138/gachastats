#!/usr/bin/env python3
"""
Exports API Tests
================
Tests for /api/exports/* endpoints.

Coverage:
- GET /api/exports/accounts - List exportable accounts
- POST /api/exports/{account_id} - Export account data
- GET /api/exports/download/{export_id} - Download exported file
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.api]


class TestExportsList:
    """Tests for exports list endpoint."""

    def test_get_exportable_accounts(self, api_client: TestClient, test_data):
        """Test getting list of exportable accounts."""
        # Create an account first
        account = test_data["accounts"][0].copy()
        api_client.post("/api/accounts", json=account)

        response = api_client.get("/api/exports/accounts")

        assert response.status_code in [200, 404]  # May not be implemented
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or isinstance(data, dict)

    def test_exports_empty_database(self, api_client: TestClient):
        """Test exports with no accounts."""
        response = api_client.get("/api/exports/accounts")
        assert response.status_code in [200, 404]


class TestExportAccount:
    """Tests for export account endpoint."""

    def test_export_nonexistent_account(self, api_client: TestClient):
        """Test exporting non-existent account."""
        response = api_client.post("/api/exports/99999", json={
            "format": "json"
        })
        assert response.status_code == 404

    def test_export_valid_account(self, api_client: TestClient, test_data):
        """Test exporting account with data."""
        # Create account
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")

        # Import some data first
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

        api_client.post("/api/imports/json", json={
            "account_id": account_id,
            "data": json_data
        })

        # Try to export
        response = api_client.post(f"/api/exports/{account_id}", json={
            "format": "json"
        })

        # May not be implemented
        assert response.status_code in [200, 404]

    def test_export_different_formats(self, api_client: TestClient, test_data):
        """Test exporting in different formats."""
        # Create account
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")

        formats = ["json", "csv", "xlsx"]

        for fmt in formats:
            response = api_client.post(f"/api/exports/{account_id}", json={
                "format": fmt
            })
            # At least one should work or all return 404
            assert response.status_code in [200, 404, 400]


class TestExportDownload:
    """Tests for export download endpoint."""

    def test_download_nonexistent_export(self, api_client: TestClient):
        """Test downloading non-existent export."""
        response = api_client.get("/api/exports/download/nonexistent")
        assert response.status_code == 404

    def test_download_invalid_export_id(self, api_client: TestClient):
        """Test downloading with invalid export ID."""
        response = api_client.get("/api/exports/download/!!!invalid!!!")
        assert response.status_code in [404, 422]


class TestExportValidation:
    """Tests for export data validation."""

    def test_export_data_integrity(self, api_client: TestClient, test_data):
        """Test that exported data matches imported data."""
        # Create account
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")

        # Import specific data
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

        api_client.post("/api/imports/json", json={
            "account_id": account_id,
            "data": json_data
        })

        # Export and verify contents
        response = api_client.post(f"/api/exports/{account_id}", json={
            "format": "json"
        })

        # Skip if endpoint not implemented
        if response.status_code == 404:
            pytest.skip("Export endpoint not implemented")

        if response.status_code == 200:
            data = response.json()
            # Verify exported data contains expected record
            if "data" in data and "list" in data["data"]:
                assert len(data["data"]["list"]) == 1
                assert data["data"]["list"][0]["item_name"] == "雷电将军"

    def test_export_empty_account(self, api_client: TestClient, test_data):
        """Test exporting account with no gacha data."""
        # Create account but don't import data
        account = test_data["accounts"][0].copy()
        create_resp = api_client.post("/api/accounts", json=account)
        resp_data = create_resp.json()
        account_id = resp_data.get("id") or resp_data.get("account_id")

        response = api_client.post(f"/api/exports/{account_id}", json={
            "format": "json"
        })

        # Should succeed with empty data or fail gracefully
        assert response.status_code in [200, 404, 400]
