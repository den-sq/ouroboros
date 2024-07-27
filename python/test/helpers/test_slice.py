import numpy as np
import pytest
from ouroboros.helpers.bounding_boxes import BoundingBox
from ouroboros.helpers.slice import (
    calculate_slice_rects,
    generate_coordinate_grid_for_rect,
    make_volume_binary,
    slice_volume_from_grids,
    write_slices_to_volume,
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


def test_slice_volume_from_grids_single_channel():
    volume = np.random.rand(10, 10, 10).astype(np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 10, 0, 10, 0, 10))
    grids = np.random.rand(5, 10, 10, 3).astype(np.float32)
    width, height = 10, 10

    result = slice_volume_from_grids(volume, bounding_box, grids, width, height)

    assert result.shape == (5, height, width)
    assert result.dtype == np.float32


def test_slice_volume_from_grids_multi_channel():
    volume = np.random.rand(10, 10, 10, 3).astype(np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 10, 0, 10, 0, 10))
    grids = np.random.rand(5, 10, 10, 3).astype(np.float32)
    width, height = 10, 10

    result = slice_volume_from_grids(volume, bounding_box, grids, width, height)

    assert result.shape == (5, height, width, 3)
    assert result.dtype == np.float32


def test_slice_volume_from_grids_empty_grids():
    volume = np.random.rand(10, 10, 10).astype(np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 10, 0, 10, 0, 10))
    grids = np.empty((0, 10, 10, 3)).astype(np.float32)
    width, height = 10, 10

    result = slice_volume_from_grids(volume, bounding_box, grids, width, height)

    assert result.shape == (0, height, width)
    assert result.dtype == np.float32


def test_slice_volume_from_grids_invalid_dimensions():
    volume = np.random.rand(10, 10, 10).astype(np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 10, 0, 10, 0, 10))
    grids = np.random.rand(5, 10, 10, 2).astype(np.float32)  # Invalid grid dimensions
    width, height = 10, 10

    with pytest.raises(ValueError):
        slice_volume_from_grids(volume, bounding_box, grids, width, height)


def test_write_slices_to_volume_basic():
    volume = np.zeros((10, 10, 10), dtype=np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 10, 0, 10, 0, 10))
    grids = np.random.rand(5, 10, 10, 3).astype(np.float32)
    slices = np.random.rand(5, 10, 10).astype(np.float32)

    write_slices_to_volume(volume, bounding_box, grids, slices)

    assert volume.shape == (10, 10, 10)
    assert volume.dtype == np.float32
    assert np.any(volume > 0)


def test_write_slices_to_volume_empty_slices():
    volume = np.zeros((10, 10, 10), dtype=np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 10, 0, 10, 0, 10))
    grids = np.random.rand(0, 10, 10, 3).astype(np.float32)
    slices = np.random.rand(0, 10, 10).astype(np.float32)

    write_slices_to_volume(volume, bounding_box, grids, slices)

    assert volume.shape == (10, 10, 10)
    assert volume.dtype == np.float32
    assert np.all(volume == 0)


def test_write_slices_to_volume_partial_overlap():
    volume = np.zeros((10, 10, 10), dtype=np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 10, 0, 10, 0, 10))
    grids = np.random.rand(5, 10, 10, 3).astype(np.float32)
    slices = np.random.rand(5, 10, 10).astype(np.float32)

    # Modify grids to partially overlap the volume
    grids[:, :, :, 0] += 5

    write_slices_to_volume(volume, bounding_box, grids, slices)

    assert volume.shape == (10, 10, 10)
    assert volume.dtype == np.float32
    assert np.any(volume > 0)


def test_write_slices_to_volume_invalid_dimensions():
    volume = np.zeros((10, 10, 10), dtype=np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 10, 0, 10, 0, 10))
    grids = np.random.rand(5, 10, 10, 3).astype(np.float32)
    slices = np.random.rand(5, 8, 8).astype(np.float32)  # Invalid dimensions

    with pytest.raises(ValueError):
        write_slices_to_volume(volume, bounding_box, grids, slices)


def test_write_slices_to_volume_large_volume():
    volume = np.zeros((100, 100, 100), dtype=np.float32)
    bounding_box = BoundingBox(BoundingBox.bounds_to_rect(0, 100, 0, 100, 0, 100))
    grids = np.random.rand(50, 100, 100, 3).astype(np.float32)
    slices = np.random.rand(50, 100, 100).astype(np.float32)

    write_slices_to_volume(volume, bounding_box, grids, slices)

    assert volume.shape == (100, 100, 100)
    assert volume.dtype == np.float32
    assert np.any(volume > 0)


def test_make_volume_binary():
    volume = np.array(
        [
            [[0.1, 0.5, 0.9], [0.2, 0.6, 0.8], [0.3, 0.7, 0.4]],
            [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            [[0.9, 0.8, 0.7], [0.6, 0.5, 0.4], [0.3, 0.2, 0.1]],
        ],
        dtype=np.float32,
    )

    binary_volume = make_volume_binary(volume)

    expected_binary_volume = np.array(
        [
            [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
            [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
        ],
        dtype=np.uint8,
    )

    assert binary_volume.shape == volume.shape
    assert binary_volume.dtype == np.uint8
    assert np.array_equal(binary_volume, expected_binary_volume)
