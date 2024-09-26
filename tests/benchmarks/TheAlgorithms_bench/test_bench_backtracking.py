import math

import pytest
from backtracking.all_combinations import combination_lists, generate_all_combinations
from backtracking.all_permutations import generate_all_permutations
from backtracking.all_subsequences import generate_all_subsequences
from backtracking.coloring import color
from backtracking.combination_sum import combination_sum
from backtracking.crossword_puzzle_solver import solve_crossword
from backtracking.generate_parentheses import generate_parenthesis
from backtracking.hamiltonian_cycle import hamilton_cycle
from backtracking.knight_tour import get_valid_pos, is_complete, open_knight_tour
from backtracking.match_word_pattern import match_word_pattern
from backtracking.minimax import minimax
from backtracking.n_queens import is_safe
from backtracking.n_queens import solve as n_queens_solve
from backtracking.n_queens_math import depth_first_search
from backtracking.power_sum import solve
from backtracking.rat_in_maze import solve_maze
from backtracking.sudoku import sudoku
from backtracking.sum_of_subsets import generate_sum_of_subsets_soln
from backtracking.word_search import word_exists


@pytest.mark.parametrize("sequence", [[1, 2, 3], ["A", "B", "C"]])
def test_generate_all_permutations(benchmark, sequence):
    benchmark(generate_all_permutations, sequence)


@pytest.mark.parametrize("n, k", [(4, 2), (0, 0), (5, 4)])
def test_combination_lists(benchmark, n, k):
    benchmark(combination_lists, n, k)


@pytest.mark.parametrize("n, k", [(4, 2), (0, 0), (5, 4)])
def test_generate_all_combinations(benchmark, n, k):
    benchmark(generate_all_combinations, n, k)


@pytest.mark.parametrize("sequence", [[3, 2, 1], ["A", "B"]])
def test_generate_all_subsequences(benchmark, sequence):
    benchmark(generate_all_subsequences, sequence)


@pytest.mark.parametrize("candidates, target", [([2, 3, 5], 8)])
def test_combination_sum(benchmark, candidates, target):
    benchmark(combination_sum, candidates, target)


@pytest.mark.parametrize(
    "initial_grid",
    [
        [
            [3, 0, 6, 5, 0, 8, 4, 0, 0],
            [5, 2, 0, 0, 0, 0, 0, 0, 0],
            [0, 8, 7, 0, 0, 0, 0, 3, 1],
            [0, 0, 3, 0, 1, 0, 0, 8, 0],
            [9, 0, 0, 8, 6, 3, 0, 0, 5],
            [0, 5, 0, 0, 9, 0, 6, 0, 0],
            [1, 3, 0, 0, 0, 0, 2, 5, 0],
            [0, 0, 0, 0, 0, 0, 0, 7, 4],
            [0, 0, 5, 2, 0, 6, 3, 0, 0],
        ]
    ],
)
def test_sudoku(benchmark, initial_grid):
    benchmark(sudoku, initial_grid)


@pytest.mark.parametrize("nums, max_sum", [([3, 34, 4, 12, 5, 2], 9)])
def test_generate_sum_of_subsets_soln(benchmark, nums, max_sum):
    benchmark(generate_sum_of_subsets_soln, nums, max_sum)


@pytest.mark.parametrize("scores", [[90, 23, 6, 33, 21, 65, 123, 34423]])
def test_minimax(benchmark, scores):
    height = math.log(len(scores), 2)
    benchmark(minimax, 0, 0, True, scores, height)


@pytest.mark.parametrize(
    "graph, max_colors",
    [
        (
            [
                [0, 1, 0, 0, 0],
                [1, 0, 1, 0, 1],
                [0, 1, 0, 1, 0],
                [0, 1, 1, 0, 0],
                [0, 1, 0, 0, 0],
            ],
            3,
        )
    ],
)
def test_color(benchmark, graph, max_colors):
    benchmark(color, graph, max_colors)


@pytest.mark.parametrize("n", [3])
def test_generate_parenthesis(benchmark, n):
    benchmark(generate_parenthesis, n)


@pytest.mark.parametrize("x, n", [(13, 2)])
def test_solve_power_sum(benchmark, x, n):
    benchmark(solve, x, n)


@pytest.mark.parametrize("board, row, col", [([[0, 0, 0], [0, 0, 0], [0, 0, 0]], 1, 1)])
def test_is_safe(benchmark, board, row, col):
    benchmark(is_safe, board, row, col)


@pytest.mark.parametrize("board", [[[0 for i in range(4)] for j in range(4)]])
def test_n_queens_solve(benchmark, board):
    benchmark(n_queens_solve, board, 0)


@pytest.mark.parametrize("pattern, string", [("aba", "GraphTreesGraph")])
def test_match_word_pattern(benchmark, pattern, string):
    benchmark(match_word_pattern, pattern, string)


@pytest.mark.parametrize("pos, board_size", [((1, 3), 4)])
def test_get_valid_pos(benchmark, pos, board_size):
    benchmark(get_valid_pos, pos, board_size)


@pytest.mark.parametrize("board", [[[1]]])
def test_is_complete(benchmark, board):
    benchmark(is_complete, board)


@pytest.mark.parametrize("board_size", [1])
def test_open_knight_tour(benchmark, board_size):
    benchmark(open_knight_tour, board_size)


@pytest.mark.parametrize(
    "graph",
    [
        [
            [0, 1, 0, 1, 0],
            [1, 0, 1, 1, 1],
            [0, 1, 0, 0, 1],
            [1, 1, 0, 0, 1],
            [0, 1, 1, 1, 0],
        ]
    ],
)
def test_hamilton_cycle(benchmark, graph):
    benchmark(hamilton_cycle, graph)


@pytest.mark.parametrize(
    "maze",
    [
        [
            [0, 1, 0, 1, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 1, 0, 0],
            [1, 0, 0, 1, 0],
        ]
    ],
)
def test_solve_maze(benchmark, maze):
    benchmark(solve_maze, maze, 0, 0, len(maze) - 1, len(maze) - 1)


@pytest.mark.parametrize(
    "board, word",
    [([["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCCED")],
)
def test_word_exists(benchmark, board, word):
    benchmark(word_exists, board, word)


@pytest.mark.parametrize(
    "puzzle, words", [([[""] * 3 for _ in range(3)], ["cat", "dog", "car"])]
)
def test_solve_crossword(benchmark, puzzle, words):
    benchmark(solve_crossword, puzzle, words)


@pytest.mark.parametrize("n", [4])
def test_depth_first_search(benchmark, n):
    boards = []
    benchmark(depth_first_search, [], [], [], boards, n)
