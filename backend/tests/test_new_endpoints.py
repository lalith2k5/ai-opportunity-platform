
"""Tests for Screen 2-5 backend endpoints (Phases N.2, N.3, N.7).

Read-only. Skips cleanly when the DB has no data or the backend is down.
"""
import urllib.parse

import pytest
import requests


def test_technologies_list(api_base, auth):
    r = requests.get(f"{api_base}/api/technologies?limit=5", headers=auth, timeout=20)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    for row in rows:
        for key in ("name", "composite_score", "source_count",
                    "related_problem_count", "related_paper_count"):
            assert key in row, "missing key: " + key


def test_technologies_detail(api_base, auth):
    rows = requests.get(f"{api_base}/api/technologies?limit=1",
                        headers=auth, timeout=20).json()
    if not rows:
        pytest.skip("no technologies in DB")
    name = rows[0]["name"]
    enc = urllib.parse.quote(name, safe="")
    r = requests.get(f"{api_base}/api/technologies/{enc}", headers=auth, timeout=20)
    assert r.status_code == 200
    body = r.json()
    for key in ("technology", "related_problems", "related_papers",
                "github_repositories", "news_articles", "reddit_discussions",
                "trend", "potential_gaps", "opportunities", "sources"):
        assert key in body, "missing key: " + key
    assert body["technology"]["name"].lower() == name.lower()


def test_technologies_detail_404(api_base, auth):
    r = requests.get(f"{api_base}/api/technologies/zzz-nonexistent-xyz",
                     headers=auth, timeout=15)
    assert r.status_code == 404


def test_research_papers_list(api_base, auth):
    r = requests.get(f"{api_base}/api/research-papers?limit=5",
                     headers=auth, timeout=20)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    for row in rows:
        for key in ("arxiv_id", "title", "relevance_score"):
            assert key in row, "missing key: " + key


def test_research_papers_detail(api_base, auth):
    rows = requests.get(f"{api_base}/api/research-papers?limit=1",
                        headers=auth, timeout=20).json()
    if not rows:
        pytest.skip("no research papers in DB")
    aid = rows[0].get("arxiv_id")
    if not aid:
        pytest.skip("no arxiv id in first paper")
    enc = urllib.parse.quote(aid, safe="")
    r = requests.get(f"{api_base}/api/research-papers/{enc}",
                     headers=auth, timeout=20)
    assert r.status_code == 200
    body = r.json()
    for key in ("paper", "research_objective", "methodology", "key_findings",
                "limitations", "related_papers", "related_technologies",
                "potential_gaps", "source"):
        assert key in body, "missing key: " + key


def test_research_papers_detail_404(api_base, auth):
    r = requests.get(f"{api_base}/api/research-papers/9999.99999",
                     headers=auth, timeout=15)
    assert r.status_code == 404


def test_ideas_list(api_base, auth):
    r = requests.get(f"{api_base}/api/ideas?limit=5", headers=auth, timeout=20)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    for row in rows:
        for key in ("id", "title", "composite_score", "source_count",
                    "demand_score", "opportunity_count"):
            assert key in row, "missing key: " + key
    if len(rows) >= 2:
        scores = [r["composite_score"] for r in rows]
        assert scores == sorted(scores, reverse=True), "not sorted desc by composite_score"


def test_ideas_detail(api_base, auth):
    rows = requests.get(f"{api_base}/api/ideas?limit=1",
                        headers=auth, timeout=20).json()
    if not rows:
        pytest.skip("no ideas in DB")
    idea_id = rows[0]["id"]
    r = requests.get(f"{api_base}/api/ideas/{idea_id}", headers=auth, timeout=20)
    assert r.status_code == 200
    body = r.json()
    for key in ("idea", "related_technologies", "related_news",
                "reddit_discussions", "github_repositories", "research_papers",
                "evidence", "potential_gaps", "opportunities",
                "suggested_directions"):
        assert key in body, "missing key: " + key
    assert body["idea"]["id"] == idea_id


def test_ideas_detail_404(api_base, auth):
    r = requests.get(f"{api_base}/api/ideas/999999999", headers=auth, timeout=15)
    assert r.status_code == 404


def test_rd_problem_detail(api_base, auth):
    rows = requests.get(f"{api_base}/api/problem-profiles?limit=1",
                        headers=auth, timeout=20).json()
    items = rows.get("items", []) if isinstance(rows, dict) else []
    if not items:
        pytest.skip("no problem profiles in DB")
    pid = items[0]["id"]
    r = requests.get(f"{api_base}/api/rd/problems/{pid}",
                     headers=auth, timeout=20)
    assert r.status_code == 200
    body = r.json()
    for key in ("problem", "organization", "related_technologies",
                "technology_landscape", "research_landscape", "emerging_trends",
                "evidence_aggregation", "knowledge_graph", "potential_gaps",
                "innovation_opportunities", "opportunity_scoring",
                "recommended_next_steps"):
        assert key in body, "missing key: " + key


def test_rd_problem_detail_404(api_base, auth):
    r = requests.get(f"{api_base}/api/rd/problems/999999999",
                     headers=auth, timeout=15)
    assert r.status_code == 404


def test_new_endpoints_require_auth(api_base):
    for path in ("/api/technologies", "/api/research-papers", "/api/ideas"):
        r = requests.get(f"{api_base}{path}", timeout=10)
        assert r.status_code == 401, path + " should require auth"
