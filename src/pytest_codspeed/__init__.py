__version__ = "4.0.0b1"
# We also have the semver version since __version__ is not semver compliant
__semver_version__ = "4.0.0-beta1"

from .plugin import BenchmarkFixture

__all__ = ["BenchmarkFixture", "__version__", "__semver_version__"]
