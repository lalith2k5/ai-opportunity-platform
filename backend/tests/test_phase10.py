"""Tests for Phase 10 endpoints -- all read-only, use the standard test token."""
import requests


# ---- SRS 30: Organizations ----

def test_organizations_list(api_base, auth):
    r = requests.get(f"{api_base}/api/organizations", headers=auth, timeout=10)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    for row in rows:
        for key in ("id", "name", "canonical_name", "profile_count"):
            assert key in row, f"missing key: {key}"


def test_organizations_requires_auth(api_base):
    r = requests.get(f"{api_base}/api/organizations", timeout=5)
    assert r.status_code == 401


# ---- Pagination / count ----

def test_opportunities_count(api_base, auth):
    r = requests.get(f"{api_base}/api/opportunities/count", headers=auth, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "total" in body and "filtered" in body
    assert isinstance(body["total"], int)


def test_opportunities_pagination(api_base, auth):
    r1 = requests.get(f"{api_base}/api/opportunities?offset=0&limit=3", headers=auth, timeout=10)
    r2 = requests.get(f"{api_base}/api/opportunities?offset=3&limit=3", headers=auth, timeout=10)
    assert r1.status_code == 200 and r2.status_code == 200
    a, b = r1.json(), r2.json()
    assert len(a) <= 3 and len(b) <= 3
    ids_a = {o["id"] for o in a}
    ids_b = {o["id"] for o in b}
    assert not (ids_a & ids_b), "pagination returned overlapping rows"


# ---- SRS 30: Recommendations ----

def test_recommendations_recent(api_base, auth):
    r = requests.get(f"{api_base}/api/recommendations/recent?limit=5", headers=auth, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "count" in body and "recommendations" in body
    assert isinstance(body["recommendations"], list)


def test_opportunity_recommendations_endpoint(api_base, auth):
    opps = requests.get(f"{api_base}/api/opportunities?limit=1", headers=auth, timeout=10).json()
    if not opps:
        import pytest
        pytest.skip("no opportunities")
    oid = opps[0]["id"]
    r = requests.get(f"{api_base}/api/opportunities/{oid}/recommendations", headers=auth, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["opportunity_id"] == oid
    assert "recommendations" in body


# ---- SRS FR-01: Data sources admin ----

def test_admin_data_sources(api_base, auth):
    r = requests.get(f"{api_base}/api/admin/data-sources", headers=auth, timeout=10)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert len(rows) >= 1
    for row in rows:
        for key in ("id", "name", "is_active", "document_count"):
            assert key in row, f"missing key: {key}"


def test_admin_active_source_names(api_base, auth):
    r = requests.get(f"{api_base}/api/admin/data-sources/active-names", headers=auth, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "active" in body
    assert isinstance(body["active"], list)


# ---- SRS 11/13: new fields exposed ----

def test_problem_profiles_have_new_fields(api_base, auth):
    r = requests.get(f"{api_base}/api/problem-profiles?limit=3", headers=auth, timeout=10)
    assert r.status_code == 200
    body = r.json()
    items = body.get("items", [])
    for it in items:
        # These keys must exist (even if empty lists/None)
        assert "affected_stakeholders" in it
        assert "evidence" in it
        assert "confidence" in it


def test_opportunity_detail_has_profile_and_papers_keys(api_base, auth):
    opps = requests.get(f"{api_base}/api/opportunities?limit=1", headers=auth, timeout=10).json()
    if not opps:
        import pytest
        pytest.skip("no opportunities")
    oid = opps[0]["id"]
    r = requests.get(f"{api_base}/api/opportunities/{oid}", headers=auth, timeout=10)
    assert r.status_code == 200
    body = r.json()
    # New keys must be present even if the values are None/[] right now
    assert "problem_profile" in body
    assert "linked_papers" in body
    assert isinstance(body["linked_papers"], list)
    # Opportunity payload must include new scoring factors
    for k in ("technology_suitability_score", "evidence_strength_score", "recency_score"):
        assert k in body["opportunity"], f"missing {k}"


# ---- SRS 21 filters ----

def test_opportunities_domain_filter(api_base, auth):
    # Grab any domain
    filters = requests.get(f"{api_base}/api/opportunities/filters", headers=auth, timeout=10).json()
    domains = filters.get("domains") or []
    if not domains:
        import pytest
        pytest.skip("no domains available yet")
    d = domains[0]
    r = requests.get(f"{api_base}/api/opportunities?domain={d}", headers=auth, timeout=10)
    assert r.status_code == 200
    rows = r.json()
    for row in rows:
        assert row.get("domain") == d
