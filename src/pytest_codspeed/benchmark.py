from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from pytest_codspeed.utils import get_git_relative_path

if TYPE_CHECKING:
    from typing import Any


def has_args(item: pytest.Item) -> bool:
    return isinstance(item, pytest.Function) and "callspec" in item.__dict__


@dataclass
class Benchmark:
    file: str
    module: str
    groups: list[str]
    name: str
    args: list
    args_names: list[str]

    @classmethod
    def from_item(cls, item: pytest.Item) -> Benchmark:
        file = str(get_git_relative_path(item.path))
        module = "::".join(
            [node.name for node in item.listchain() if isinstance(node, pytest.Class)]
        )
        name = item.originalname if isinstance(item, pytest.Function) else item.name
        args = list(item.callspec.params.values()) if has_args(item) else []
        args_names = list(item.callspec.params.keys()) if has_args(item) else []
        groups = []
        benchmark_marker = item.get_closest_marker("benchmark")
        if benchmark_marker is not None:
            benchmark_marker_kwargs = benchmark_marker.kwargs.get("group")
            if benchmark_marker_kwargs is not None:
                groups.append(benchmark_marker_kwargs)

        return cls(
            file=file,
            module=module,
            groups=groups,
            name=name,
            args=args,
            args_names=args_names,
        )

    @property
    def display_name(self) -> str:
        if len(self.args) == 0:
            args_str = ""
        else:
            arg_blocks = []
            for i, (arg_name, arg_value) in enumerate(zip(self.args_names, self.args)):
                arg_blocks.append(arg_to_str(arg_value, arg_name, i))
            args_str = f"[{'-'.join(arg_blocks)}]"

        return f"{self.name}{args_str}"

    def to_json_string(self) -> str:
        return json.dumps(
            self.__dict__, default=vars, separators=(",", ":"), sort_keys=True
        )


def arg_to_str(arg: Any, arg_name: str, index: int) -> str:
    if type(arg) in [int, float, str]:
        return str(arg)
    if (
        arg is not None
        and type(arg) not in [list, dict, tuple]
        and hasattr(arg, "__str__")
    ):
        return str(arg)
    return f"{arg_name}{index}"
