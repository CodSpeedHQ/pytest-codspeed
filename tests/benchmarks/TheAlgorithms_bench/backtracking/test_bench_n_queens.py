from backtracking.n_queens import is_safe, solve


def test_is_safe(benchmark):
    board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    benchmark(is_safe, board, 1, 1)


def test_solve(benchmark):
    board = [[0 for i in range(4)] for j in range(4)]
    benchmark(solve, board, 0)
