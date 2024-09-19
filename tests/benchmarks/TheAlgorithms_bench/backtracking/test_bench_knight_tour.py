from backtracking.knight_tour import get_valid_pos, is_complete, open_knight_tour


def test_get_valid_pos(benchmark):
    benchmark(get_valid_pos, (1, 3), 4)


def test_is_complete(benchmark):
    benchmark(is_complete, [[1]])


def test_open_knight_tour(benchmark):
    benchmark(open_knight_tour, 1)
