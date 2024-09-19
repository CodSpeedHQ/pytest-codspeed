from backtracking.coloring import color


def test_color(benchmark):
    graph = [
        [0, 1, 0, 0, 0],
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
    ]
    max_colors = 3
    benchmark(color, graph, max_colors)
