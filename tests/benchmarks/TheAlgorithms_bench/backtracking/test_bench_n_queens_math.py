from backtracking.n_queens_math import depth_first_search


def test_depth_first_search(benchmark):
    boards = []
    benchmark(depth_first_search, [], [], [], boards, 4)
