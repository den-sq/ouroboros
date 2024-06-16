import numpy as np
import pytest
from ouroboros.spline import Spline

def test_generate_knot_vector_basic():
    # Test with a small number of points and a low degree
    num_points = 5
    degree = 2
    expected_knots = np.array([0, 0, 0, 1, 2, 3, 4, 4, 4])
    assert np.array_equal(Spline.generate_knot_vector(num_points, degree), expected_knots)

def test_generate_knot_vector_high_degree():
    # Test with a high degree relative to points
    num_points = 5
    degree = 4
    expected_knots = np.array([0, 0, 0, 0, 0, 1, 2, 3, 4, 4, 4, 4, 4])
    assert np.array_equal(Spline.generate_knot_vector(num_points, degree), expected_knots)

def test_generate_knot_vector_single_point():
    # Test with a single point
    num_points = 1
    degree = 0
    expected_knots = np.array([0])
    assert np.array_equal(Spline.generate_knot_vector(num_points, degree), expected_knots)

def test_generate_knot_vector_invalid_input():
    # Test with invalid input (negative number of points)
    with pytest.raises(ValueError):
        Spline.generate_knot_vector(-1, 2)

def test_fit_spline():
    import numpy as np

    # Sample points (x, y, z)
    sample_points = np.array([
        [0, 0, 0],
        [1, 1, 1],
        [2, 0, 2],
        [3, -1, 3],
        [4, 0, 4]
    ])

    # Fit the spline
    tck = Spline.fit_spline(sample_points, degree=3)

    # Check if the tck object is not None and has the expected structure
    assert tck is not None, "The tck object should not be None"
    assert len(tck) == 3, "The tck object should have three components"
    print(type(tck[0]))
    print(type(tck[1]))
    assert isinstance(tck[0], np.ndarray), "The first component of tck should be a numpy array"
    assert isinstance(tck[1], list), "The second component of tck should be an array"
    assert isinstance(tck[2], int), "The third component of tck should be an integer"

def test_evaluate_spline():
    import numpy as np

    # Sample points for fitting the spline
    sample_points = np.array([
        [0, 0, 0],
        [1, 1, 1],
        [2, 0, 2],
        [3, -1, 3],
        [4, 0, 4]
    ])

    # Fit the spline
    tck = Spline.fit_spline(sample_points, degree=3)

    # Generate a range of t values
    t_values = np.linspace(0, 1, 100)

    # Evaluate the spline
    evaluated_points = Spline.evaluate_spline(tck, t_values)

    # Check if the evaluated points array has the correct shape
    assert evaluated_points.shape == (100, 3), "The shape of evaluated points should match the number of t values and dimensions"