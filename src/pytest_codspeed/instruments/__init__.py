from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, ClassVar, ParamSpec, TypeVar

    import pytest

    T = TypeVar("T")
    P = ParamSpec("P")


class Instrument(metaclass=ABCMeta):
    instrument: ClassVar[CodSpeedMeasurementMode]

    @abstractmethod
    def __init__(self): ...

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


class CodSpeedMeasurementMode(str, Enum):
    Instrumentation = "instrumentation"
    WallTime = "walltime"


def get_instrument_from_mode(mode: CodSpeedMeasurementMode) -> type[Instrument]:
    from pytest_codspeed.instruments.instrumentation import InstrumentationInstrument
    from pytest_codspeed.instruments.walltime import WallTimeInstrument

    if mode == CodSpeedMeasurementMode.Instrumentation:
        return InstrumentationInstrument
    else:
        return WallTimeInstrument
