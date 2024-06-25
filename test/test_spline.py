import numpy as np
import pytest
from ouroboros.helpers.spline import Spline

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
    assert evaluated_points.shape == (3, 100), "The shape of evaluated points should match the number of t values and dimensions"


def test_calculate_vectors_basic():
    # Sample points arranged in a simple curve
    sample_points = np.array([
        [0, 0, 0],
        [1, 1, 0],
        [2, 0, 0]
    ])
    # Initialize Spline object
    spline = Spline(sample_points, degree=2)
    # Times at which to calculate vectors
    times = np.linspace(0, 1, 5)
    # Calculate vectors
    tangent_vectors, normal_vectors, binormal_vectors = spline.calculate_vectors(times)
    # Assert that the method returns three numpy arrays
    assert isinstance(tangent_vectors, np.ndarray), "Tangent vectors should be a numpy array"
    assert isinstance(normal_vectors, np.ndarray), "Normal vectors should be a numpy array"
    assert isinstance(binormal_vectors, np.ndarray), "Binormal vectors should be a numpy array"
    # Assert that the shapes of the vectors are correct
    assert tangent_vectors.shape == (3, len(times)), "Tangent vectors shape should match (3, number of times)"
    assert normal_vectors.shape == (3, len(times)), "Normal vectors shape should match (3, number of times)"
    assert binormal_vectors.shape == (3, len(times)), "Binormal vectors shape should match (3, number of times)"

def test_vectors_orthogonality():
    # Define a simple curve as sample points
    sample_points = np.array([
        [1, 0, 0],
        [1, 2, 1],
        [2, 1, 2],
        [3, -2, 4],
        [4, 7, 4]
    ])

    # Initialize Spline object
    spline = Spline(sample_points, degree=3)

    times = np.linspace(0, 1, 5)

    # Calculate vectors
    tangent_vectors, normal_vectors, binormal_vectors = spline.calculate_vectors(times)

    # Transpose the vectors for vector-by-vector indexing (3, n) -> (n, 3)
    tangent_vectors = tangent_vectors.T
    normal_vectors = normal_vectors.T
    binormal_vectors = binormal_vectors.T
    
    # Check orthogonality between each pair of vectors
    for i in range(tangent_vectors.shape[0]):
        tangent_normal_dot = np.dot(tangent_vectors[i], normal_vectors[i])
        tangent_binormal_dot = np.dot(tangent_vectors[i], binormal_vectors[i])
        normal_binormal_dot = np.dot(normal_vectors[i], binormal_vectors[i])
        
        assert np.allclose(tangent_normal_dot, 0, atol=1e-6), "Tangent and normal vectors should be orthogonal"
        assert np.allclose(tangent_binormal_dot, 0, atol=1e-6), "Tangent and binormal vectors should be orthogonal"
        assert np.allclose(normal_binormal_dot, 0, atol=1e-6), "Normal and binormal vectors should be orthogonal"

# def test_calculate_equidistant_parameters():
#     # Define a simple curve as sample points
#     sample_points = np.array([
#         [0, 0, 0],
#         [1, 2, 1],
#         [2, 0, 2],
#         [3, -2, 3],
#         [4, 0, 4]
#     ])
#     # Initialize Spline object
#     spline = Spline(sample_points, degree=3)
#     # Specify the distance between points
#     distance_between_points = 0.1
#     # Calculate equidistant parameters
#     equidistant_params = spline.calculate_equidistant_parameters(distance_between_points)
#     # Evaluate the spline at these parameters
#     evaluated_points = spline(equidistant_params)
#     # Calculate distances between consecutive points
#     distances = np.sqrt(np.sum(np.diff(evaluated_points, axis=1)**2, axis=0))

#     print(distances, distance_between_points)

#     # Assert that distances are close to the specified distance
#     assert np.allclose(distances, distance_between_points, atol=0.1), "Distances between points should be close to the specified distance"