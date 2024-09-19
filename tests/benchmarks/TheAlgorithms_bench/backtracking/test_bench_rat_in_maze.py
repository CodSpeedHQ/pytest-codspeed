from backtracking.rat_in_maze import solve_maze


def test_solve_maze(benchmark):
    maze = [
        [0, 1, 0, 1, 1],
        [0, 0, 0, 0, 0],
        [1, 0, 1, 0, 1],
        [0, 0, 1, 0, 0],
        [1, 0, 0, 1, 0],
    ]
    benchmark(solve_maze, maze, 0, 0, len(maze) - 1, len(maze) - 1)
