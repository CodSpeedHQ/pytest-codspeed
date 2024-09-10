from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable, ParamSpec, TypeVar

    import pytest

    T = TypeVar("T")
    P = ParamSpec("P")


class Instrument(metaclass=ABCMeta):
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


class CodSpeedMeasurementMode(str, Enum):
    Instrumentation = "instrumentation"


def get_instrument_from_mode(mode: CodSpeedMeasurementMode) -> type[Instrument]:
    from pytest_codspeed.instruments.instrumentation import InstrumentationInstrument

    return InstrumentationInstrument
