import pytest
from HumanEval_0 import *
from HumanEval_0 import has_close_elements

import pytest
from HumanEval_0 import has_close_elements

def test_empty_list():
    """
    Test with an empty list
    """
    assert not has_close_elements([], 0.5)

def test_single_element():
    """
    Test with a single element
    """
    assert not has_close_elements([1.0], 0.5)

def test_no_close_elements():
    """
    Test with no close elements
    """
    assert not has_close_elements([1.0, 2.0, 3.0], 0.5)

def test_close_elements():
    """
    Test with close elements
    """
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)

def test_close_elements_at_start():
    """
    Test with close elements at the start
    """
    assert has_close_elements([0.2, 1.0, 2.0, 3.0], 0.5)

def test_close_elements_at_end():
    """
    Test with close elements at the end
    """
    assert has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0], 0.5)

def test_close_elements_in_middle():
    """
    Test with close elements in the middle
    """
    assert has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 0.5)

def test_negative_threshold():
    """
    Test with negative threshold
    """
    assert not has_close_elements([1.0, 2.0, 3.0], -0.5)

def test_zero_threshold():
    """
    Test with zero threshold
    """
    assert not has_close_elements([1.0, 2.0, 3.0], 0)
