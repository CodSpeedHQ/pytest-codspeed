<div align="center">
<h1>pytest-codspeed</h1>

[![CI](https://github.com/CodSpeedHQ/pytest-codspeed/actions/workflows/ci.yml/badge.svg)](https://github.com/CodSpeedHQ/pytest-codspeed/actions/workflows/ci.yml)
[![PyPi Version](https://img.shields.io/pypi/v/pytest-codspeed?color=%2334D058&label=pypi)](https://pypi.org/project/pytest-codspeed)
![Python Version](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-informational.svg)
[![Discord](https://img.shields.io/badge/chat%20on-discord-7289da.svg)](https://discord.com/invite/MxpaCfKSqF)
[![CodSpeed Badge](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/CodSpeedHQ/pytest-codspeed)

Pytest plugin to create CodSpeed benchmarks

</div>

---

**Documentation**: https://codspeed.io/docs/reference/pytest-codspeed

---

## Installation

```shell
pip install pytest-codspeed
```

## Usage

### Creating benchmarks

In a nutshell, `pytest-codspeed` offers two approaches to create performance benchmarks that integrate seamlessly with your existing test suite.

Use `@pytest.mark.benchmark` to measure entire test functions automatically:

```python
import pytest
from statistics import median

@pytest.mark.benchmark
def test_median_performance():
    input = [1, 2, 3, 4, 5]
    output = sum(i**2 for i in input)
    assert output == 55
```

Since this measure the entire function, you might want to use the `benchmark` fixture for precise control over what code gets measured:

```python
def test_mean_performance(benchmark):
    data = [1, 2, 3, 4, 5]
    # Only the function call is measured
    result = benchmark(lambda: sum(i**2 for i in data))
    assert result == 55
```

Check out the [full documentation](https://codspeed.io/docs/reference/pytest-codspeed) for more details.

### Testing the benchmarks locally

If you want to run the benchmarks tests locally, you can use the `--codspeed` pytest flag:

```sh
$ pytest tests/ --codspeed
============================= test session starts ====================
platform darwin -- Python 3.13.0, pytest-7.4.4, pluggy-1.5.0
codspeed: 3.0.0 (enabled, mode: walltime, timer_resolution: 41.7ns)
rootdir: /home/user/codspeed-test, configfile: pytest.ini
plugins: codspeed-3.0.0
collected 1 items

tests/test_sum_squares.py .                                    [ 100%]

                         Benchmark Results
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃     Benchmark  ┃ Time (best) ┃ Rel. StdDev ┃ Run time ┃ Iters  ┃
┣━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━╋━━━━━━━━━━━━━╋━━━━━━━━━━╋━━━━━━━━┫
┃test_sum_squares┃     1,873ns ┃        4.8% ┃    3.00s ┃ 66,930 ┃
┗━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━┻━━━━━━━━━━━━━┻━━━━━━━━━━┻━━━━━━━━┛
=============================== 1 benchmarked ========================
=============================== 1 passed in 4.12s ====================
```

### Running the benchmarks in your CI

You can use the [CodSpeedHQ/action](https://github.com/CodSpeedHQ/action) to run the benchmarks in Github Actions and upload the results to CodSpeed.

Here is an example of a GitHub Actions workflow that runs the benchmarks and reports the results to CodSpeed on every push to the `main` branch and every pull request:

```yaml
name: CodSpeed

on:
  push:
    branches:
      - "main" # or "master"
  pull_request: # required to have reports on PRs
  # `workflow_dispatch` allows CodSpeed to trigger backtest
  # performance analysis in order to generate initial data.
  workflow_dispatch:

jobs:
  benchmarks:
    name: Run benchmarks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run benchmarks
        uses: CodSpeedHQ/action@v4
        with:
          mode: instrumentation   # or `walltime`
          token: ${{ secrets.CODSPEED_TOKEN }}
          run: pytest tests/ --codspeed
```
