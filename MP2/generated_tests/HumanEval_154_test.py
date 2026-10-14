import pytest
from HumanEval_154 import *
from HumanEval_154 import cycpattern_check

import pytest
from HumanEval_154 import cycpattern_check

def test_cycpattern_check_1():
    assert cycpattern_check('abcd', 'abd') == False

def test_cycpattern_check_2():
    assert cycpattern_check('hello', 'ell') == True

def test_cycpattern_check_3():
    assert cycpattern_check('whassup', 'psus') == False

def test_cycpattern_check_4():
    assert cycpattern_check('abab', 'baa') == True

def test_cycpattern_check_5():
    assert cycpattern_check('efef', 'eeff') == False

def test_cycpattern_check_6():
    assert cycpattern_check('himenss', 'simen') == True

def test_cycpattern_check_7():
    assert cycpattern_check('a', 'a') == True

def test_cycpattern_check_8():
    assert cycpattern_check('aa', 'aa') == True

def test_cycpattern_check_9():
    assert cycpattern_check('ab', 'ab') == True

def test_cycpattern_check_10():
    assert cycpattern_check('abc', 'abc') == True

def test_cycpattern_check_11():
    assert cycpattern_check('abcd', 'abcd') == True

def test_cycpattern_check_12():
    assert cycpattern_check('a', '') == False

def test_cycpattern_check_13():
    assert cycpattern_check('', 'a') == False

def test_cycpattern_check_14():
    assert cycpattern_check('', '') == False

def test_cycpattern_check_15():
    assert cycpattern_check('abc', 'adc') == False

def test_cycpattern_check_16():
    assert cycpattern_check('abcd', 'ae') == False

def test_cycpattern_check_17():
    assert cycpattern_check('abc', 'ae') == False

def test_cycpattern_check_18():
    assert cycpattern_check('a' * 1000000, 'a' * 500000 + 'a' * 500000) == True

def test_cycpattern_check_19():
    assert cycpattern_check('a' * 1000000, 'a' * 1000000) == True
