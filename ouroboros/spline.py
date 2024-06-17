import numpy as np
from scipy.interpolate import splprep, splev, splder

# https://github.com/scipy/scipy/issues/10389
# https://docs.scipy.org/doc/scipy/reference/interpolate.html

class Spline:
    def __init__(self, sample_points: np.ndarray, degree = 3) -> None:
        # Guarantee that the degree is at least 2
        degree = max(degree, 2)

        self.tck = self.fit_spline(sample_points, degree=degree)

    def __call__(self, times: np.ndarray):
        return self.evaluate_spline(self.tck, times)
    
    def calculate_vectors(self, times: np.ndarray):
        """
        Calculate the tangent, normal, and binormal vectors of the spline at a set of time points.
        
        Parameters:
        ----------
            times (numpy.ndarray): The time points at which to calculate the vectors.

        Returns:
        -------
            tuple: A tuple containing the tangent, normal, and binormal vectors at the given time points. Each has shape (3, n).
        """

        # Handle the case where times is empty
        if len(times) == 0:
            return np.array([]), np.array([]), np.array([])
                    
        # Calculate the first derivative of the spline
        first_derivatives = self.evaluate_spline(self.tck, times, derivative=1)

        # Calculate the second derivative of the spline
        second_derivatives = self.evaluate_spline(self.tck, times, derivative=2)

        # Calculate tangent vectors
        tangent_vectors = first_derivatives / np.linalg.norm(first_derivatives, axis=0)
        
        # Calculate normal vectors
        # https://tex.stackexchange.com/questions/643915/tangent-normal-and-binormal-vectors
        normals = np.cross(first_derivatives, np.cross(second_derivatives, first_derivatives, axis=0), axis=0)
        normal_vectors = normals / np.linalg.norm(normals, axis=0)
        
        # Calculate binormal vectors
        binormal_vectors = np.cross(tangent_vectors, normal_vectors, axis=0)
        # binormal_vectors = binormals / np.linalg.norm(binormals, axis=0)
        
        return tangent_vectors, normal_vectors, binormal_vectors

    @staticmethod
    def fit_spline(sample_points: np.ndarray, degree = 3):
        """
        Fit a B-spline to a set of sample points.
        
        Parameters:
        ----------
            sample_points (numpy.ndarray): A 2D array of shape (n, 3) containing the sample points.
            degree (int): The degree of the B-spline.
        
        Returns:
        -------
            tuple: A tuple containing the knot vector and the coefficients of the B-spline.
        """

        x, y, z = sample_points.T

        # Fit a B-spline to the sample points
        # t = knots, c = coefficients, k = degree
        tck, _ = splprep([x, y, z], k=degree)

        return tck

    @staticmethod
    def evaluate_spline(tck, times: np.ndarray, derivative = 0):
        """
        Evaluate a B-spline at a set of time points.
        
        Parameters:
        ----------
            tck (tuple): A tuple containing the knot vector and the coefficients of the B-spline.
            times (numpy.ndarray): The time points at which to evaluate the B-spline.
            derivative (int): The order of the derivative to evaluate (default is 0).
        
        Returns:
        -------
            numpy.ndarray: The points on the B-spline at the given time points (3, n).
        """

        return np.array(splev(times, tck, der = derivative))

    @staticmethod
    def generate_knot_vector(num_points: int, degree: int):
        """
        Generate a knot vector for a B-spline given the number of points and the degree.
        
        Parameters:
        ----------
            num_points (int): The number of points to fit the spline to.
            degree (int): The degree of the B-spline.

        Returns:
        -------
            numpy.ndarray: The knot vector for the B-spline.
        """

        # Throw error if number of points is negative
        if num_points < 0:
            raise ValueError("Number of points must be non-negative")
        
        if num_points == 1:
            return np.array([0])

        # Start with degree + 1 zeros
        knots = [0] * (degree + 1)

        # Internal knots
        for i in range(1, num_points - 1):
            knots.append(i)

        # End with degree + 1 ones (scaled to the range of internal knots)
        knots += [num_points - 1] * (degree + 1)
        
        return np.array(knots)