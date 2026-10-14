import pytest
from HumanEval_74 import *
from HumanEval_74 import total_match

import pytest
from HumanEval_74 import total_match

def test_empty_lists():
    assert total_match([], []) == []

def test_first_list_shorter():
    assert total_match(['hi', 'admin'], ['hI', 'Hi']) == ['hI', 'Hi']

def test_lists_same_length():
    assert total_match(['hi', 'admin'], ['hi', 'hi', 'admin', 'project']) == ['hi', 'admin']

def test_second_list_shorter():
    assert total_match(['hi', 'admin'], ['hI', 'hi', 'hi']) == ['hI', 'hi', 'hi']

def test_single_string_lists():
    assert total_match(['4'], ['1', '2', '3', '4', '5']) == ['4']

def test_large_lists():
    lst1 = ['a' * i for i in range(1, 1000)]
    lst2 = ['b' * i for i in range(1, 1000)]
    assert total_match(lst1, lst2) == lst1
