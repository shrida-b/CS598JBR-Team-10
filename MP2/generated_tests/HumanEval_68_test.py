import pytest
from HumanEval_68 import *
from HumanEval_68 import pluck

import pytest
from HumanEval_68 import pluck

def test_empty_array():
    """
    Test the function with an empty array.
    """
    assert pluck([]) == []

def test_no_even_numbers():
    """
    Test the function with an array that contains no even numbers.
    """
    assert pluck([1, 3, 5, 7, 9]) == []

def test_single_even_number():
    """
    Test the function with an array that contains a single even number.
    """
    assert pluck([2]) == [2, 0]

def test_multiple_even_numbers():
    """
    Test the function with an array that contains multiple even numbers.
    """
    assert pluck([2, 4, 6, 8, 10]) == [2, 0]

def test_smallest_even_number_at_different_positions():
    """
    Test the function with an array that contains multiple even numbers and the smallest even number is at different positions.
    """
    assert pluck([3, 2, 5, 4, 7, 6, 9, 8, 10]) == [2, 1]

def test_multiple_smallest_even_numbers():
    """
    Test the function with an array that contains multiple smallest even numbers.
    """
    assert pluck([2, 2, 2, 2, 2, 2, 2, 2, 2]) == [2, 0]

def test_large_input():
    """
    Test the function with a large input array.
    """
    arr = list(range(10000))
    assert pluck(arr) == [0, 0]
