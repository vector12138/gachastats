"""Test configuration and shared utilities."""

import os
import sys
from pathlib import Path
from typing import Generator

import pytest

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Server configuration  
TEST_SERVER_HOST = os.getenv("TEST_SERVER_HOST", "127.0.0.1")
TEST_SERVER_PORT = int(os.getenv("TEST_SERVER_PORT", "8777"))
TEST_BASE_URL = f"http://{TEST_SERVER_HOST}:{TEST_SERVER_PORT}"


@pytest.fixture(scope="session")
def api_client() -> Generator:
    """Create a test client for the FastAPI app."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from fastapi.testclient import TestClient
    from backend.main import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def test_data():
    """Provide test data fixtures."""
    import uuid
    return {
        "games": ["genshin", "starrail", "zzz", "zenless"],
        "servers": ["cn_gf01", "prod_gf_cn", "prod_official_asia"],
        "accounts": [
            {
                "game_type": "genshin",
                "account_name": f"Test Account {i}",
                "uid": f"{uuid.uuid4().hex[:10]}",
                "server": "cn_gf01",
            }
            for i in range(3)
        ],
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "browser: marks tests that require browser")
    config.addinivalue_line("markers", "live: marks tests that require a running server")
    config.addinivalue_line("markers", "unit: marks unit tests")
    config.addinivalue_line("markers", "api: marks API tests")


def pytest_collection_modifyitems(config, items):
    """Skip browser tests if playwright not available."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        skip_browser = pytest.mark.skip(reason="playwright not installed")
        for item in items:
            if "browser" in item.keywords:
                item.add_marker(skip_browser)
