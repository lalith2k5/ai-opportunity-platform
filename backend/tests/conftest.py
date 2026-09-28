"""Shared pytest fixtures.

Tests run against the live backend on localhost:8000, using the seeded
test account (test@example.com / test1234). No LLM calls are made — the
suite is intentionally cheap and read-heavy so it can run any time.
"""
import os
import pytest
import requests


API_BASE = os.environ.get("AOD_API_BASE", "http://localhost:8000")
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test1234"


@pytest.fixture(scope="session")
def api_base():
    return API_BASE


@pytest.fixture(scope="session")
def token(api_base):
    """Login as the seeded test admin. Skips the whole session if the
    backend is not reachable, rather than reporting 30 failures."""
    try:
        r = requests.post(
            f"{api_base}/api/auth/login",
            data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        pytest.skip("backend not reachable — run `op-start` first")
    if r.status_code != 200:
        pytest.skip(f"login failed ({r.status_code}) — is test@example.com seeded?")
    return r.json()["access_token"]


@pytest.fixture
def auth(token):
    return {"Authorization": f"Bearer {token}"}
