import pytest
from HumanEval_136 import *
from HumanEval_136 import largest_smallest_integers

import pytest
from HumanEval_136 import largest_smallest_integers

def test_empty_list():
    assert largest_smallest_integers([]) == (None, None)

def test_single_zero():
    assert largest_smallest_integers([0]) == (None, None)

def test_positive_integers():
    assert largest_smallest_integers([1, 2, 3, 4, 5]) == (None, 1)

def test_negative_integers():
    assert largest_smallest_integers([-1, -2, -3, -4, -5]) == (-1, None)

def test_mixed_positive_and_negative_integers():
    assert largest_smallest_integers([1, -2, 3, -4, 5]) == (-2, 1)

def test_large_input():
    lst = list(range(-10000, 10000))
    assert largest_smallest_integers(lst) == (-9999, 1)

def test_large_negative_input():
    lst = list(range(-10000, 0))
    assert largest_smallest_integers(lst) == (-1, None)

def test_large_positive_input():
    lst = list(range(1, 10000))
    assert largest_smallest_integers(lst) == (None, 1)

def test_large_mixed_input():
    lst = list(range(-10000, 10000))
    assert largest_smallest_integers(lst) == (-9999, 1)
