from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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

        options = cls(
            group=marker.kwargs.pop("group", None),
            min_time=marker.kwargs.pop("min_time", None),
            max_time=marker.kwargs.pop("max_time", None),
            max_rounds=marker.kwargs.pop("max_rounds", None),
        )

        if len(marker.kwargs) > 0:
            raise ValueError(
                "Unknown kwargs passed to benchmark marker: "
                + ", ".join(marker.kwargs.keys())
            )
        return options
