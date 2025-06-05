from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, ClassVar, TypeVar

    import pytest

    from pytest_codspeed.config import BenchmarkMarkerOptions, PedanticOptions
    from pytest_codspeed.plugin import CodSpeedConfig

    T = TypeVar("T")


class Instrument(metaclass=ABCMeta):
    instrument: ClassVar[str]

    @abstractmethod
    def __init__(self, config: CodSpeedConfig): ...

    @abstractmethod
    def get_instrument_config_str_and_warns(self) -> tuple[str, list[str]]: ...

    @abstractmethod
    def measure(
        self,
        marker_options: BenchmarkMarkerOptions,
        name: str,
        uri: str,
        fn: Callable[..., T],
        *args: tuple,
        **kwargs: dict[str, Any],
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
    Instrumentation = "instrumentation"
    WallTime = "walltime"


def get_instrument_from_mode(mode: MeasurementMode) -> type[Instrument]:
    from pytest_codspeed.instruments.valgrind import (
        ValgrindInstrument,
    )
    from pytest_codspeed.instruments.walltime import WallTimeInstrument

    if mode == MeasurementMode.Instrumentation:
        return ValgrindInstrument
    else:
        return WallTimeInstrument
