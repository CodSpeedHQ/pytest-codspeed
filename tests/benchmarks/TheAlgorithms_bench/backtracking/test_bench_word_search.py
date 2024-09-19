from backtracking.word_search import word_exists


def test_word_exists(benchmark):
    board = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]
    word = "ABCCED"
    benchmark(word_exists, board, word)
