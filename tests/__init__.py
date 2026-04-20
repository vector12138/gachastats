"""
GachaStats Test Suite
=====================

Complete test framework for GachaStats application.

Structure:
    - backend/api: API endpoint tests (FastAPI + httpx)
    - backend/unit: Unit tests for internal functions
    - frontend/e2e: End-to-end browser tests (Playwright)
    - fixtures: Test data and utilities
    - reports: Test results and coverage reports

Usage:
    # Run all tests
    pytest tests/ -v
    
    # Run backend tests only
    pytest tests/backend/ -v
    
    # Run frontend tests only  
    pytest tests/frontend/ -v
    
    # Run with coverage
    pytest tests/ --cov=backend --cov-report=html:tests/reports/coverage

Environment Variables:
    TEST_DB_URL: SQLite database URL for testing (default: test_data/test.db)
    TEST_SERVER_URL: Base URL for API tests (default: http://127.0.0.1:8777)
    BROWSER_HEADLESS: Run browser in headless mode (default: true)
"""

__version__ = "1.0.0"
__all__ = []
