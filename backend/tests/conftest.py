"""Shared pytest fixtures for backend API tests."""

import os
import pytest
import requests

BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8002")
ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL", "admin@nexus.local")
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "admin123")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def admin_session():
    """Return a requests.Session authenticated as admin."""
    session = requests.Session()
    resp = session.post(
        f"{BASE_URL}/api/nx/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return session


@pytest.fixture
def anon_session():
    """Return an unauthenticated requests.Session."""
    return requests.Session()
