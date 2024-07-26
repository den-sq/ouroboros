import numpy as np
from ouroboros.helpers.slice import (
    calculate_slice_rects,
    generate_coordinate_grid_for_rect,
)
from ouroboros.helpers.spline import Spline
from test.sample_data import generate_sample_curve_helix


def test_calculate_slice_rects():
    # Sample points arranged in a simple curve
    sample_points = generate_sample_curve_helix()

    # Initialize Spline object
    spline = Spline(sample_points, degree=3)

    # Generate a range of t values
    equidistant_times = spline.calculate_equidistant_parameters(
        distance_between_points=1
    )

    WIDTH = 100
    HEIGHT = 100

    # Calculate slice rects
    slice_rects = calculate_slice_rects(equidistant_times, spline, WIDTH, HEIGHT)

    # Assert that the method returns a list of numpy arrays
    assert isinstance(slice_rects, np.ndarray), "Slice rects should be a numpy array"
    for rect in slice_rects:
        assert isinstance(rect, np.ndarray), "Each slice rect should be a numpy array"
        assert rect.shape == (4, 3), "Each slice rect should have shape (4, 3)"

        # Check if the slice rects are valid rectangles
        top_left = rect[0]
        top_right = rect[1]
        bottom_right = rect[2]
        bottom_left = rect[3]

        assert np.allclose(
            top_left + bottom_right, top_right + bottom_left
        ), "The diagonals of the rectangle should intersect at the center"

        # Make sure rectangles have expected width and height
        assert np.allclose(
            np.linalg.norm(top_left - top_right), WIDTH
        ), "Width should be 100"
        assert np.allclose(
            np.linalg.norm(top_left - bottom_left), HEIGHT
        ), "Height should be 100"


def test_generate_coordinate_grid_for_rect():
    rect = np.array([[0, 0, 1], [1, 0, 1], [1, 0, 0], [0, 0, 0]])
    WIDTH = 100
    HEIGHT = 100

    # Generate a coordinate grid for the rectangle
    coordinate_grid = generate_coordinate_grid_for_rect(rect, WIDTH, HEIGHT)

    # Assert that the method returns a numpy array
    assert isinstance(
        coordinate_grid, np.ndarray
    ), "Coordinate grid should be a numpy array"
    assert coordinate_grid.shape == (
        WIDTH,
        HEIGHT,
        3,
    ), "Coordinate grid should have shape (100, 100, 3)"
    assert np.allclose(
        coordinate_grid[0][0], rect[0]
    ), "The first coordinate should be the top left corner of the rectangle"
