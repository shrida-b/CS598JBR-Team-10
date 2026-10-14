import pytest
from HumanEval_67 import *
from HumanEval_67 import fruit_distribution

import pytest
from HumanEval_67 import fruit_distribution

def test_fruit_distribution_1():
    assert fruit_distribution('5 apples and 6 oranges', 19) == 8

def test_fruit_distribution_2():
    assert fruit_distribution('0 apples and 1 oranges', 3) == 2

def test_fruit_distribution_3():
    assert fruit_distribution('2 apples and 3 oranges', 100) == 95

def test_fruit_distribution_4():
    assert fruit_distribution('100 apples and 1 oranges', 120) == 19

def test_fruit_distribution_5():
    assert fruit_distribution('0 apples and 0 oranges', 0) == 0

def test_fruit_distribution_6():
    assert fruit_distribution('0 apples and 0 oranges', 10) == 10
