import requests


def test_list_opportunities(api_base, auth):
    r = requests.get(f"{api_base}/api/opportunities", headers=auth, timeout=15)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    if rows:
        top = rows[0]
        for key in ("id", "title", "opportunity_score", "confidence_score",
                    "demand_score", "research_gap_score", "trend_score"):
            assert key in top, f"missing key: {key}"
        # Should be sorted by score desc
        scores = [x["opportunity_score"] for x in rows if "opportunity_score" in x]
        assert scores == sorted(scores, reverse=True)


def test_opportunity_detail(api_base, auth):
    rows = requests.get(f"{api_base}/api/opportunities", headers=auth, timeout=15).json()
    if not rows:
        import pytest
        pytest.skip("no opportunities in DB — run a pipeline first")
    opp_id = rows[0]["id"]
    r = requests.get(f"{api_base}/api/opportunities/{opp_id}", headers=auth, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "opportunity" in body
    assert body["opportunity"]["id"] == opp_id
    for key in ("domain", "industry", "related_technologies",
                "existing_research", "suggested_research_direction",
                "suggested_project_direction", "emerging_trend",
                "evidence_sources"):
        assert key in body["opportunity"], f"missing enrichment key: {key}"


def test_opportunity_detail_404(api_base, auth):
    r = requests.get(f"{api_base}/api/opportunities/999999999", headers=auth, timeout=10)
    assert r.status_code == 404


def test_opportunity_history_endpoint(api_base, auth):
    rows = requests.get(f"{api_base}/api/opportunities", headers=auth, timeout=15).json()
    if not rows:
        import pytest
        pytest.skip("no opportunities in DB")
    opp_id = rows[0]["id"]
    r = requests.get(f"{api_base}/api/opportunities/{opp_id}/history?days=30",
                     headers=auth, timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["opportunity_id"] == opp_id
    assert "history" in body and isinstance(body["history"], list)
    for row in body["history"]:
        assert "score" in row
        assert "rank" in row
        assert "recorded_at" in row
