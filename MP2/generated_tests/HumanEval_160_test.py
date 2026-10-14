import pytest
from HumanEval_160 import *
from HumanEval_160 import do_algebra

import pytest
from HumanEval_160 import do_algebra

def test_do_algebra_addition():
    """
    Test the addition operation.
    """
    operator = ['+']
    operand = [2, 3]
    assert do_algebra(operator, operand) == 5

def test_do_algebra_subtraction():
    """
    Test the subtraction operation.
    """
    operator = ['-']
    operand = [5, 3]
    assert do_algebra(operator, operand) == 2

def test_do_algebra_multiplication():
    """
    Test the multiplication operation.
    """
    operator = ['*']
    operand = [2, 3]
    assert do_algebra(operator, operand) == 6

def test_do_algebra_floor_division():
    """
    Test the floor division operation.
    """
    operator = ['//']
    operand = [10, 3]
    assert do_algebra(operator, operand) == 3

def test_do_algebra_exponentiation():
    """
    Test the exponentiation operation.
    """
    operator = ['**']
    operand = [2, 3]
