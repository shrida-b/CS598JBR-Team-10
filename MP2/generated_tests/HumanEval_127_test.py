import pytest
from HumanEval_127 import *
from HumanEval_127 import intersection

import pytest
from HumanEval_127 import intersection

def test_intersection_no_intersection_1():
    """
    Test when there is no intersection between the two intervals.
    """
    assert intersection((1, 2), (3, 4)) == 'NO'

def test_intersection_no_intersection_2():
    """
    Test when there is no intersection between the two intervals.
    """
    assert intersection((-1, 1), (2, 4)) == 'NO'

def test_intersection_no_intersection_3():
    """
    Test when there is no intersection between the two intervals.
    """
    assert intersection((-3, -1), (-2, -5)) == 'NO'

def test_intersection_intersect_at_one_point_1():
    """
    Test when the two intervals intersect at one point.
    """
    assert intersection((1, 1), (1, 2)) == 'NO'

def test_intersection_intersect_at_one_point_2():
    """
    Test when the two intervals intersect at one point.
    """
    assert intersection((-1, -1), (-5, -5)) == 'NO'

def test_intersection_intersect_at_one_point_3():
    """
    Test when the two intervals intersect at one point.
    """
    assert intersection((3, 3), (3, 5)) == 'NO'

def test_intersection_intersect_at_two_points_1():
    """
    Test when the two intervals intersect at two points.
    """
    assert intersection((1, 2), (1, 3)) == 'NO'

def test_intersection_intersect_at_two_points_2():
    """
    Test when the two intervals intersect at two points.
    """
    assert intersection((-1, 1), (-5, 1)) == 'NO'

def test_intersection_intersect_at_two_points_3():
    """
    Test when the two intervals intersect at two points.
    """
    assert intersection((3, 5), (3, 7)) == 'NO'

def test_intersection_intersect_at_three_points_1():
    """
    Test when the two intervals intersect at three points.
    """
    assert intersection((1, 3), (1, 3)) == 'YES'

def test_intersection_intersect_at_three_points_2():
    """
    Test when the two intervals intersect at three points.
    """
    assert intersection((-1, 1), (-1, 1)) == 'YES'

def test_intersection_intersect_at_three_points_3():
    """
    Test when the two intervals intersect at three points.
    """
    assert intersection((3, 5), (3, 5)) == 'YES'

def test_intersection_intersect_at_four_points_1():
    """
    Test when the two intervals intersect at four points.
    """
    assert intersection((1, 4), (1, 4)) == 'YES'

def test_intersection_intersect_at_four_points_2():
    """
    Test when the two intervals intersect at four points.
    """
    assert intersection((-1, 4), (-1, 4)) == 'YES'

def test_intersection_intersect_at_four_points_3():
    """
    Test when the two intervals intersect at four points.
    """
    assert intersection((3, 6), (3, 6)) == 'YES'

def test_intersection_intersect_at_five_points_1():
    """
    Test when the two intervals intersect at five points.
    """
    assert intersection((1, 5), (1, 5)) == 'YES'

def test_intersection_intersect_at_five_points_2():
    """
    Test when the two intervals intersect at five points.
    """
    assert intersection((-1, 5), (-1, 5)) == 'YES'

def test_intersection_intersect_at_five_points_3():
    """
    Test when the two intervals intersect at five points.
    """
    assert intersection((3, 7), (3, 7)) == 'YES'

def test_intersection_intersect_at_six_points_1():
    """
    Test when the two intervals intersect at six points.
    """
    assert intersection((1, 6), (1, 6)) == 'YES'

def test_intersection_intersect_at_six_points_2():
    """
    Test when the two intervals intersect at six points.
    """
    assert intersection((-1, 6), (-1, 6)) == 'YES'

def test_intersection_intersect_at_six_points_3():
    """
    Test when the two intervals intersect at six points.
    """
    assert intersection((3, 8), (3, 8)) == 'YES'

def test_intersection_intersect_at_seven_points_1():
    """
    Test when the two intervals intersect at seven points.
    """
    assert intersection((1, 7), (1, 7)) == 'YES'

def test_intersection_intersect_at_seven_points_2():
    """
    Test when the two intervals intersect at seven points.
    """
    assert intersection((-1, 7), (-1, 7)) == 'YES'

def test_intersection_intersect_at_seven_points_3():
    """
    Test when the two intervals intersect at seven points.
    """
    assert intersection((3, 9), (3, 9)) == 'YES'

def test_intersection_intersect_at_eight_points_1():
    """
    Test when the two intervals intersect at eight points.
    """
    assert intersection((1, 8), (1, 8)) == 'YES'

def test_intersection_intersect_at_eight_points_2():
    """
    Test when the two intervals intersect at eight points.
    """
    assert intersection((-1, 8), (-1, 8)) == 'YES'

def test_intersection_intersect_at_eight_points_3():
    """
    Test when the two intervals intersect at eight points.
    """
    assert intersection((3, 10), (3, 10)) == 'YES'

def test_intersection_intersect_at_nine_points_1():
    """
    Test when the two intervals intersect at nine points.
    """
    assert intersection((1, 9), (1, 9)) == 'YES'

def test_intersection_intersect_at_nine_points_2():
    """
    Test when the two intervals intersect at nine points.
    """
    assert intersection((-1, 9), (-1, 9)) == 'YES'

def test_intersection_intersect_at_nine_points_3():
    """
    Test when the two intervals intersect at nine points.
    """
    assert intersection((3, 11), (3, 11)) == 'YES'
