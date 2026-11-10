"""Benchmarks that emit telemetry in different ways: OpenTelemetry spans with
`logging` records in them, `logging` records only, or nothing at all.

In telemetry mode, the plugin exports the spans and the records. In the other
modes, nothing is exported, and these benchmarks show the cost of the calls.
"""

from __future__ import annotations

import logging

import pytest

trace = pytest.importorskip("opentelemetry.trace")

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


def parse(text: str) -> list[int]:
    with tracer.start_as_current_span("parse") as span:
        span.set_attribute("input_len", len(text))
        values = [int(field) for field in text.split(",") if field.isdigit()]
        logger.info("parsed %d values", len(values))
        return values


def total(values: list[int]) -> int:
    with tracer.start_as_current_span("total"):
        logger.debug("the default filter drops this record")
        return sum(values)


@pytest.mark.benchmark
def test_nested_spans_with_logs():
    """Nested spans, with `logging` records in them."""
    with tracer.start_as_current_span("parse_and_total"):
        values = parse("1,2,x,3")
        if len(values) < 4:
            logger.warning("skipped %d invalid fields", 4 - len(values))
        assert total(values) == 6


@pytest.mark.benchmark
def test_log_without_span():
    """A `logging` record outside of any span."""
    values = [1, 2, 3]
    logger.info("summing %d values without a span", len(values))
    assert sum(values) == 6


@pytest.mark.benchmark
def test_no_telemetry():
    """No telemetry at all."""
    assert sum([1, 2, 3]) == 6
