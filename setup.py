import os
import platform

from setuptools import setup

system = platform.system()
current_arch = platform.machine()

IS_EXTENSION_REQUIRED = (
    system == "Linux"
    and current_arch
    in [
        "x86_64",
        "arm64",
    ]
    or os.environ.get("PYTEST_CODSPEED_FORCE_EXTENSION") is not None
)

setup(
    package_data={
        "pytest_codspeed": [
            "instruments/valgrind/_wrapper/*.h",
            "instruments/valgrind/_wrapper/*.c",
        ]
    },
    cffi_modules=[
        "src/pytest_codspeed/instruments/valgrind/_wrapper/build.py:ffibuilder"
    ]
    if IS_EXTENSION_REQUIRED
    else [],
)
