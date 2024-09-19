from backtracking.sum_of_subsets import generate_sum_of_subsets_soln


def test_generate_sum_of_subsets_soln(benchmark):
    nums = [3, 34, 4, 12, 5, 2]
    max_sum = 9
    benchmark(generate_sum_of_subsets_soln, nums, max_sum)
