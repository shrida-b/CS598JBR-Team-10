import pytest
from HumanEval_32 import *
from HumanEval_32 import find_zero

import pytest
from HumanEval_32 import find_zero

def test_poly_edge_cases_1():
    """
    Testing edge cases for poly function.
    """
    assert poly([1, 2, 3], 0) == 1

def test_poly_edge_cases_2():
    """
    Testing edge cases for poly function.
    """
    assert poly([0, 0, 0], 1) == 0

def test_poly_edge_cases_3():
    """
    Testing edge cases for poly function.
    """
    assert poly([1, 2, 3, 4, 5], 1) == 6

def test_poly_boundary_conditions_1():
    """
    Testing boundary conditions for poly function.
    """
    assert poly([1, 2, 3], 1) == 4

def test_poly_boundary_conditions_2():
    """
    Testing boundary conditions for poly function.
    """
    assert poly([1, 2, 3, 4, 5], 0) == 1

def test_poly_boundary_conditions_3():
    """
    Testing boundary conditions for poly function.
    """
    assert poly([1, 2, 3, 4, 5], 2) == 11

def test_find_zero_edge_cases_1():
    """
    Testing edge cases for find_zero function.
    """
    assert round(find_zero([1, 2]), 2) == -0.5

def test_find_zero_edge_cases_2():
    """
    Testing edge cases for find_zero function.
    """
    assert round(find_zero([-6, 11, -6, 1]), 2) == 1.0

def test_find_zero_boundary_conditions_1():
    """
    Testing boundary conditions for find_zero function.
    """
    assert round(find_zero([1, 0, -1]), 2) == 0.0

def test_find_zero_boundary_conditions_2():
    """
    Testing boundary conditions for find_zero function.
    """
    assert round(find_zero([1, 0, 0, -1]), 2) == 0.0

def test_find_zero_uncovered_branches_1():
    """
    Testing uncovered branches for find_zero function.
    """
    assert round(find_zero([1, 1, 1]), 2) == -1.0

def test_find_zero_uncovered_branches_2():
    """
    Testing uncovered branches for find_zero function.
    """
    assert round(find_zero([1, 2, 3, 4, 5]), 2) == -0.64

def test_find_zero_invalid_inputs():
    """
    Testing invalid inputs for find_zero function.
    """
    with pytest.raises(ZeroDivisionError):
        find_zero([0, 0, 0])

def test_find_zero_large_inputs():
    """
    Testing large inputs for find_zero function.
    """
    with pytest.raises(RecursionError):
        find_zero([1] * 1000000)
