"""Simple load test: measure endpoint latency under concurrent requests."""
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median

BASE = "http://localhost:8000"

def get_token():
    r = requests.post(f"{BASE}/api/auth/login", data={
        "username": "test@example.com",
        "password": "test1234",
    })
    return r.json()["access_token"]

def timed_get(url, headers):
    start = time.time()
    r = requests.get(url, headers=headers)
    return (time.time() - start) * 1000, r.status_code

def run_test(endpoint, n_requests=50, concurrency=10, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{BASE}{endpoint}"
    print(f"\n=== Testing {endpoint} ({n_requests} requests, concurrency={concurrency}) ===")

    # Warm up
    for _ in range(3):
        requests.get(url, headers=headers)

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        results = list(ex.map(lambda _: timed_get(url, headers), range(n_requests)))

    latencies = [r[0] for r in results]
    statuses = [r[1] for r in results]
    ok = sum(1 for s in statuses if 200 <= s < 300)

    print(f"  Success rate: {ok}/{n_requests} ({100*ok/n_requests:.1f}%)")
    print(f"  Min latency:  {min(latencies):.1f} ms")
    print(f"  Median:       {median(latencies):.1f} ms")
    print(f"  Mean:         {mean(latencies):.1f} ms")
    print(f"  Max latency:  {max(latencies):.1f} ms")
    print(f"  P95:          {sorted(latencies)[int(0.95 * len(latencies))]:.1f} ms")

def main():
    token = get_token()
    print("Token acquired")
    run_test("/api/health", n_requests=50, concurrency=10)
    run_test("/api/opportunities", n_requests=50, concurrency=10, token=token)
    run_test("/api/problems", n_requests=50, concurrency=10, token=token)
    run_test("/api/trends", n_requests=50, concurrency=10, token=token)
    run_test("/api/notifications", n_requests=50, concurrency=10)

if __name__ == "__main__":
    main()
