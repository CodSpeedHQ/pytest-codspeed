from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

T = TypeVar("T")

if TYPE_CHECKING:
    from typing import Any, Callable

    import pytest


@dataclass(frozen=True)
class CodSpeedConfig:
    """
    The configuration for the codspeed plugin.
    Usually created from the command line arguments.
    """

    warmup_time_ns: int | None = None
    max_time_ns: int | None = None
    max_rounds: int | None = None

    @classmethod
    def from_pytest_config(cls, config: pytest.Config) -> CodSpeedConfig:
        warmup_time = config.getoption("--codspeed-warmup-time", None)
        warmup_time_ns = (
            int(warmup_time * 1_000_000_000) if warmup_time is not None else None
        )
        max_time = config.getoption("--codspeed-max-time", None)
        max_time_ns = int(max_time * 1_000_000_000) if max_time is not None else None
        return cls(
            warmup_time_ns=warmup_time_ns,
            max_rounds=config.getoption("--codspeed-max-rounds", None),
            max_time_ns=max_time_ns,
        )


@dataclass(frozen=True)
class BenchmarkMarkerOptions:
    group: str | None = None
    """The group name to use for the benchmark."""
    min_time: int | None = None
    """
    The minimum time of a round (in seconds).
    Only available in walltime mode.
    """
    max_time: int | None = None
    """
    The maximum time to run the benchmark for (in seconds).
    Only available in walltime mode.
    """
    max_rounds: int | None = None
    """
    The maximum number of rounds to run the benchmark for.
    Takes precedence over max_time. Only available in walltime mode.
    """

    @classmethod
    def from_pytest_item(cls, item: pytest.Item) -> BenchmarkMarkerOptions:
        marker = item.get_closest_marker(
            "codspeed_benchmark"
        ) or item.get_closest_marker("benchmark")
        if marker is None:
            return cls()
        if len(marker.args) > 0:
            raise ValueError(
                "Positional arguments are not allowed in the benchmark marker"
            )
        kwargs = marker.kwargs

        unknown_kwargs = set(kwargs.keys()) - {
            field.name for field in dataclasses.fields(cls)
        }
        if unknown_kwargs:
            raise ValueError(
                "Unknown kwargs passed to benchmark marker: "
                + ", ".join(sorted(unknown_kwargs))
            )

        return cls(**kwargs)


@dataclass(frozen=True)
class PedanticOptions(Generic[T]):
    """Parameters for running a benchmark using the pedantic fixture API."""

    target: Callable[..., T]
    setup: Callable[[], Any | None] | None
    teardown: Callable[..., Any | None] | None
    rounds: int
    warmup_rounds: int
    iterations: int
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.rounds < 0:
            raise ValueError("rounds must be positive")
        if self.warmup_rounds < 0:
            raise ValueError("warmup_rounds must be non-negative")
        if self.iterations <= 0:
            raise ValueError("iterations must be positive")
        if self.iterations > 1 and self.setup is not None:
            raise ValueError(
                "setup cannot be used with multiple iterations, use multiple rounds"
            )

    def setup_and_get_args_kwargs(self) -> tuple[tuple[Any, ...], dict[str, Any]]:
        if self.setup is None:
            return self.args, self.kwargs
        maybe_result = self.setup(*self.args, **self.kwargs)
        if maybe_result is not None:
            if len(self.args) > 0 or len(self.kwargs) > 0:
                raise ValueError("setup cannot return a value when args are provided")
            return maybe_result
        return self.args, self.kwargs
