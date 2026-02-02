from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, ClassVar, TypeVar

    from typing_extensions import ParamSpec

    from codspeed.config import BenchmarkMarkerOptions, CodSpeedConfig, PedanticOptions

    T = TypeVar("T")
    P = ParamSpec("P")


class Instrument(metaclass=ABCMeta):
    instrument: ClassVar[str]

    @abstractmethod
    def __init__(
        self,
        config: CodSpeedConfig,
        integration_name: str = "pytest-codspeed",
        integration_version: str = "0.0.0",
    ): ...

    @abstractmethod
    def get_instrument_config_str_and_warns(self) -> tuple[str, list[str]]: ...

    @abstractmethod
    def measure(
        self,
        marker_options: BenchmarkMarkerOptions,
        name: str,
        uri: str,
        fn: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T: ...

    @abstractmethod
    def measure_pedantic(
        self,
        marker_options: BenchmarkMarkerOptions,
        pedantic_options: PedanticOptions[T],
        name: str,
        uri: str,
    ) -> T: ...

    @abstractmethod
    def get_result_dict(
        self,
    ) -> dict[str, Any]: ...


class MeasurementMode(str, Enum):
    Simulation = "simulation"
    WallTime = "walltime"

    @classmethod
    def _missing_(cls, value: object):
        # Accept "instrumentation" as deprecated alias for "simulation"
        if value == "instrumentation":
            return cls.Simulation
        return None


def get_instrument_from_mode(mode: MeasurementMode) -> type[Instrument]:
    from codspeed.instruments.valgrind import (
        ValgrindInstrument,
    )
    from codspeed.instruments.walltime import WallTimeInstrument

    if mode == MeasurementMode.Simulation:
        return ValgrindInstrument
    else:
        return WallTimeInstrument
