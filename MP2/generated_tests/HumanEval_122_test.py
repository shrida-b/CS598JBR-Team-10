import pytest
from HumanEval_122 import *
from HumanEval_122 import add_elements

import pytest
from HumanEval_122 import add_elements

def test_add_elements_1():
    assert add_elements([111, 21, 3, 4000, 5, 6, 7, 8, 9], 4) == 24

def test_add_elements_2():
    assert add_elements([1, 2, 3, 4, 5, 6, 7, 8, 9], 5) == 15

def test_add_elements_3():
    assert add_elements([10, 20, 30, 40, 50, 60, 70, 80, 90], 8) == 280

def test_add_elements_4():
    assert add_elements([100, 2, 3, 4, 5, 6, 7, 8, 9], 1) == 100

def test_add_elements_5():
    assert add_elements([1, 2, 3, 4, 5, 6, 7, 8, 9], 9) == 45

def test_add_elements_6():
    assert add_elements([1, 2, 3, 4, 5, 6, 7, 8, 9], 10) == 45

def test_add_elements_7():
    assert add_elements([1, 2, 3, 4, 5, 6, 7, 8, 9], 1) == 1

def test_add_elements_8():
    assert add_elements([111, 21, 3, 4000, 5, 6, 7, 8, 9], 2) == 21

def test_add_elements_9():
    assert add_elements([1, 2, 3, 4, 5, 6, 7, 8, 9], 3) == 6

def test_add_elements_10():
    with pytest.raises(ValueError):
        add_elements([1, 2, 3, 4, 5, 6, 7, 8, 9], 0)

def test_add_elements_11():
    with pytest.raises(ValueError):
        add_elements([1, 2, 3, 4, 5, 6, 7, 8, 9], 101)

def test_add_elements_12():
    arr = [i for i in range(1, 101)]
    assert add_elements(arr, 100) == 5050
