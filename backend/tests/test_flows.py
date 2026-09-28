import requests


def test_researcher_flow(api_base, auth):
    r = requests.get(f"{api_base}/api/researcher/flow?limit=3",
                     headers=auth, timeout=20)
    assert r.status_code == 200
    body = r.json()
    assert "chains" in body
    assert isinstance(body["chains"], list)
    for chain in body["chains"]:
        assert "cluster" in chain
        assert "technologies" in chain
        assert "papers" in chain
        assert "gaps" in chain
        assert "opportunities" in chain


def test_researcher_flow_with_topic(api_base, auth):
    r = requests.get(f"{api_base}/api/researcher/flow?topic=machine&limit=2",
                     headers=auth, timeout=20)
    assert r.status_code == 200
    assert "chains" in r.json()


def test_rd_flow(api_base, auth):
    r = requests.get(f"{api_base}/api/rd/flow?limit=5",
                     headers=auth, timeout=20)
    assert r.status_code == 200
    body = r.json()
    for key in ("profile_count", "technologies", "research", "trends", "opportunities"):
        assert key in body, f"missing key: {key}"
    assert isinstance(body["technologies"], list)
    assert isinstance(body["research"], list)
    assert isinstance(body["trends"], list)
    assert isinstance(body["opportunities"], list)


def test_flows_require_auth(api_base):
    for path in ("/api/researcher/flow", "/api/rd/flow"):
        r = requests.get(f"{api_base}{path}", timeout=5)
        assert r.status_code == 401, f"{path} should require auth"
