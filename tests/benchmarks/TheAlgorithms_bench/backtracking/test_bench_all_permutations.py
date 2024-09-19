from backtracking.all_permutations import generate_all_permutations


def test_generate_all_permutations(benchmark):
    sequence = [1, 2, 3]
    benchmark(generate_all_permutations, sequence)


def test_generate_all_permutations_str(benchmark):
    sequence = ["A", "B", "C"]
    benchmark(generate_all_permutations, sequence)
