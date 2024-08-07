import numpy as np

from scipy.ndimage import map_coordinates

from cloudvolume import VolumeCutout
from .bounding_boxes import BoundingBox

from .spline import Spline

INDEXING = "xy"

NO_COLOR_CHANNELS_DIMENSIONS = 3
COLOR_CHANNELS_DIMENSIONS = NO_COLOR_CHANNELS_DIMENSIONS + 1


def calculate_slice_rects(
    times: np.ndarray, spline: Spline, width, height, spline_points=None
) -> np.ndarray:
    """
    Calculate the slice rectangles for a spline at a set of time points.

    Parameters:
    ----------
        times (numpy.ndarray): The time points at which to calculate the slice rectangles.
        spline (Spline): The spline object.
        width (float): The width of the slice rectangles.
        height (float): The height of the slice rectangles.
        spline_points (numpy.ndarray): The points on the spline at the given time points (3, n).

    Returns:
    -------
        numpy.ndarray: The slice rectangles at the given time points (n, 4, 3).
    """

    # Calculate the tangent, normal, and binormal vectors
    tangent_vectors, normal_vectors, binormal_vectors = (
        spline.calculate_rotation_minimizing_vectors(times)
    )

    # Transpose the vectors for vectpr-by-vector indexing (3, n) -> (n, 3)
    tangent_vectors = tangent_vectors.T
    normal_vectors = normal_vectors.T
    binormal_vectors = binormal_vectors.T

    if spline_points is None:
        spline_points = spline(times)

    # (3, n) -> (n, 3)
    spline_points = spline_points.T

    rects = []

    _width, w_remainder = divmod(width, 2)
    _height, h_remainder = divmod(height, 2)

    width_left = _width
    width_right = _width + w_remainder

    height_top = _height
    height_bottom = _height + h_remainder

    for i in range(len(times)):
        point = spline_points[i]

        localx = normal_vectors[i]
        localy = binormal_vectors[i]

        width_left_vec = localx * width_left
        width_right_vec = localx * width_right
        height_top_vec = localy * height_top
        height_bottom_vec = localy * height_bottom

        top_left = point - width_left_vec + height_top_vec
        top_right = point + width_right_vec + height_top_vec
        bottom_right = point + width_right_vec - height_bottom_vec
        bottom_left = point - width_left_vec - height_bottom_vec

        rects.append(np.array([top_left, top_right, bottom_right, bottom_left]))

    # Output the rects in the form (n, 4, 3)
    return np.array(rects)


def generate_coordinate_grid_for_rect(rect: np.ndarray, width, height) -> np.ndarray:
    """
    Generate a coordinate grid for a rectangle.

    Parameters:
    ----------
        rect (numpy.ndarray): The corners of the rectangle as a list of 3D coordinates.
        width (int): The width of the grid.
        height (int): The height of the grid.

    Returns:
    -------
        numpy.ndarray: The grid of coordinates (width, height, 3).
    """

    top_left, top_right, bottom_right, bottom_left = rect

    # Generate a grid of (u, v) coordinates
    u = np.linspace(0, 1, width)
    v = np.linspace(0, 1, height)
    u, v = np.meshgrid(u, v, indexing=INDEXING)  # TODO: need 'ij'?

    # Interpolate the 3D coordinates
    # TODO: There must be a way to do this faster
    points = (
        (1 - u)[:, :, np.newaxis] * (1 - v)[:, :, np.newaxis] * top_left
        + u[:, :, np.newaxis] * (1 - v)[:, :, np.newaxis] * top_right
        + (1 - u)[:, :, np.newaxis] * v[:, :, np.newaxis] * bottom_left
        + u[:, :, np.newaxis] * v[:, :, np.newaxis] * bottom_right
    )

    return points


def slice_volume_from_grids(
    volume: VolumeCutout, bounding_box: BoundingBox, grids: np.ndarray, width, height
) -> np.ndarray:
    """
    Slice a volume based on a grid of coordinates.

    Parameters:
    ----------
        volume (VolumeCutout): The volume of shape (x, y, z, c) to slice.
        bounding_box (BoundingBox): The bounding box of the volume.
        grids (numpy.ndarray): The grids of coordinates to slice the volume (n, width, height, 3).
        width (int): The width of the grid.
        height (int): The height of the grid.

    Returns:
    -------
        numpy.ndarray: The slice of the volume as a 2D array.
    """

    # Normalize grid coordinates based on bounding box (since volume coordinates are truncated)
    bounding_box_min = np.array(
        [bounding_box.x_min, bounding_box.y_min, bounding_box.z_min]
    )

    # Subtract the bounding box min from the grids (n, width, height, 3)
    normalized_grid = grids - bounding_box_min

    # Reshape the grids to be (3, n * width * height)
    normalized_grid = normalized_grid.reshape(-1, 3).T

    # Check if volume has color channels
    has_color_channels, num_channels = detect_color_channels(volume)

    if has_color_channels:
        # Initialize an empty list to store slices from each channel
        channel_slices = []

        # Iterate over each color channel
        for channel in range(num_channels):
            # Extract the current channel
            current_channel = volume[..., channel]

            # Map the grid coordinates to the current channel volume
            slice_points = map_coordinates(current_channel, normalized_grid)

            # Reshape and store the result
            channel_slices.append(slice_points.reshape(len(grids), height, width))

        # Stack the channel slices along the last axis to form the final output
        return np.stack(channel_slices, axis=-1)

    else:
        # If no color channels, process as before
        slice_points = map_coordinates(volume, normalized_grid)
        return slice_points.reshape(len(grids), height, width)


def write_slices_to_volume(
    volume: np.ndarray, bounding_box: BoundingBox, grids: np.ndarray, slices: np.ndarray
):
    """
    Write a slice to volume based on a grid of coordinates.

    Parameters:
    ----------
        volume (numpy.ndarray, dtype=float32): A volume of shape (x, y, z), which should match the dimensions of the given bounding box.
        bounding_box (BoundingBox): The bounding box of the volume.
        grids (numpy.ndarray): The grids of coordinates to slice the volume (n, width, height, 3).
        slices (numpy.ndarray): The slice data to write to the volume (n, width, height).

    Returns:
    -------
        None
    """

    # Create a list of slice values and coordinates
    slice_values = slices.flatten()
    slice_coords = grids.reshape(-1, 3).T

    # Normalize grid coordinates based on bounding box (since volume coordinates are truncated)
    x_min, _, y_min, _, z_min, _ = bounding_box.approx_bounds()
    bounding_box_min = np.array([x_min, y_min, z_min])
    slice_coords -= bounding_box_min[:, np.newaxis]

    # Get the integer and fractional parts of the coordinates
    coords_floor = np.floor(slice_coords).astype(int)
    coords_ceil = np.ceil(slice_coords).astype(int)
    weights = slice_coords - coords_floor

    # Check if volume has color channels
    has_color_channels, num_channels = detect_color_channels(volume)

    for channel in range(num_channels):
        # Initialize the accumulation arrays
        accumulated_volume = volume[:, :, :, channel] if has_color_channels else volume
        weight_volume = np.zeros_like(accumulated_volume)

        # Prepare the indices for the 8 corners surrounding each coordinate
        x0, y0, z0 = coords_floor
        x1, y1, z1 = coords_ceil

        # Calculate the weights for each corner
        wx0, wy0, wz0 = 1 - weights[0], 1 - weights[1], 1 - weights[2]
        wx1, wy1, wz1 = weights[0], weights[1], weights[2]

        c000 = wx0 * wy0 * wz0
        c001 = wx0 * wy0 * wz1
        c010 = wx0 * wy1 * wz0
        c011 = wx0 * wy1 * wz1
        c100 = wx1 * wy0 * wz0
        c101 = wx1 * wy0 * wz1
        c110 = wx1 * wy1 * wz0
        c111 = wx1 * wy1 * wz1

        # Use numpy.add.at to accumulate the values at the correct positions
        np.add.at(accumulated_volume, (x0, y0, z0), slice_values * c000)
        np.add.at(accumulated_volume, (x0, y0, z1), slice_values * c001)
        np.add.at(accumulated_volume, (x0, y1, z0), slice_values * c010)
        np.add.at(accumulated_volume, (x0, y1, z1), slice_values * c011)
        np.add.at(accumulated_volume, (x1, y0, z0), slice_values * c100)
        np.add.at(accumulated_volume, (x1, y0, z1), slice_values * c101)
        np.add.at(accumulated_volume, (x1, y1, z0), slice_values * c110)
        np.add.at(accumulated_volume, (x1, y1, z1), slice_values * c111)

        # Accumulate the weights similarly
        np.add.at(weight_volume, (x0, y0, z0), c000)
        np.add.at(weight_volume, (x0, y0, z1), c001)
        np.add.at(weight_volume, (x0, y1, z0), c010)
        np.add.at(weight_volume, (x0, y1, z1), c011)
        np.add.at(weight_volume, (x1, y0, z0), c100)
        np.add.at(weight_volume, (x1, y0, z1), c101)
        np.add.at(weight_volume, (x1, y1, z0), c110)
        np.add.at(weight_volume, (x1, y1, z1), c111)

        # Normalize the accumulated volume by the weights
        nonzero_weights = weight_volume != 0
        accumulated_volume[nonzero_weights] /= weight_volume[nonzero_weights]


def make_volume_binary(volume: np.ndarray, dtype=np.uint8) -> np.ndarray:
    """
    Convert a volume to binary format.

    Note: To view a binary volume, use the threshold feature in ImageJ.

    Parameters:
    ----------
        volume (numpy.ndarray): The volume to convert to binary format.

    Returns:
    -------
        numpy.ndarray: The binary volume.
    """

    return (volume > 0).astype(dtype)


def detect_color_channels(data: np.ndarray, none_value=1):
    """
    Detect the number of color channels in a volume.

    Parameters:
    ----------
        data (numpy.ndarray): The volume data.
        none_value (int): The value to return if the volume has no color channels.

    Returns:
    -------
        tuple: A tuple containing the following:
            - has_color_channels (bool): Whether the volume has color channels.
            - num_color_channels (int): The number of color channels in the volume.
    """

    has_color_channels, num_color_channels = detect_color_channels_shape(
        data.shape, none_value
    )

    return has_color_channels, num_color_channels


def detect_color_channels_shape(shape: tuple, none_value=1):
    """
    Detect the number of color channels in a volume.

    Parameters:
    ----------
        shape (tuple): The shape of the volume data.
        none_value (int): The value to return if the volume has no color channels.

    Returns:
    -------
        tuple: A tuple containing the following:
            - has_color_channels (bool): Whether the volume has color channels.
            - num_color_channels (int): The number of color channels in the volume.
    """

    has_color_channels = len(shape) == COLOR_CHANNELS_DIMENSIONS
    num_color_channels = shape[-1] if has_color_channels else none_value

    return has_color_channels, num_color_channels
