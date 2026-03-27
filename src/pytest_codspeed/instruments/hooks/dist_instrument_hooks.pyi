from cffi import FFI

InstrumentHooksPointer = object

class lib:
    @staticmethod
    def instrument_hooks_init() -> InstrumentHooksPointer: ...
    @staticmethod
    def instrument_hooks_deinit(hooks: InstrumentHooksPointer) -> None: ...
    @staticmethod
    def instrument_hooks_is_instrumented(hooks: InstrumentHooksPointer) -> bool: ...
    @staticmethod
    def instrument_hooks_start_benchmark(hooks: InstrumentHooksPointer) -> int: ...
    @staticmethod
    def instrument_hooks_stop_benchmark(hooks: InstrumentHooksPointer) -> int: ...
    @staticmethod
    def instrument_hooks_set_executed_benchmark(
        hooks: InstrumentHooksPointer, pid: int, uri: bytes
    ) -> int: ...
    @staticmethod
    def instrument_hooks_set_integration(
        hooks: InstrumentHooksPointer, name: bytes, version: bytes
    ) -> int: ...
    @staticmethod
    def instrument_hooks_add_marker(
        hooks: InstrumentHooksPointer, pid: int, marker_type: int, timestamp: int
    ) -> int: ...
    @staticmethod
    def instrument_hooks_current_timestamp() -> int: ...
    @staticmethod
    def callgrind_start_instrumentation() -> int: ...
    @staticmethod
    def callgrind_stop_instrumentation() -> int: ...
    @staticmethod
    def instrument_hooks_set_feature(feature: int, enabled: bool) -> None: ...
    @staticmethod
    def instrument_hooks_set_environment(
        hooks: InstrumentHooksPointer, section_name: bytes, key: bytes, value: bytes
    ) -> int: ...
    @staticmethod
    def instrument_hooks_set_environment_list(
        hooks: InstrumentHooksPointer,
        section_name: bytes,
        key: bytes,
        values: FFI.CData,
        count: int,
    ) -> int: ...
    @staticmethod
    def instrument_hooks_write_environment(
        hooks: InstrumentHooksPointer, pid: int
    ) -> int: ...

LibType = type[lib]
