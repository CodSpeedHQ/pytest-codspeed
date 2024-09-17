def noop_pass():
    pass


def noop_ellipsis(): ...


def noop_lambda():
    (lambda: None)()


def test_noop_pass(benchmark):
    benchmark(noop_pass)


def test_noop_ellipsis(benchmark):
    benchmark(noop_ellipsis)


def test_noop_lambda(benchmark):
    benchmark(noop_lambda)


def test_noop_pass_decorated(benchmark):
    @benchmark
    def _():
        noop_pass()


def test_noop_ellipsis_decorated(benchmark):
    @benchmark
    def _():
        noop_ellipsis()


def test_noop_lambda_decorated(benchmark):
    @benchmark
    def _():
        noop_lambda()
