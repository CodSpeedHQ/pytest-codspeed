import importlib.util
import os
import platform
from pathlib import Path

from setuptools import setup

build_path = (
    Path(__file__).parent / "src/pytest_codspeed/instruments/valgrind/_wrapper/build.py"
)

spec = importlib.util.spec_from_file_location("build", build_path)
assert spec is not None, "The spec should be initialized"
build = importlib.util.module_from_spec(spec)
assert spec.loader is not None, "The loader should be initialized"
spec.loader.exec_module(build)

system = platform.system()
current_arch = platform.machine()

print(f"System: {system} ({current_arch})")

IS_EXTENSION_BUILDABLE = system == "Linux" and current_arch in [
    "x86_64",
    "aarch64",
]

IS_EXTENSION_REQUIRED = (
    os.environ.get("PYTEST_CODSPEED_FORCE_EXTENSION_BUILD") is not None
)

SKIP_EXTENSION_BUILD = (
    os.environ.get("PYTEST_CODSPEED_SKIP_EXTENSION_BUILD") is not None
)

if SKIP_EXTENSION_BUILD and IS_EXTENSION_REQUIRED:
    raise ValueError("Extension build required but the build requires to skip it")

if IS_EXTENSION_REQUIRED and not IS_EXTENSION_BUILDABLE:
    raise ValueError(
        "The extension is required but the current platform is not supported"
    )

ffi_extension = build.ffibuilder.distutils_extension()
ffi_extension.optional = not IS_EXTENSION_REQUIRED

print(
    "CodSpeed native extension is "
    + ("required" if IS_EXTENSION_REQUIRED else "optional")
)

setup(
    package_data={
        "pytest_codspeed": [
            "instruments/valgrind/_wrapper/*.h",
            "instruments/valgrind/_wrapper/*.c",
        ]
    },
    ext_modules=(
        [ffi_extension] if IS_EXTENSION_BUILDABLE and not SKIP_EXTENSION_BUILD else []
    ),
)
