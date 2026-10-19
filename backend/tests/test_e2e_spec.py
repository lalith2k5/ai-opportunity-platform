#!/usr/bin/env python3
"""End-to-end spec compliance test. Usage: python3 tests/test_e2e_spec.py"""
import json
import os
import sys
from datetime import datetime

import requests

BASE = os.environ.get("AOD_API_BASE", "http://localhost:8000")
EMAIL = "test@example.com"
PWD = "test1234"

PASS = 0
FAIL = 0
ERRORS = []


def ok(label, extra=""):
    global PASS
    PASS += 1
    print(f"  [PASS] {label}{(' — ' + extra) if extra else ''}")


def ko(label, extra=""):
    global FAIL
    FAIL += 1
    ERRORS.append((label, extra))
    print(f"  [FAIL] {label}{(' — ' + extra) if extra else ''}")


def get(path, token=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.get(f"{BASE}{path}", headers=h, timeout=30)


def post(path, token=None, body=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.post(f"{BASE}{path}", headers=h, json=body, timeout=180)


def check(name, resp, expect=200):
    if resp.status_code != expect:
        ko(name, f"HTTP {resp.status_code}")
        return None
    try:
        return resp.json()
    except Exception:
        return {}


def main():
    print(f"=== E2E spec test — {datetime.now().isoformat()} ===\n")

    print("[1] health + auth")
    data = check("health", get("/api/health"))
    if data and data.get("status") == "healthy":
        ok("health.status=healthy")
    else:
        ko("health.status", str(data))

    r = requests.post(
        f"{BASE}/api/auth/login",
        data={"username": EMAIL, "password": PWD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    auth = check("login", r)
    token = auth.get("access_token") if auth else None
    if token:
        ok("login -> token")
    else:
        ko("login", "no token")
        return summarize()

    print("\n[2] opportunities + spec fields")
    opps = check("GET /api/opportunities", get("/api/opportunities?limit=10", token))
    if opps and len(opps) > 0:
        ok("opportunities list", f"{len(opps)} rows")
        first = opps[0]
        spec_keys = ["opportunity_score_spec", "confidence_spec", "weights_version", "confidence_version"]
        missing = [k for k in spec_keys if k not in first]
        if missing:
            ko("opportunity spec fields", f"missing {missing}")
        else:
            ok("opportunity spec fields present")
        scores = [o.get("opportunity_score_spec") for o in opps if o.get("opportunity_score_spec") is not None]
        if len(set(scores)) >= 3:
            ok("scores vary", f"{len(set(scores))} distinct")
        else:
            ko("scores vary", f"only {len(set(scores))} distinct")
    else:
        ko("opportunities list", "empty")

    print("\n[3] opportunity detail + gap caveat")
    if opps:
        oid = opps[0]["id"]
        detail = check(f"GET /api/opportunities/{oid}", get(f"/api/opportunities/{oid}", token))
        if detail:
            opp = detail.get("opportunity", {})
            if "opportunity_score_spec" in opp:
                ok("detail has spec score")
            else:
                ko("detail spec score", "missing")
            gap = detail.get("research_gap")
            if gap:
                if "kind" in gap and "gap_status" in gap:
                    ok("gap kind + gap_status", f"kind={gap['kind']} status={gap['gap_status']}")
                else:
                    ko("gap spec fields", f"keys={list(gap.keys())[:8]}")

    print("\n[4] research gaps")
    gaps = check("GET /api/research-gaps", get("/api/research-gaps", token))
    if gaps and len(gaps) > 0:
        ok("gaps list", f"{len(gaps)} rows")
        first = gaps[0]
        if "kind" in first and "gap_status" in first and "gap_confidence" in first:
            ok("gap spec fields present")
        else:
            ko("gap spec fields", f"keys={list(first.keys())}")
    else:
        ko("gaps list", "empty")

    print("\n[5] review queue + decision workflow")
    q = check("GET /api/admin/review/queue", get("/api/admin/review/queue?limit=5", token))
    if q is not None:
        ok("review queue endpoint", f"count={q.get('count')}")
        items = q.get("items") or []
        if items:
            gid = items[0]["id"]
            bad = post(f"/api/admin/review/gaps/{gid}/decide", token,
                       {"decision": "UNDER_REVIEW", "rationale": "e2e invalid"})
            if bad.status_code == 400:
                ok("invalid decision rejected (400)")
            else:
                ko("invalid decision", f"HTTP {bad.status_code}")
            good = post(f"/api/admin/review/gaps/{gid}/decide", token,
                        {"decision": "VALIDATED", "rationale": "e2e smoke"})
            if good.status_code == 200:
                ok("valid decision accepted")
                revert = post(f"/api/admin/review/gaps/{gid}/decide", token,
                              {"decision": "REVISED", "rationale": "e2e revert"})
                if revert.status_code == 200:
                    ok("revert accepted")
            else:
                ko("valid decision", f"HTTP {good.status_code}")

    print("\n[6] evaluation metrics")
    m = check("GET /api/admin/evaluation/metrics", get("/api/admin/evaluation/metrics", token))
    if m:
        for key in ("opportunities", "research_gaps", "provenance", "validation",
                    "conflicts", "change_events_total", "reproducibility"):
            if key in m:
                ok(f"metrics.{key}")
            else:
                ko(f"metrics.{key}", "missing")
        prov = m.get("provenance", {}).get("completeness_pct")
        if prov == 100.0:
            ok("provenance 100%")
        else:
            ko("provenance completeness", f"{prov}%")

    print("\n[7] conflict sweep")
    r = post("/api/admin/evaluation/conflict-sweep", token)
    if r.status_code == 200:
        d = r.json()
        ok("conflict-sweep", f"scanned={d.get('scanned')} raised={d.get('raised')}")
    else:
        ko("conflict-sweep", f"HTTP {r.status_code}")

    print("\n[8] scheduler + pipeline status")
    s = check("GET /api/admin/scheduler", get("/api/admin/scheduler", token))
    if s:
        job_ids = [j.get("id") for j in s.get("jobs", [])]
        if "spec_sync_hooks" in job_ids:
            ok("spec_sync_hooks job registered")
        else:
            ko("spec_sync_hooks", f"jobs={job_ids}")

    pstat = check("GET /api/admin/pipeline/status", get("/api/admin/pipeline/status", token))
    if pstat is not None:
        ok("pipeline status", f"running={pstat.get('running')}")

    print("\n[9] auth required on protected endpoints")
    for path in ("/api/opportunities", "/api/ideas", "/api/technologies",
                 "/api/research-papers", "/api/admin/evaluation/metrics"):
        r = get(path)
        if r.status_code == 401:
            ok(f"{path} requires auth")
        else:
            ko(f"{path} auth", f"HTTP {r.status_code} expected 401")

    return summarize()


def summarize():
    print("\n" + "=" * 60)
    print(f"RESULT: {PASS} PASS | {FAIL} FAIL")
    print("=" * 60)
    if ERRORS:
        print("\nFailures:")
        for label, extra in ERRORS:
            print(f"  - {label}: {extra}")
    report = {
        "generated_at": datetime.now().isoformat(),
        "pass": PASS,
        "fail": FAIL,
        "errors": [{"label": l, "extra": e} for l, e in ERRORS],
    }
    with open("/tmp/e2e_report.txt", "w") as f:
        f.write(json.dumps(report, indent=2))
    print(f"\nReport: /tmp/e2e_report.txt")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("backend not reachable -- op-start first")
        sys.exit(2)
