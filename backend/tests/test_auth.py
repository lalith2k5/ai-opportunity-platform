import requests


def test_login_returns_token(api_base):
    r = requests.post(
        f"{api_base}/api/auth/login",
        data={"username": "test@example.com", "password": "test1234"},
        timeout=10,
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "test@example.com"
    assert body["user"]["role"] in ("admin", "student", "researcher", "entrepreneur", "investor")


def test_login_rejects_bad_password(api_base):
    r = requests.post(
        f"{api_base}/api/auth/login",
        data={"username": "test@example.com", "password": "wrong-password"},
        timeout=10,
    )
    assert r.status_code == 401


def test_me_requires_auth(api_base):
    r = requests.get(f"{api_base}/api/auth/me", timeout=5)
    assert r.status_code == 401


def test_me_with_token(api_base, auth):
    r = requests.get(f"{api_base}/api/auth/me", headers=auth, timeout=5)
    assert r.status_code == 200
    assert r.json()["email"] == "test@example.com"
