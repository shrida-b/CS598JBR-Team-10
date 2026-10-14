import pytest
from HumanEval_110 import *
from HumanEval_110 import exchange

import pytest
from HumanEval_110 import exchange

def test_exchange_empty_lists():
    """Test with empty lists"""
    assert exchange([], []) == 'YES'

def test_exchange_all_even_numbers():
    """Test with all even numbers"""
    assert exchange([2, 4, 6, 8], [1, 3, 5, 7]) == 'YES'

def test_exchange_all_odd_numbers():
    """Test with all odd numbers"""
    assert exchange([1, 3, 5, 7], [2, 4, 6, 8]) == 'NO'

def test_exchange_mix_of_odd_and_even_numbers():
    """Test with mix of odd and even numbers"""
    assert exchange([1, 2, 3, 4], [1, 2, 3, 4]) == 'YES'

def test_exchange_with_large_inputs():
    """Test with large inputs"""
    lst1 = [i for i in range(1, 10000)]
    lst2 = [i for i in range(10001, 20000)]
    assert exchange(lst1, lst2) == 'YES'

def test_exchange_with_negative_numbers():
    """Test with negative numbers"""
    assert exchange([-2, -4, -6, -8], [-1, -3, -5, -7]) == 'YES'

def test_exchange_with_positive_and_negative_numbers():
    """Test with positive and negative numbers"""
    assert exchange([-1, -3, -5, -7], [2, 4, 6, 8]) == 'NO'

def test_exchange_with_zero():
    """Test with zero"""
    assert exchange([0, 2, 4, 6], [1, 3, 5, 7]) == 'YES'
