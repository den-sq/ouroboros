import numpy as np
from scipy.interpolate import splprep, splev

class Spline:
    def __init__(self, sample_points: np.ndarray, degree = 3) -> None:
        self.tck = self.fit_spline(sample_points, degree=degree)

    def __call__(self, times: np.ndarray):
        return self.evaluate_spline(self.tck, times)

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
    def evaluate_spline(tck, times: np.ndarray):
        """
        Evaluate a B-spline at a set of time points.
        
        Parameters:
        ----------
            tck (tuple): A tuple containing the knot vector and the coefficients of the B-spline.
            times (numpy.ndarray): The time points at which to evaluate the B-spline.
        
        Returns:
        -------
            numpy.ndarray: The points on the B-spline at the given time points (n, 3).
        """

        return np.array(splev(times, tck)).T

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