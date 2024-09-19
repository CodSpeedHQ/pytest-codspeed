from backtracking.all_subsequences import generate_all_subsequences


def test_generate_all_subsequences(benchmark):
    sequence = [3, 2, 1]
    benchmark(generate_all_subsequences, sequence)


def test_generate_all_subsequences_str(benchmark):
    sequence = ["A", "B"]
    benchmark(generate_all_subsequences, sequence)
