def test_some_addition_performance(benchmark):
    @benchmark
    def _():
        return 1 + 1
