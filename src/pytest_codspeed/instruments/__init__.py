from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, ClassVar, ParamSpec, TypeVar

    import pytest

    from pytest_codspeed.plugin import CodSpeedConfig

    T = TypeVar("T")
    P = ParamSpec("P")


class Instrument(metaclass=ABCMeta):
    instrument: ClassVar[MeasurementMode]

    @abstractmethod
    def __init__(self, config: CodSpeedConfig): ...

    @abstractmethod
    def get_instrument_config_str_and_warns(self) -> tuple[str, list[str]]: ...

    @abstractmethod
    def measure(
        self,
        name: str,
        uri: str,
        fn: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T: ...

    @abstractmethod
    def report(self, session: pytest.Session) -> None: ...

    @abstractmethod
    def get_result_dict(
        self,
    ) -> dict[str, Any]: ...


class MeasurementMode(str, Enum):
    CPUInstrumentation = "cpu_instrumentation"
    WallTime = "walltime"


def get_instrument_from_mode(mode: MeasurementMode) -> type[Instrument]:
    from pytest_codspeed.instruments.cpu_instrumentation import (
        CPUInstrumentationInstrument,
    )
    from pytest_codspeed.instruments.walltime import WallTimeInstrument

    if mode == MeasurementMode.CPUInstrumentation:
        return CPUInstrumentationInstrument
    else:
        return WallTimeInstrument
