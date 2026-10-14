import pytest
from HumanEval_47 import *
from HumanEval_47 import median

import pytest
from HumanEval_47 import median

def test_empty_list():
    """Test with an empty list"""
    assert median([]) == None

def test_single_element():
    """Test with a single element"""
    assert median([5]) == 5

def test_even_length_list():
    """Test with an even length list"""
    assert median([1, 2, 3, 4]) == 2.5

def test_odd_length_list():
    """Test with an odd length list"""
    assert median([1, 2, 3]) == 2

def test_negative_numbers():
    """Test with negative numbers"""
    assert median([-1, -2, -3]) == -2

def test_positive_and_negative_numbers():
    """Test with positive and negative numbers"""
    assert median([-3, -2, 1, 2, 3]) == 0

def test_large_numbers():
    """Test with large numbers"""
    assert median([1000000, 2000000, 3000000]) == 2000000

def test_duplicates():
    """Test with duplicate numbers"""
    assert median([1, 1, 2, 2]) == 1.5

def test_non_integer_numbers():
    """Test with non-integer numbers"""
    assert median([1.5, 2.5, 3.5]) == 2.5
