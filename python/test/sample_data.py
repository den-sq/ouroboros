import numpy as np


def generate_sample_curve_helix(start_z=-10, end_z=10, num_points=100) -> np.ndarray:
    """
    Generates a sample helix curve for testing purposes.

    Parameters
    ----------
    start_z : float
        The starting z value.
    end_z : float
        The ending z value.
    num_points : int
        The number of points to generate.

    Returns
    -------
    np.ndarray
        The sample helix curve (num_points, 3).
    """
    t = np.linspace(start_z, end_z, num_points)
    x = np.cos(t)
    y = np.sin(t)
    z = t

    return np.vstack((x, y, z)).T
