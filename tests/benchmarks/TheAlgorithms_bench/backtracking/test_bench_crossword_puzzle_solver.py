from backtracking.crossword_puzzle_solver import solve_crossword


def test_solve_crossword(benchmark):
    puzzle = [[""] * 3 for _ in range(3)]
    words = ["cat", "dog", "car"]
    benchmark(solve_crossword, puzzle, words)
