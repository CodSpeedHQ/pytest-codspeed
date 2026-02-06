"""Foo / bar / baz benchmarks for asv-codspeed."""


def time_foo():
    total = 0
    for i in range(500):
        total += i
    return total


def time_bar():
    data = list(range(200))
    return sorted(data, reverse=True)


def time_baz():
    return {k: k * k for k in range(300)}
