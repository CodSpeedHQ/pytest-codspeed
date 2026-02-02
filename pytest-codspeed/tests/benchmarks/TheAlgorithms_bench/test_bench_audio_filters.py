import pytest
from audio_filters.butterworth_filter import (
    make_allpass,
    make_bandpass,
    make_highpass,
    make_highshelf,
    make_lowpass,
    make_lowshelf,
    make_peak,
)
from audio_filters.iir_filter import IIRFilter


def test_make_lowpass(benchmark):
    benchmark(make_lowpass, 1000, 48000)


def test_make_highpass(benchmark):
    benchmark(make_highpass, 1000, 48000)


def test_make_bandpass(benchmark):
    benchmark(make_bandpass, 1000, 48000)


def test_make_allpass(benchmark):
    benchmark(make_allpass, 1000, 48000)


def test_make_peak(benchmark):
    benchmark(make_peak, 1000, 48000, 6)


def test_make_lowshelf(benchmark):
    benchmark(make_lowshelf, 1000, 48000, 6)


def test_make_highshelf(benchmark):
    benchmark(make_highshelf, 1000, 48000, 6)


@pytest.mark.parametrize("a_coeffs, b_coeffs", [([1.0, -1.8, 0.81], [0.9, -1.8, 0.81])])
def test_iir_filter_set_coefficients(benchmark, a_coeffs, b_coeffs):
    filt = IIRFilter(2)
    benchmark(filt.set_coefficients, a_coeffs, b_coeffs)


def test_iir_filter_process(benchmark):
    filt = IIRFilter(2)
    benchmark(filt.process, 0)
