import pytest
from HumanEval_16 import *
from HumanEval_16 import count_distinct_characters

import pytest
from HumanEval_16 import count_distinct_characters

def test_count_distinct_characters_1():
    assert count_distinct_characters('xyzXYZ') == 3

def test_count_distinct_characters_2():
    assert count_distinct_characters('Jerry') == 4

def test_count_distinct_characters_3():
    assert count_distinct_characters('') == 0

def test_count_distinct_characters_4():
    assert count_distinct_characters('aabbcc') == 1

def test_count_distinct_characters_5():
    assert count_distinct_characters('1234567890') == 10

def test_count_distinct_characters_6():
    assert count_distinct_characters('aaaaaaaaaa') == 1

def test_count_distinct_characters_7():
    assert count_distinct_characters('A' * 100000) == 1

def test_count_distinct_characters_8():
    assert count_distinct_characters('a' * 100000) == 1

def test_count_distinct_characters_9():
    assert count_distinct_characters('1234567890' * 10000) == 10

def test_count_distinct_characters_10():
    assert count_distinct_characters('abcdefghijklmnopqrstuvwxyz' * 10000) == 26

def test_count_distinct_characters_11():
    with pytest.raises(TypeError):
        count_distinct_characters(12345)

def test_count_distinct_characters_12():
    with pytest.raises(TypeError):
        count_distinct_characters(None)
