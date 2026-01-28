from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, ClassVar, TypeVar

    import pytest
    from typing_extensions import ParamSpec

    from pytest_codspeed.config import BenchmarkMarkerOptions, PedanticOptions
    from pytest_codspeed.plugin import CodSpeedConfig

    T = TypeVar("T")
    P = ParamSpec("P")


class Instrument(metaclass=ABCMeta):
    instrument: ClassVar[str]

    @abstractmethod
    def __init__(self, config: CodSpeedConfig, mode: MeasurementMode): ...

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
    def report(self, session: pytest.Session) -> None: ...

    @abstractmethod
    def get_result_dict(
        self,
    ) -> dict[str, Any]: ...


class MeasurementMode(str, Enum):
    Simulation = "simulation"
    Memory = "memory"
    WallTime = "walltime"

    @classmethod
    def _missing_(cls, value: object):
        # Accept "instrumentation" as deprecated alias for "simulation"
        if value == "instrumentation":
            return cls.Simulation
        return None


def get_instrument_from_mode(mode: MeasurementMode) -> type[Instrument]:
    from pytest_codspeed.instruments.analysis import (
        AnalysisInstrument,
    )
    from pytest_codspeed.instruments.walltime import WallTimeInstrument

    if mode in (MeasurementMode.Simulation, MeasurementMode.Memory):
        return AnalysisInstrument
    else:
        return WallTimeInstrument
