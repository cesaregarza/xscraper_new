from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import requests
import sentry_sdk
from psycopg2.extensions import connection as Connection
from splatnet3_scraper.auth.exceptions import (
    NXAPIRateLimitError,
    NXAPIServiceUnavailableError,
    RateLimitException,
)
from splatnet3_scraper.query import QueryHandler

from xscraper.scraper.main import scrape

TRANSIENT_UPSTREAM_EXCEPTIONS = (
    NXAPIRateLimitError,
    NXAPIServiceUnavailableError,
    RateLimitException,
    requests.ConnectionError,
    requests.Timeout,
)


@dataclass
class UpstreamRecovery:
    """Track bounded retry state for transient upstream failures."""

    backoff_seconds: Sequence[float]
    jitter_ratio: float = 0.2
    failure_count: int = 0
    next_attempt_at: float = 0.0

    @property
    def active(self) -> bool:
        """Return whether an upstream outage is currently being recovered.

        Returns:
            bool: Whether recovery is active.
        """
        return self.failure_count > 0

    def ready(self, now: float) -> bool:
        """Return whether the next recovery attempt may run.

        Args:
            now (float): Current monotonic time.

        Returns:
            bool: Whether the recovery delay has elapsed.
        """
        return not self.active or now >= self.next_attempt_at

    def seconds_until_retry(self, now: float) -> float:
        """Return the remaining recovery delay.

        Args:
            now (float): Current monotonic time.

        Returns:
            float: Seconds until another attempt may run.
        """
        if not self.active:
            return 0.0
        return max(0.0, self.next_attempt_at - now)

    def record_failure(
        self,
        now: float,
        *,
        jitter_fn: Callable[[float, float], float] = random.uniform,
    ) -> float:
        """Advance the backoff and return the selected retry delay.

        Args:
            now (float): Current monotonic time.
            jitter_fn (Callable[[float, float], float]): Function used to
                select a jitter multiplier.

        Returns:
            float: Selected retry delay in seconds.

        Raises:
            ValueError: If the recovery configuration is invalid.
        """
        if not self.backoff_seconds:
            raise ValueError("At least one recovery backoff is required")
        if not 0 <= self.jitter_ratio < 1:
            raise ValueError("jitter_ratio must be at least 0 and less than 1")

        index = min(self.failure_count, len(self.backoff_seconds) - 1)
        base_delay = float(self.backoff_seconds[index])
        if base_delay <= 0:
            raise ValueError("Recovery backoffs must be positive")

        multiplier = jitter_fn(
            1.0 - self.jitter_ratio,
            1.0 + self.jitter_ratio,
        )
        delay = base_delay * multiplier
        self.failure_count += 1
        self.next_attempt_at = now + delay
        return delay

    def reset(self) -> None:
        """Clear the outage after a successful scrape."""
        self.failure_count = 0
        self.next_attempt_at = 0.0


def scrape_with_recovery(
    scraper: QueryHandler,
    conn: Connection | None,
    recovery: UpstreamRecovery,
    *,
    now: float,
    scrape_fn: Callable[[QueryHandler, Connection | None], None] = scrape,
    capture_message: Callable[..., object] = sentry_sdk.capture_message,
) -> bool:
    """Run one scrape and classify transient upstream errors.

    Args:
        scraper (QueryHandler): Client used to query SplatNet.
        conn (Connection | None): Optional existing database connection.
        recovery (UpstreamRecovery): Mutable outage recovery state.
        now (float): Current monotonic time.
        scrape_fn (Callable[[QueryHandler, Connection | None], None]): Scrape
            implementation to run.
        capture_message (Callable[..., object]): Sentry-compatible message
            capture function.

    Returns:
        bool: Whether this successful scrape recovered from an outage.

    Raises:
        UpstreamRecoveryScheduled: If a transient failure schedules a retry.
    """
    was_recovering = recovery.active
    try:
        scrape_fn(scraper, conn)
    except TRANSIENT_UPSTREAM_EXCEPTIONS as exc:
        delay = recovery.record_failure(now)
        if not was_recovering:
            capture_message(
                "XScraper upstream outage detected; automatic recovery "
                "started.",
                level="warning",
            )
        raise UpstreamRecoveryScheduled(delay, exc) from exc

    if was_recovering:
        capture_message(
            "XScraper successfully recovered from the upstream outage.",
            level="info",
        )
    recovery.reset()
    return was_recovering


class UpstreamRecoveryScheduled(Exception):
    """Signal that a transient failure has scheduled a bounded retry."""

    def __init__(self, delay: float, cause: Exception) -> None:
        super().__init__(str(cause))
        self.delay = delay
        self.cause = cause
