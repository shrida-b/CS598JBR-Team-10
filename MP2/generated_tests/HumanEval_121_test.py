import pytest
from HumanEval_121 import *
from HumanEval_121 import solution

import pytest
from HumanEval_121 import solution

def test_odd_sum_in_even_positions_1():
    """Testing the sum of odd numbers in even positions"""
    assert solution([5, 8, 7, 1]) == 12

def test_odd_sum_in_even_positions_2():
    """Testing the sum of odd numbers in even positions"""
    assert solution([3, 3, 3, 3, 3]) == 9

def test_odd_sum_in_even_positions_3():
    """Testing the sum of odd numbers in even positions"""
    assert solution([30, 13, 24, 321]) == 0

def test_empty_list():
    """Testing with an empty list"""
    with pytest.raises(IndexError):
        solution([])

def test_negative_numbers():
    """Testing with negative numbers"""
    assert solution([-5, 8, -7, 1]) == 0

def test_large_numbers():
    """Testing with large numbers"""
    assert solution([1000000000, 8, 7, 1]) == 1000000000

def test_zero():
    """Testing with zero"""
    assert solution([0, 8, 7, 1]) == 8

def test_one_element():
    """Testing with one element"""
    assert solution([5]) == 0

def test_all_even_numbers():
    """Testing with all even numbers"""
    assert solution([2, 4, 6, 8, 10]) == 0

def test_all_odd_numbers():
    """Testing with all odd numbers"""
    assert solution([1, 3, 5, 7, 9]) == 0
