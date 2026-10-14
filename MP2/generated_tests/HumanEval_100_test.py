import pytest
from HumanEval_100 import *
from HumanEval_100 import make_a_pile

import pytest
from HumanEval_100 import make_a_pile

def test_make_a_pile_positive_integer_1():
    """
    Testing with positive integer
    """
    assert make_a_pile(5) == [5, 7, 9, 11, 13]

def test_make_a_pile_positive_integer_2():
    """
    Testing with positive integer
    """
    assert make_a_pile(1) == [1]

def test_make_a_pile_positive_integer_3():
    """
    Testing with positive integer
    """
    assert make_a_pile(10) == [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]

def test_make_a_pile_zero():
    """
    Testing with zero
    """
    assert make_a_pile(0) == []

def test_make_a_pile_negative():
    """
    Testing with negative integer
    """
    with pytest.raises(ValueError):
        make_a_pile(-5)

def test_make_a_pile_non_integer():
    """
    Testing with non-integer
    """
    with pytest.raises(TypeError):
        make_a_pile('5')

def test_make_a_pile_large_integer_1():
    """
    Testing with large integer
    """
    result = make_a_pile(10000)
    assert len(result) == 10000

def test_make_a_pile_large_integer_2():
    """
    Testing with large integer
    """
    result = make_a_pile(10000)
    assert result[-1] == 20000
