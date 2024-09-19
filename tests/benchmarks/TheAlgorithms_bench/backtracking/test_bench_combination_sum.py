from backtracking.combination_sum import combination_sum


def test_combination_sum(benchmark):
    candidates = [2, 3, 5]
    target = 8
    benchmark(combination_sum, candidates, target)
