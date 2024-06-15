import numpy as np
import pytest
from ouroboros.spline import generate_knot_vector

def test_generate_knot_vector_basic():
    # Test with a small number of points and a low degree
    num_points = 5
    degree = 2
    expected_knots = np.array([0, 0, 0, 1, 2, 3, 4, 4, 4])
    assert np.array_equal(generate_knot_vector(num_points, degree), expected_knots)

def test_generate_knot_vector_high_degree():
    # Test with a high degree relative to points
    num_points = 5
    degree = 4
    expected_knots = np.array([0, 0, 0, 0, 0, 1, 2, 3, 4, 4, 4, 4, 4])
    assert np.array_equal(generate_knot_vector(num_points, degree), expected_knots)

def test_generate_knot_vector_single_point():
    # Test with a single point
    num_points = 1
    degree = 0
    expected_knots = np.array([0])
    assert np.array_equal(generate_knot_vector(num_points, degree), expected_knots)

def test_generate_knot_vector_invalid_input():
    # Test with invalid input (negative number of points)
    with pytest.raises(ValueError):
        generate_knot_vector(-1, 2)