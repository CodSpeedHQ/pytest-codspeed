from backtracking.generate_parentheses import generate_parenthesis


def test_generate_parenthesis(benchmark):
    n = 3
    benchmark(generate_parenthesis, n)
