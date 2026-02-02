"""Recursive Fibonacci benchmark for asv-codspeed."""


def _fibo(n):
    if n <= 1:
        return n
    return _fibo(n - 1) + _fibo(n - 2)


def time_recursive_fibo_10():
    _fibo(10)
