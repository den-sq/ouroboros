import numpy as np

from .spline import Spline

def calculate_slice_rects(times: np.ndarray, spline: Spline, width, height, spline_points=None) -> np.ndarray:
    # Calculate the tangent, normal, and binormal vectors
    tangent_vectors, normal_vectors, binormal_vectors = spline.calculate_vectors(times)

    # Transpose the vectors for vectpr-by-vector indexing (3, n) -> (n, 3)
    tangent_vectors = tangent_vectors.T
    normal_vectors = normal_vectors.T
    binormal_vectors = binormal_vectors.T

    if spline_points is None:
        spline_points = spline(times)

    # (3, n) -> (n, 3)
    spline_points = spline_points.T

    rects = []

    for i, time in enumerate(times):
        point = spline_points[i]

        localx = normal_vectors[i]
        localy = binormal_vectors[i]

        width_vec = localx * width
        height_vec = localy * height

        top_left = point - width_vec + height_vec
        top_right = point + width_vec + height_vec
        bottom_right = point + width_vec - height_vec
        bottom_left = point - width_vec - height_vec

        rects.append(np.array([top_left, top_right, bottom_right, bottom_left]))

    # Output the rects in the form (n, 4)
    return np.array(rects)

