# Rebuild the native extension and reinstall pytest-codspeed locally.
rebuild:
    PYTEST_CODSPEED_FORCE_EXTENSION_BUILD=1 uv sync --all-extras --dev --reinstall-package pytest-codspeed
