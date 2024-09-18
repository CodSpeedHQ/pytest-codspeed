from audio_filters.iir_filter import IIRFilter


def test_set_coefficients(benchmark):
    filt = IIRFilter(2)
    a_coeffs = [1.0, -1.8, 0.81]
    b_coeffs = [0.9, -1.8, 0.81]
    benchmark(filt.set_coefficients, a_coeffs, b_coeffs)


def test_process(benchmark):
    filt = IIRFilter(2)
    benchmark(filt.process, 0)
