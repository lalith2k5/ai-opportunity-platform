from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
    before_sleep_log,
)
import logging
from app.logger import logger

# Create a standard logging adapter for tenacity
_log = logging.getLogger("tenacity")

def api_retry(max_attempts: int = 3, initial_wait: float = 1.0):
    """Decorator: retry API calls with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=initial_wait, min=1, max=15),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        before_sleep=before_sleep_log(_log, logging.WARNING),
        reraise=True,
    )
