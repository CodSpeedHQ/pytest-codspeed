from backtracking.all_combinations import combination_lists, generate_all_combinations


def test_combination_lists(benchmark):
    benchmark(combination_lists, n=4, k=2)


def test_generate_all_combinations(benchmark):
    benchmark(generate_all_combinations, n=4, k=2)


def test_generate_all_combinations_edge_case(benchmark):
    benchmark(generate_all_combinations, n=0, k=0)


def test_generate_all_combinations_larger(benchmark):
    benchmark(generate_all_combinations, n=5, k=4)
