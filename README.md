<div align="center">
<h1>pytest-codspeed</h1>

[![CI](https://github.com/CodSpeedHQ/pytest-codspeed/actions/workflows/ci.yml/badge.svg)](https://github.com/CodSpeedHQ/pytest-codspeed/actions/workflows/ci.yml)
[![PyPi Version](https://img.shields.io/pypi/v/pytest-codspeed?color=%2334D058&label=pypi)](https://pypi.org/project/pytest-codspeed)
![Python Version](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-informational.svg)
[![Discord](https://img.shields.io/badge/chat%20on-discord-7289da.svg)](https://discord.com/invite/MxpaCfKSqF)
[![CodSpeed Badge](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/CodSpeedHQ/pytest-codspeed)

Pytest plugin to create CodSpeed benchmarks

</div>

## Requirements

**Python**: 3.8 and later

**pytest**: any recent version

## Installation

```shell
pip install pytest-codspeed
```

## Usage

### Creating benchmarks

Creating benchmarks with `pytest-codspeed` is compatible with the standard `pytest-benchmark` API. So if you already have benchmarks written with it, you can start using `pytest-codspeed` right away.

#### Marking a whole test function as a benchmark with `pytest.mark.benchmark`

```python
import pytest
from statistics import median

@pytest.mark.benchmark
def test_median_performance():
    return median([1, 2, 3, 4, 5])
```

#### Benchmarking selected lines of a test function with the `benchmark` fixture

```python
import pytest
from statistics import mean

def test_mean_performance(benchmark):
    # Precompute some data useful for the benchmark but that should not be
    # included in the benchmark time
    data = [1, 2, 3, 4, 5]

    # Benchmark the execution of the function
    benchmark(lambda: mean(data))


def test_mean_and_median_performance(benchmark):
    # Precompute some data useful for the benchmark but that should not be
    # included in the benchmark time
    data = [1, 2, 3, 4, 5]

    # Benchmark the execution of the function:
    # The `@benchmark` decorator will automatically call the function and
    # measure its execution
    @benchmark
    def bench():
        mean(data)
        median(data)
```

### Running benchmarks

#### Testing the benchmarks locally

If you want to run only the benchmarks tests locally, you can use the `--codspeed` pytest flag:

```shell
pytest tests/ --codspeed
```

> **Note:** Running `pytest-codspeed` locally will not produce any performance reporting. It's only useful for making sure that your benchmarks are working as expected. If you want to get performance reporting, you should run the benchmarks in your CI.

#### In your CI

You can use the [CodSpeedHQ/action](https://github.com/CodSpeedHQ/action) to run the benchmarks in Github Actions and upload the results to CodSpeed.

Example workflow:

```yaml
name: benchmarks

on:
  push:
    branches:
      - "main" # or "master"
  pull_request:

jobs:
  benchmarks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run benchmarks
        uses: CodSpeedHQ/action@v3
        with:
          token: ${{ secrets.CODSPEED_TOKEN }}
          run: pytest tests/ --codspeed
```
