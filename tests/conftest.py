import pkgutil
import sys

pytest_plugins = ["pytester"]

if pkgutil.find_loader("pytest_benchmark") is not None:
    pytest_plugins.append("pytest_benchmark")
    print("NOTICE: Testing with pytest-benchmark compatibility", file=sys.stderr)
