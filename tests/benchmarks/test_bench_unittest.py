import unittest

import pytest


class MyBenchmark(unittest.TestCase):
    def setUp(self):
        # Initialize the benchmark environment
        self.input = (
            "Lorem Ipsum is simply dummy text of the printing and typesetting industry."
            * 100
        )

    @pytest.mark.benchmark
    def test_bench_hash(self):
        hash(self.input)

    def tearDown(self):
        # Clean up the benchmark environment
        pass
