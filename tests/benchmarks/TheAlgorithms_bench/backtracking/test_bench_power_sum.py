from backtracking.power_sum import solve


def test_solve(benchmark):
    benchmark(solve, 13, 2)
