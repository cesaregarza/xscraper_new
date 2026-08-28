from __future__ import annotations

from splatnet3_scraper.auth.exceptions import NXAPIServiceUnavailableError

from xscraper.job.recovery import (
    UpstreamRecovery,
    UpstreamRecoveryScheduled,
    scrape_with_recovery,
)


def service_unavailable() -> NXAPIServiceUnavailableError:
    return NXAPIServiceUnavailableError(
        message="NXAPI service unavailable: No workers available",
        error_code="service_unavailable",
        error_description="No workers available",
        http_status=503,
    )


def test_upstream_recovery_uses_bounded_backoff() -> None:
    recovery = UpstreamRecovery(
        (60, 300, 600, 1200, 2400, 3600),
        jitter_ratio=0,
    )
    now = 100.0

    delays = []
    for _ in range(7):
        delay = recovery.record_failure(now)
        delays.append(delay)
        assert recovery.ready(now) is False
        assert recovery.seconds_until_retry(now) == delay
        now += delay

    assert delays == [60, 300, 600, 1200, 2400, 3600, 3600]
    assert recovery.ready(now) is True


def test_upstream_recovery_resets_after_success() -> None:
    recovery = UpstreamRecovery((60,), jitter_ratio=0)
    recovery.record_failure(100.0)

    recovery.reset()

    assert recovery.active is False
    assert recovery.ready(100.0) is True
    assert recovery.seconds_until_retry(100.0) == 0


def test_scrape_sends_one_outage_and_one_recovery_message() -> None:
    recovery = UpstreamRecovery((60, 300), jitter_ratio=0)
    outcomes: list[Exception | None] = [
        service_unavailable(),
        service_unavailable(),
        None,
    ]
    messages: list[tuple[str, str]] = []

    def fake_scrape(*_args: object) -> None:
        outcome = outcomes.pop(0)
        if outcome is not None:
            raise outcome

    def capture_message(message: str, *, level: str) -> None:
        messages.append((message, level))

    for now, expected_delay in ((100.0, 60), (160.0, 300)):
        try:
            scrape_with_recovery(
                object(),
                None,
                recovery,
                now=now,
                scrape_fn=fake_scrape,
                capture_message=capture_message,
            )
        except UpstreamRecoveryScheduled as exc:
            assert exc.delay == expected_delay
        else:
            raise AssertionError("Expected recovery to be scheduled")

    recovered = scrape_with_recovery(
        object(),
        None,
        recovery,
        now=460.0,
        scrape_fn=fake_scrape,
        capture_message=capture_message,
    )

    assert recovered is True
    assert recovery.active is False
    assert messages == [
        (
            "XScraper upstream outage detected; automatic recovery started.",
            "warning",
        ),
        (
            "XScraper successfully recovered from the upstream outage.",
            "info",
        ),
    ]


def test_normal_success_does_not_send_sentry_message() -> None:
    recovery = UpstreamRecovery((60,), jitter_ratio=0)
    messages: list[tuple[str, str]] = []

    recovered = scrape_with_recovery(
        object(),
        None,
        recovery,
        now=100.0,
        scrape_fn=lambda *_args: None,
        capture_message=lambda message, level: messages.append(
            (message, level)
        ),
    )

    assert recovered is False
    assert messages == []


def test_unexpected_errors_still_escape() -> None:
    recovery = UpstreamRecovery((60,), jitter_ratio=0)

    def fail(*_args: object) -> None:
        raise ValueError("bad response shape")

    try:
        scrape_with_recovery(
            object(),
            None,
            recovery,
            now=100.0,
            scrape_fn=fail,
        )
    except ValueError as exc:
        assert str(exc) == "bad response shape"
    else:
        raise AssertionError("Expected unexpected error to escape")

    assert recovery.active is False
