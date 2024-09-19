from backtracking.match_word_pattern import match_word_pattern


def test_match_word_pattern(benchmark):
    benchmark(match_word_pattern, "aba", "GraphTreesGraph")
