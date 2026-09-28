def test_health_ok(api_base):
    import requests
    r = requests.get(f"{api_base}/api/health", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "healthy"
    assert "vectors_stored" in body
    assert isinstance(body["vectors_stored"], int)


def test_root_endpoint(api_base):
    import requests
    r = requests.get(f"{api_base}/", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert "docs" in body
    assert body.get("health") == "/api/health"
