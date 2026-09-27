"""Simple in-memory sliding-window rate limiter for sensitive endpoints."""
import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import Request, HTTPException

_lock = Lock()
_hits: dict = defaultdict(deque)


def rate_limit(max_requests: int = 5, window_seconds: int = 60):
    """Returns a FastAPI dependency that limits by client IP."""
    def _check(request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        with _lock:
            q = _hits[ip]
            while q and (now - q[0]) > window_seconds:
                q.popleft()
            if len(q) >= max_requests:
                retry_in = int(window_seconds - (now - q[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many attempts. Try again in {retry_in}s.",
                    headers={"Retry-After": str(retry_in)},
                )
            q.append(now)
    return _check
