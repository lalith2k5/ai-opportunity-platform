"""Retry helpers for external API calls.

Retries on:
  - Network-level errors (ConnectionError, TimeoutError, OSError, RequestException)
  - HTTP 5xx responses (server-side failures)
  - HTTP 429 responses (rate limit)

Uses exponential backoff via tenacity.
"""
import logging

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

_log = logging.getLogger("tenacity")


def _is_retryable_response(result) -> bool:
    """Return True if `result` is a retryable HTTP response.

    Only `requests.Response` objects are inspected. Anything else
    (e.g. feedparser FeedParserDict) is treated as non-retryable.
    """
    if result is None:
        return False
    status = getattr(result, "status_code", None)
    if status is None:
        return False
    return status >= 500 or status == 429


def api_retry(max_attempts: int = 3, initial_wait: float = 1.0):
    """Decorator: retry API calls with exponential backoff.

    Covers network errors AND retryable HTTP responses (5xx, 429).
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=initial_wait, min=1, max=15),
        retry=(
            retry_if_exception_type(
                (ConnectionError, TimeoutError, OSError, requests.exceptions.RequestException)
            )
            | retry_if_result(_is_retryable_response)
        ),
        before_sleep=before_sleep_log(_log, logging.WARNING),
        reraise=True,
    )
