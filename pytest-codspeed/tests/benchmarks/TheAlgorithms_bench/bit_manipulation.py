import pytest
from bit_manipulation.binary_and_operator import binary_and
from bit_manipulation.binary_coded_decimal import binary_coded_decimal
from bit_manipulation.binary_count_setbits import binary_count_setbits
from bit_manipulation.binary_count_trailing_zeros import binary_count_trailing_zeros
from bit_manipulation.binary_or_operator import binary_or
from bit_manipulation.binary_shifts import (
    arithmetic_right_shift,
    logical_left_shift,
    logical_right_shift,
)
from bit_manipulation.binary_twos_complement import twos_complement
from bit_manipulation.binary_xor_operator import binary_xor
from bit_manipulation.count_1s_brian_kernighan_method import get_1s_count
from bit_manipulation.excess_3_code import excess_3_code
from bit_manipulation.find_previous_power_of_two import find_previous_power_of_two
from bit_manipulation.gray_code_sequence import gray_code
from bit_manipulation.highest_set_bit import get_highest_set_bit_position
from bit_manipulation.is_even import is_even
from bit_manipulation.largest_pow_of_two_le_num import largest_pow_of_two_le_num
from bit_manipulation.missing_number import find_missing_number
from bit_manipulation.numbers_different_signs import different_signs
from bit_manipulation.power_of_4 import power_of_4
from bit_manipulation.reverse_bits import reverse_bit
from bit_manipulation.single_bit_manipulation_operations import (
    clear_bit,
    flip_bit,
    get_bit,
    is_bit_set,
    set_bit,
)
from bit_manipulation.swap_all_odd_and_even_bits import swap_odd_even_bits


@pytest.mark.parametrize("a, b", [(25, 32), (37, 50), (21, 30), (58, 73)])
def test_binary_and(benchmark, a, b):
    benchmark(binary_and, a, b)


@pytest.mark.parametrize("a, b", [(25, 32), (37, 50), (21, 30), (58, 73)])
def test_binary_or(benchmark, a, b):
    benchmark(binary_or, a, b)


@pytest.mark.parametrize("a, b", [(25, 32), (37, 50), (21, 30), (58, 73)])
def test_binary_xor(benchmark, a, b):
    benchmark(binary_xor, a, b)


@pytest.mark.parametrize("a", [25, 36, 16, 58, 4294967295, 0])
def test_binary_count_setbits(benchmark, a):
    benchmark(binary_count_setbits, a)


@pytest.mark.parametrize("a", [25, 36, 16, 58, 4294967296, 0])
def test_binary_count_trailing_zeros(benchmark, a):
    benchmark(binary_count_trailing_zeros, a)


@pytest.mark.parametrize("a", [-1, -5, -17, -207])
def test_twos_complement(benchmark, a):
    benchmark(twos_complement, a)


@pytest.mark.parametrize("a", [25, 37, 21, 58, 0, 256])
def test_get_1s_count(benchmark, a):
    benchmark(get_1s_count, a)


@pytest.mark.parametrize("a", [25, 37, 21, 58, 0, 256])
def test_reverse_bit(benchmark, a):
    benchmark(reverse_bit, a)


@pytest.mark.parametrize("number, position", [(0b1101, 1), (0b0, 5), (0b1111, 1)])
def test_set_bit(benchmark, number, position):
    benchmark(set_bit, number, position)


@pytest.mark.parametrize("number, position", [(0b10010, 1), (0b0, 5)])
def test_clear_bit(benchmark, number, position):
    benchmark(clear_bit, number, position)


@pytest.mark.parametrize("number, position", [(0b101, 1), (0b101, 0)])
def test_flip_bit(benchmark, number, position):
    benchmark(flip_bit, number, position)


@pytest.mark.parametrize(
    "number, position", [(0b1010, 0), (0b1010, 1), (0b1010, 2), (0b1010, 3), (0b0, 17)]
)
def test_is_bit_set(benchmark, number, position):
    benchmark(is_bit_set, number, position)


@pytest.mark.parametrize(
    "number, position", [(0b1010, 0), (0b1010, 1), (0b1010, 2), (0b1010, 3)]
)
def test_get_bit(benchmark, number, position):
    benchmark(get_bit, number, position)


@pytest.mark.parametrize(
    "number, shift_amount", [(0, 1), (1, 1), (1, 5), (17, 2), (1983, 4)]
)
def test_logical_left_shift(benchmark, number, shift_amount):
    benchmark(logical_left_shift, number, shift_amount)


@pytest.mark.parametrize(
    "number, shift_amount", [(0, 1), (1, 1), (1, 5), (17, 2), (1983, 4)]
)
def test_logical_right_shift(benchmark, number, shift_amount):
    benchmark(logical_right_shift, number, shift_amount)


@pytest.mark.parametrize(
    "number, shift_amount", [(0, 1), (1, 1), (-1, 1), (17, 2), (-17, 2), (-1983, 4)]
)
def test_arithmetic_right_shift(benchmark, number, shift_amount):
    benchmark(arithmetic_right_shift, number, shift_amount)


@pytest.mark.parametrize("number", [0, 3, 2, 12, 987])
def test_binary_coded_decimal(benchmark, number):
    benchmark(binary_coded_decimal, number)


@pytest.mark.parametrize("number", [0, 3, 2, 20, 120])
def test_excess_3_code(benchmark, number):
    benchmark(excess_3_code, number)


@pytest.mark.parametrize("number", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 16, 17])
def test_find_previous_power_of_two(benchmark, number):
    benchmark(find_previous_power_of_two, number)


@pytest.mark.parametrize("bit_count", [1, 2, 3])
def test_gray_code(benchmark, bit_count):
    benchmark(gray_code, bit_count)


@pytest.mark.parametrize("number", [25, 37, 1, 4, 0])
def test_get_highest_set_bit_position(benchmark, number):
    benchmark(get_highest_set_bit_position, number)


@pytest.mark.parametrize("number", [1, 4, 9, 15, 40, 100, 101])
def test_is_even(benchmark, number):
    benchmark(is_even, number)


@pytest.mark.parametrize("number", [0, 1, 3, 15, 99, 178, 999999])
def test_largest_pow_of_two_le_num(benchmark, number):
    benchmark(largest_pow_of_two_le_num, number)


@pytest.mark.parametrize(
    "nums",
    [
        [0, 1, 3, 4],
        [4, 3, 1, 0],
        [-4, -3, -1, 0],
        [-2, 2, 1, 3, 0],
        [1, 3, 4, 5, 6],
        [6, 5, 4, 2, 1],
        [6, 1, 5, 3, 4],
    ],
)
def test_find_missing_number(benchmark, nums):
    benchmark(find_missing_number, nums)


@pytest.mark.parametrize(
    "num1, num2",
    [
        (1, -1),
        (1, 1),
        (1000000000000000000000000000, -1000000000000000000000000000),
        (-1000000000000000000000000000, 1000000000000000000000000000),
        (50, 278),
        (0, 2),
        (2, 0),
    ],
)
def test_different_signs(benchmark, num1, num2):
    benchmark(different_signs, num1, num2)


@pytest.mark.parametrize("number", [1, 2, 4, 6, 8, 17, 64])
def test_power_of_4(benchmark, number):
    benchmark(power_of_4, number)


@pytest.mark.parametrize("number", [0, 1, 2, 3, 4, 5, 6, 23, 24])
def test_swap_odd_even_bits(benchmark, number):
    benchmark(swap_odd_even_bits, number)
