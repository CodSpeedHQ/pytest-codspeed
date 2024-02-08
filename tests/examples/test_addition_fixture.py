def test_some_addition_performance(benchmark):
    @benchmark
    def _():
        assert 1 + 1
