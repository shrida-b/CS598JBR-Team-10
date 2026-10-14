import pytest
from HumanEval_91 import *
from HumanEval_91 import is_bored

import pytest
from HumanEval_91 import is_bored

def test_no_boredoms():
    """
    Test the function with a string that does not contain any boredoms.
    """
    assert is_bored('Hello world') == 0

def test_one_boredom():
    """
    Test the function with a string that contains one boredom.
    """
    assert is_bored('The sky is blue. The sun is shining. I love this weather') == 1

def test_multiple_boredoms():
    """
    Test the function with a string that contains multiple boredoms.
    """
    assert is_bored('I am bored. I hate this weather. I want to go home.') == 2

def test_no_sentences():
    """
    Test the function with an empty string.
    """
    assert is_bored('') == 0

def test_no_capital_i():
    """
    Test the function with a sentence that does not start with 'I'.
    """
    assert is_bored('The sky is blue. The sun is shining. love this weather') == 0

def test_no_period():
    """
    Test the function with a sentence that does not end with a period.
    """
    assert is_bored('I am bored. I hate this weather I want to go home') == 2

def test_no_boredoms_with_capital_i():
    """
    Test the function with a string that does not contain any boredoms but starts with 'I'.
    """
    assert is_bored('I am bored. The sun is shining. love this weather') == 1
