"""
Hit every API endpoint with real auth. Print a status table.
Flags anything that isn't 200 (or expected 4xx for known-bad inputs).
"""
import requests
import json

BASE = "http://127.0.0.1:8000"

def login():
    r = requests.post(
        f"{BASE}/api/auth/login",
        data={"username": "test@example.com", "password": "test1234"},
    )
    if r.status_code != 200:
        print(f"❌ Login failed: {r.status_code} {r.text[:200]}")
        return None
    return r.json()["access_token"]

def check(method, path, token, expect=200, **kw):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{path}", headers=headers, timeout=15, **kw)
        elif method == "POST":
            r = requests.post(f"{BASE}{path}", headers=headers, timeout=30, **kw)
        elif method == "DELETE":
            r = requests.delete(f"{BASE}{path}", headers=headers, timeout=15, **kw)
        elif method == "PATCH":
            r = requests.patch(f"{BASE}{path}", headers=headers, timeout=15, **kw)
        else:
            return "??", "unknown method"

        marker = "✅" if r.status_code == expect else "❌"
        snippet = r.text[:80].replace("\n", " ") if r.status_code != expect else ""
        return marker, f"{r.status_code} {snippet}"
    except Exception as e:
        return "💥", str(e)[:80]

def main():
    token = login()
    if not token:
        return

    # Discover a valid opp id, problem id, gap id, trend name, session id
    r = requests.get(f"{BASE}/api/opportunities", headers={"Authorization": f"Bearer {token}"})
    opps = r.json() if r.status_code == 200 else []
    opp_id = opps[0]["id"] if opps else 1

    r = requests.get(f"{BASE}/api/chat-history", headers={"Authorization": f"Bearer {token}"})
    sessions = r.json() if r.status_code == 200 else []
    session_id = sessions[0]["id"] if sessions else 1

    tests = [
        # method, path, expect
        ("GET",  "/api/health", 200),
        ("GET",  "/api/opportunities", 200),
        ("GET",  f"/api/opportunities/{opp_id}", 200),
        ("GET",  "/api/problems", 200),
        ("GET",  "/api/research-gaps", 200),
        ("GET",  "/api/trends", 200),
        ("GET",  "/api/search-history", 200),
        ("GET",  "/api/chat-history", 200),
        ("GET",  f"/api/chat-sessions/{session_id}", 200),
        ("GET",  "/api/processed-documents", 200),
        ("GET",  "/api/notifications", 200),
        ("GET",  "/api/notifications/unread-count", 200),
        ("GET",  "/api/kg/stats", 200),
        ("GET",  "/api/kg/nodes?limit=5", 200),
        ("GET",  "/api/kg/edges?limit=5", 200),
        ("GET",  "/api/kg/entity-types", 200),
        ("GET",  "/api/kg/search?q=ai", 200),
        ("GET",  "/api/scheduler/status", 200),
        ("GET",  "/api/reports/narrative", 200),
        ("GET",  "/api/export/opportunities.json", 200),
        ("GET",  "/api/export/research-gaps.json", 200),
        ("GET",  "/api/export/full.json", 200),
        ("GET",  "/api/auth/me", 200),
        ("GET",  "/api/admin/stats", 200),
        ("GET",  "/api/admin/users", 200),
        ("GET",  "/api/admin/agent-logs?limit=5", 200),
        ("GET",  "/api/admin/scheduler", 200),
        ("GET",  "/api/admin/settings", 200),
        ("GET",  "/api/admin/sync/status", 200),
        ("GET",  "/api/admin/llm/status", 200),
    ]

    print(f"\n{'Method':<7}{'Endpoint':<52}{'Result'}")
    print("-" * 100)

    failures = []
    for method, path, expect in tests:
        marker, result = check(method, path, token, expect=expect)
        print(f"{method:<7}{path:<52}{marker} {result}")
        if marker != "✅":
            failures.append((method, path, result))

    # POST endpoints tested with safe payloads
    print()
    post_tests = [
        ("POST", "/api/search", {"json": {"query": "machine learning"}}, 200),
    ]
    for method, path, kwargs, expect in post_tests:
        marker, result = check(method, path, token, expect=expect, **kwargs)
        print(f"{method:<7}{path:<52}{marker} {result}")
        if marker != "✅":
            failures.append((method, path, result))

    print()
    if failures:
        print(f"\n❌ {len(failures)} endpoint(s) failed:\n")
        for m, p, r in failures:
            print(f"  {m} {p}")
            print(f"    {r}\n")
    else:
        print("✅ All endpoints healthy")

if __name__ == "__main__":
    main()
