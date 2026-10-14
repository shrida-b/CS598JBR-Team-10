import pytest
from HumanEval_149 import *
from HumanEval_149 import sorted_list_sum

import pytest
from HumanEval_149 import sorted_list_sum

def test_empty_list():
    """Test with an empty list"""
    assert sorted_list_sum([]) == []

def test_single_element_list():
    """Test with a list containing a single element"""
    assert sorted_list_sum(['aa']) == ['aa']

def test_multiple_elements_list():
    """Test with a list containing multiple elements"""
    assert sorted_list_sum(['ab', 'a', 'aaa', 'cd']) == ['ab', 'cd']

def test_duplicate_elements_list():
    """Test with a list containing duplicate elements"""
    assert sorted_list_sum(['aa', 'aa', 'aaa', 'aa']) == ['aa', 'aaa']

def test_uneven_length_elements_list():
    """Test with a list containing elements with uneven length"""
    assert sorted_list_sum(['aa', 'a', 'aaa']) == ['aa']

def test_mixed_length_elements_list():
    """Test with a list containing elements with mixed length"""
    assert sorted_list_sum(['ab', 'a', 'aaa', 'cd', 'abc', 'b']) == ['ab', 'cd', 'b', 'abc']

def test_sort_by_length_and_alphabetically():
    """Test with a list containing elements with same length"""
    assert sorted_list_sum(['ab', 'cd', 'ef', 'gh']) == ['ab', 'cd', 'ef', 'gh']
