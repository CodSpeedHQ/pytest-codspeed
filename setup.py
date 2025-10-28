import os
import platform

from setuptools import Extension, setup

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

# Build native C extension
native_extension = Extension(
    "pytest_codspeed.instruments.hooks.dist_instrument_hooks",
    sources=[
        "src/pytest_codspeed/instruments/hooks/instrument_hooks_module.c",
        "src/pytest_codspeed/instruments/hooks/instrument-hooks/dist/core.c",
    ],
    include_dirs=["src/pytest_codspeed/instruments/hooks/instrument-hooks/includes"],
    optional=not IS_EXTENSION_REQUIRED,
)

print(
    "CodSpeed native extension is "
    + ("required" if IS_EXTENSION_REQUIRED else "optional")
)

setup(
    ext_modules=(
        [native_extension]
        if IS_EXTENSION_BUILDABLE and not SKIP_EXTENSION_BUILD
        else []
    ),
)
