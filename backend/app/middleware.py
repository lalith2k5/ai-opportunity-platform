import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.logger import logger
from app.database import SessionLocal
from app import models


class ActivityLogMiddleware(BaseHTTPMiddleware):
    """Log every request to DB + logfile."""

    SKIP_PATHS = {"/docs", "/openapi.json", "/redoc", "/favicon.ico", "/api/health"}

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        path = request.url.path

        if any(path.startswith(p) for p in self.SKIP_PATHS):
            return await call_next(request)

        user_email = None
        try:
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                from app.auth.security import decode_token
                payload = decode_token(auth[7:])
                if payload:
                    user_email = payload.get("sub")
        except Exception:
            pass

        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)

        try:
            db = SessionLocal()
            user_id = None
            if user_email:
                u = db.query(models.User).filter(models.User.email == user_email).first()
                if u:
                    user_id = u.id

            db.add(models.AgentLog(
                agent_name="HTTP",
                action=f"{request.method} {path}",
                status="success" if response.status_code < 400 else "error",
                details={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "user_email": user_email,
                    "client": request.client.host if request.client else None,
                },
            ))
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Activity log error: {e}")

        logger.info(
            f"{request.method} {path} -> {response.status_code} "
            f"({duration_ms}ms) user={user_email or 'anon'}"
        )
        return response
