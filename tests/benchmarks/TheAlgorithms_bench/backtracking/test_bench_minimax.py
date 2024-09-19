import math

from backtracking.minimax import minimax


def test_minimax(benchmark):
    scores = [90, 23, 6, 33, 21, 65, 123, 34423]
    height = math.log(len(scores), 2)
    benchmark(minimax, 0, 0, True, scores, height)
