"""Sends the spans and logs of the benchmarked code to the CodSpeed runner
over OTLP/HTTP.

This module does nothing unless `CODSPEED_OTEL_ENDPOINT` is set. The runner
sets it in telemetry mode. The OpenTelemetry packages come with the
`telemetry` extra of pytest-codspeed.

Each span and log record also gets its time from the clock of the benchmark
markers, so that the runner can find the benchmark it belongs to:
- spans get `codspeed.monotonic_start_ns` and `codspeed.monotonic_end_ns`
- log records get `codspeed.monotonic_time_ns`
"""

from __future__ import annotations

import logging
import os
import random
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable

    from opentelemetry.context import Context
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor
    from opentelemetry.sdk.trace.export import SpanExporter
    from opentelemetry.sdk.trace.id_generator import RandomIdGenerator

ENDPOINT_ENV = "CODSPEED_OTEL_ENDPOINT"
FILTER_ENV = "CODSPEED_TELEMETRY_FILTER"
DEFAULT_FILTER = "info"

MONOTONIC_START_ATTRIBUTE = "codspeed.monotonic_start_ns"
MONOTONIC_END_ATTRIBUTE = "codspeed.monotonic_end_ns"
MONOTONIC_TIME_ATTRIBUTE = "codspeed.monotonic_time_ns"

# The exporter logs through these loggers. The plugin never exports their
# records.
EXPORTER_LOGGERS = ("opentelemetry", "urllib3", "requests")

LEVELS = {
    "off": logging.CRITICAL + 1,
    "error": logging.ERROR,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "trace": logging.NOTSET + 1,
}


def _clock() -> Callable[[], int] | None:
    """Returns the clock that the benchmark markers use, or `None` if the native
    library doesn't load."""
    try:
        from .instruments.hooks import dist_instrument_hooks  # type: ignore
    except ImportError:
        return None
    return dist_instrument_hooks.instrument_hooks_current_timestamp


def parse_filter(spec: str) -> tuple[int, dict[str, int]]:
    """Parses directives such as `info,my_package=debug`.

    Returns the default level and the level of each named logger. The level of a
    logger also applies to its child loggers."""
    default = logging.INFO
    levels: dict[str, int] = {}
    for directive in spec.split(","):
        directive = directive.strip()
        if not directive:
            continue
        name, _, level = directive.rpartition("=")
        value = LEVELS.get(level.strip().lower())
        if value is None:
            warnings.warn(
                f"Ignoring the {FILTER_ENV} directive {directive!r}: unknown level",
                RuntimeWarning,
                stacklevel=2,
            )
            continue
        if name:
            levels[name.strip()] = value
        else:
            default = value
    return default, levels


class _LogFilter(logging.Filter):
    """Drops the records that `CODSPEED_TELEMETRY_FILTER` doesn't allow, and adds
    to each kept record its time on the benchmark marker clock."""

    def __init__(
        self, default: int, levels: dict[str, int], clock: Callable[[], int] | None
    ) -> None:
        super().__init__()
        self.default = default
        self.levels = levels
        self.clock = clock

    def level_of(self, name: str) -> int:
        # Checks the exporter loggers first, so that no directive on one of their
        # child loggers can turn them back on.
        if name.partition(".")[0] in EXPORTER_LOGGERS:
            return LEVELS["off"]
        while True:
            level = self.levels.get(name)
            if level is not None:
                return level
            if "." not in name:
                return self.default
            name = name.rpartition(".")[0]

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < self.level_of(record.name):
            return False
        if self.clock is not None:
            # The handler copies this field into the attributes of the exported
            # record.
            record.__dict__[MONOTONIC_TIME_ATTRIBUTE] = self.clock()
        return True


def _monotonic_span_processor(
    processor: SpanProcessor, clock: Callable[[], int]
) -> SpanProcessor:
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace import SpanProcessor as BaseSpanProcessor

    class MonotonicSpanProcessor(BaseSpanProcessor):
        """Adds the start and end times on the benchmark marker clock to each
        span, then gives the span to the wrapped processor.

        It reads the clock when the span starts and ends, at the same moments
        as the SDK reads its own clock. The SDK doesn't let a processor change a
        span after it ends, so the wrapped processor gets a copy with the end
        time."""

        def on_start(self, span: Span, parent_context: Context | None = None) -> None:
            span.set_attribute(MONOTONIC_START_ATTRIBUTE, clock())
            processor.on_start(span, parent_context=parent_context)

        def on_end(self, span: ReadableSpan) -> None:
            end = clock()
            processor.on_end(
                ReadableSpan(
                    name=span.name,
                    context=span.context,
                    parent=span.parent,
                    resource=span.resource,
                    attributes={
                        **(span.attributes or {}),
                        MONOTONIC_END_ATTRIBUTE: end,
                    },
                    events=span.events,
                    links=span.links,
                    kind=span.kind,
                    status=span.status,
                    start_time=span.start_time,
                    end_time=span.end_time,
                    instrumentation_scope=span.instrumentation_scope,
                )
            )

        def shutdown(self) -> None:
            processor.shutdown()

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            return processor.force_flush(timeout_millis)

    return MonotonicSpanProcessor()


def _id_generator() -> RandomIdGenerator:
    from opentelemetry.sdk.trace.id_generator import RandomIdGenerator

    class IndependentIdGenerator(RandomIdGenerator):
        """Makes the ids with its own random generator, not the global one.

        The plugin reseeds the global generator before each benchmark. With the
        global generator, each benchmark would get the same ids, and making the
        ids would change the random numbers that the benchmarks get."""

        def __init__(self) -> None:
            self._random = random.Random()

        def generate_span_id(self) -> int:
            span_id = 0
            while span_id == 0:
                span_id = self._random.getrandbits(64)
            return span_id

        def generate_trace_id(self) -> int:
            trace_id = 0
            while trace_id == 0:
                trace_id = self._random.getrandbits(128)
            return trace_id

    return IndependentIdGenerator()


class Telemetry:
    """Exports the spans and logs of the benchmarked code until `shutdown` is
    called."""

    def __init__(
        self,
        span_processor: SpanProcessor,
        logger_provider: LoggerProvider,
        handler: logging.Handler,
        previous_root_level: int,
    ) -> None:
        self._span_processor = span_processor
        self._logger_provider = logger_provider
        self._handler = handler
        self._previous_root_level = previous_root_level

    def shutdown(self) -> None:
        """Sends the remaining spans and logs, then stops the export."""
        root = logging.getLogger()
        root.removeHandler(self._handler)
        root.setLevel(self._previous_root_level)
        self._span_processor.shutdown()
        self._logger_provider.shutdown()


def start_telemetry(service_name: str) -> Telemetry | None:
    """Starts to export the spans and logs if `CODSPEED_OTEL_ENDPOINT` is set.
    Returns `None` if it is not set."""
    endpoint = os.environ.get(ENDPOINT_ENV, "").rstrip("/")
    if not endpoint:
        return None
    try:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import (
            OTLPLogExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
    except ImportError:
        warnings.warn(
            "The telemetry of the benchmarks is not exported: install the "
            "`telemetry` extra of pytest-codspeed, "
            "e.g., `pip install pytest-codspeed[telemetry]`",
            RuntimeWarning,
            stacklevel=2,
        )
        return None
    return install(
        service_name,
        OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"),
        OTLPLogExporter(endpoint=f"{endpoint}/v1/logs"),
    )


def install(
    service_name: str, span_exporter: SpanExporter, log_exporter: object
) -> Telemetry:
    """Sends the spans of the global tracer provider to `span_exporter`, and the
    records of the `logging` loggers to `log_exporter`."""
    from opentelemetry import trace
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.id_generator import RandomIdGenerator

    resource = Resource.create({SERVICE_NAME: service_name})
    clock = _clock()

    span_processor: SpanProcessor = BatchSpanProcessor(span_exporter)
    if clock is not None:
        span_processor = _monotonic_span_processor(span_processor, clock)

    tracer_provider = trace.get_tracer_provider()
    if isinstance(tracer_provider, TracerProvider):
        # The benchmarked code installed its own provider: add the export to it.
        # Its tracers keep a reference to its id generator, so this code changes
        # the generator in place: the tracers that already exist use the new
        # methods too.
        id_generator = tracer_provider.id_generator
        if type(id_generator) is RandomIdGenerator:
            independent = _id_generator()
            id_generator.generate_span_id = independent.generate_span_id  # type: ignore[method-assign]
            id_generator.generate_trace_id = independent.generate_trace_id  # type: ignore[method-assign]
        tracer_provider.add_span_processor(span_processor)
    else:
        tracer_provider = TracerProvider(
            resource=resource,
            id_generator=_id_generator(),
            shutdown_on_exit=False,
        )
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)

    logger_provider = LoggerProvider(resource=resource, shutdown_on_exit=False)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(log_exporter)  # type: ignore[arg-type]
    )
    default, levels = parse_filter(os.environ.get(FILTER_ENV, DEFAULT_FILTER))
    with warnings.catch_warnings():
        # Recent SDK versions deprecate this handler and move it to another
        # package.
        warnings.simplefilter("ignore", DeprecationWarning)
        handler = LoggingHandler(logger_provider=logger_provider)
    handler.addFilter(_LogFilter(default, levels, clock))

    root = logging.getLogger()
    previous_root_level = root.level
    # By default, the root logger drops the records below `WARNING`. Lower its
    # level so that the records the filter allows get to the handler.
    lowest = min([default, *levels.values()])
    if root.getEffectiveLevel() > lowest:
        root.setLevel(lowest)
    root.addHandler(handler)

    return Telemetry(span_processor, logger_provider, handler, previous_root_level)
