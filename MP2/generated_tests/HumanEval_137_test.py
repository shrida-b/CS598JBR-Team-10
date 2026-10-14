import pytest
from HumanEval_137 import *
from HumanEval_137 import compare_one

import pytest
from HumanEval_137 import compare_one

def test_compare_one_1():
    assert compare_one(1, 2) == 2

def test_compare_one_2():
    assert compare_one(3, 2) == 3

def test_compare_one_3():
    assert compare_one(1, 1) == None

def test_compare_one_4():
    assert compare_one(1.1, 2.2) == 2.2

def test_compare_one_5():
    assert compare_one(3.3, 2.2) == 3.3

def test_compare_one_6():
    assert compare_one(1.1, 1.1) == None

def test_compare_one_7():
    assert compare_one('2', '3') == '3'

def test_compare_one_8():
    assert compare_one('3', '2') == '3'

def test_compare_one_9():
    assert compare_one('2', '2') == None

def test_compare_one_10():
    assert compare_one('2.2', '3.3') == '3.3'

def test_compare_one_11():
    assert compare_one('3.3', '2.2') == '3.3'

def test_compare_one_12():
    assert compare_one('2.2', '2.2') == None

def test_compare_one_13():
    assert compare_one('2,2', '3,3') == '3,3'

def test_compare_one_14():
    assert compare_one('3,3', '2,2') == '3,3'

def test_compare_one_15():
    assert compare_one('2,2', '2,2') == None

def test_compare_one_16():
    assert compare_one(1, '2.2') == '2.2'

def test_compare_one_17():
    assert compare_one('3.3', 2) == 3.3

def test_compare_one_18():
    assert compare_one('2,2', 2) == '2,2'

def test_compare_one_19():
    assert compare_one(2, '2,2') == '2,2'
