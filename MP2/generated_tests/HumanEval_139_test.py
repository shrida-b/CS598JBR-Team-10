import pytest
from HumanEval_139 import *
from HumanEval_139 import special_factorial

import pytest
from HumanEval_139 import special_factorial

def test_special_factorial_zero():
    """Testing the special_factorial function with 0"""
    with pytest.raises(ValueError):
        special_factorial(0)

def test_special_factorial_negative():
    """Testing the special_factorial function with negative number"""
    with pytest.raises(ValueError):
        special_factorial(-1)

def test_special_factorial_positive_1():
    """Testing the special_factorial function with positive number"""
    assert special_factorial(5) == 5 * 4 * 3 * 2 * 1

def test_special_factorial_positive_2():
    """Testing the special_factorial function with positive number"""
    assert special_factorial(1) == 1

def test_special_factorial_positive_3():
    """Testing the special_factorial function with positive number"""
    assert special_factorial(10) == 3628800

def test_special_factorial_large():
    """Testing the special_factorial function with large number"""
    assert special_factorial(15) == 1307674368000
