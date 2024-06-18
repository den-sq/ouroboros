import numpy as np
from scipy.interpolate import splprep, splev

# https://github.com/scipy/scipy/issues/10389
# https://docs.scipy.org/doc/scipy/reference/interpolate.html

class Spline:
    def __init__(self, sample_points: np.ndarray, degree = 3) -> None:
        # Guarantee that the degree is at least 2
        degree = max(degree, 2)

        self.tck, self.u = self.fit_spline(sample_points, degree=degree)

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
    
    def calculate_equidistant_parameters(self, distance_between_points: float):
        """
        Calculate the parameter values that correspond to equidistant points along the spline.

        Parameters:
        ----------
            distance_between_points (float): The distance between consecutive points.

        Returns:
        -------
            numpy.ndarray: The parameter values that correspond to equidistant points along the spline.
        """

        # TODO: Add test
            
        # Evaluate the B-spline derivative
        dx, dy, dz = splev(self.u, self.tck, der=1)

        # Compute the cumulative arc length using the derivatives
        dists = np.linalg.norm([dx, dy, dz], axis=0)
        arc_length = np.cumsum(dists * np.diff(self.u, prepend=0))
        total_length = arc_length[-1]

        # Determine the number of points n based on the desired distance d
        n = int(np.floor(total_length / distance_between_points)) + 1

        # Interpolate distances to find equidistant parameters
        desired_arc_lengths = np.linspace(0, arc_length[-1], n)
        equidistant_params = np.interp(desired_arc_lengths, arc_length,self.u)

        return equidistant_params

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
        tck, u = splprep([x, y, z], k=degree)

        return tck, u

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