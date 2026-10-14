import pytest
from HumanEval_124 import *
from HumanEval_124 import valid_date

import pytest
from HumanEval_124 import valid_date

def test_valid_date_1():
    """Test valid dates"""
    assert valid_date('01-01-2000') == True

def test_valid_date_2():
    """Test valid dates"""
    assert valid_date('12-31-2020') == True

def test_valid_date_3():
    """Test valid dates"""
    assert valid_date('02-29-2020') == True

def test_invalid_date_1():
    """Test invalid dates"""
    assert valid_date('03-11-2000') == False

def test_invalid_date_2():
    """Test invalid dates"""
    assert valid_date('15-01-2012') == False

def test_invalid_date_3():
    """Test invalid dates"""
    assert valid_date('04-0-2040') == False

def test_invalid_date_4():
    """Test invalid dates"""
    assert valid_date('06-04-2020') == False

def test_invalid_format():
    """Test dates in invalid format"""
    assert valid_date('06/04/2020') == False

def test_invalid_month_1():
    """Test invalid month"""
    assert valid_date('13-01-2000') == False

def test_invalid_month_2():
    """Test invalid month"""
    assert valid_date('00-01-2000') == False

def test_invalid_day_1():
    """Test invalid day"""
    assert valid_date('01-32-2000') == False

def test_invalid_day_2():
    """Test invalid day"""
    assert valid_date('01-00-2000') == False

def test_leap_year_1():
    """Test leap year"""
    assert valid_date('02-29-2020') == True

def test_leap_year_2():
    """Test leap year"""
    assert valid_date('02-30-2020') == False

def test_empty_string():
    """Test empty string"""
    assert valid_date('') == False
