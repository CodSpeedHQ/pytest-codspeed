from __future__ import annotations

import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING

import pytest

from pytest_codspeed.telemetry import parse_filter

if TYPE_CHECKING:
    from collections.abc import Iterator

TELEMETRY_ARGS = ("--codspeed", "--codspeed-mode=telemetry")

TELEMETRY_BENCHMARK = """
import logging

import pytest
from opentelemetry import trace

logger = logging.getLogger("bench")


@pytest.mark.benchmark
def test_emits_telemetry():
    with trace.get_tracer("bench").start_as_current_span("work"):
        logger.info("inside the span")
        logger.debug("below the default level")


@pytest.mark.benchmark
def test_emits_another_trace():
    with trace.get_tracer("bench").start_as_current_span("other"):
        pass
"""


class _Collector:
    """An OTLP/HTTP endpoint keeping the requests it receives."""

    def __init__(self) -> None:
        self.requests: dict[str, list[bytes]] = {"/v1/traces": [], "/v1/logs": []}
        collector = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = self.rfile.read(int(self.headers["Content-Length"]))
                collector.requests.setdefault(self.path, []).append(body)
                self.send_response(200)
                self.send_header("Content-Type", "application/x-protobuf")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, format, *args) -> None:
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def endpoint(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def spans(self):
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
            ExportTraceServiceRequest,
        )

        for body in self.requests["/v1/traces"]:
            request = ExportTraceServiceRequest.FromString(body)
            for resource_spans in request.resource_spans:
                for scope_spans in resource_spans.scope_spans:
                    for span in scope_spans.spans:
                        yield resource_spans.resource, span

    def logs(self):
        from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import (
            ExportLogsServiceRequest,
        )

        for body in self.requests["/v1/logs"]:
            request = ExportLogsServiceRequest.FromString(body)
            for resource_logs in request.resource_logs:
                for scope_logs in resource_logs.scope_logs:
                    for record in scope_logs.log_records:
                        yield resource_logs.resource, record


@pytest.fixture
def collector() -> Iterator[_Collector]:
    collector = _Collector()
    collector.thread.start()
    yield collector
    collector.server.shutdown()


def _attributes(item) -> dict:
    out = {}
    for attribute in item.attributes:
        value = attribute.value
        out[attribute.key] = getattr(value, value.WhichOneof("value"))
    return out


def test_exports_spans_and_logs_with_monotonic_times(
    pytester: pytest.Pytester, codspeed_env, collector: _Collector, monkeypatch
) -> None:
    pytest.importorskip("opentelemetry.sdk")
    pytester.makepyfile(TELEMETRY_BENCHMARK)
    monkeypatch.setenv("CODSPEED_OTEL_ENDPOINT", collector.endpoint)
    with codspeed_env():
        result = pytester.runpytest_subprocess(*TELEMETRY_ARGS)
    result.stdout.fnmatch_lines(["*mode: telemetry*", "*2 benchmarked*", "*2 passed*"])

    all_spans = [span for _, span in collector.spans()]
    assert sorted(span.name for span in all_spans) == ["other", "work"]
    # The plugin reseeds the global random generator before each benchmark.
    assert all_spans[0].trace_id != all_spans[1].trace_id
    spans = [span for span in all_spans if span.name == "work"]
    span_attributes = _attributes(spans[0])
    start = span_attributes["codspeed.monotonic_start_ns"]
    end = span_attributes["codspeed.monotonic_end_ns"]
    assert 0 < start <= end

    logs = list(collector.logs())
    bodies = [record.body.string_value for _, record in logs]
    assert bodies == ["inside the span"]
    resource, record = logs[0]
    assert start <= _attributes(record)["codspeed.monotonic_time_ns"] <= end
    assert record.span_id == spans[0].span_id
    assert _attributes(resource)["service.name"] == pytester.path.name


def test_exports_nothing_without_endpoint(
    pytester: pytest.Pytester, codspeed_env, collector: _Collector, monkeypatch
) -> None:
    pytest.importorskip("opentelemetry.sdk")
    pytester.makepyfile(TELEMETRY_BENCHMARK)
    monkeypatch.delenv("CODSPEED_OTEL_ENDPOINT", raising=False)
    with codspeed_env():
        result = pytester.runpytest_subprocess(*TELEMETRY_ARGS)
    result.stdout.fnmatch_lines(["*2 passed*"])
    assert collector.requests == {"/v1/traces": [], "/v1/logs": []}


def test_parse_filter() -> None:
    assert parse_filter("info") == (logging.INFO, {})
    assert parse_filter("warn,my_package=debug, other = off") == (
        logging.WARNING,
        {"my_package": logging.DEBUG, "other": logging.CRITICAL + 1},
    )


def test_parse_filter_ignores_unknown_levels() -> None:
    with pytest.warns(RuntimeWarning, match="unknown level"):
        assert parse_filter("loud,my_package=debug") == (
            logging.INFO,
            {"my_package": logging.DEBUG},
        )
