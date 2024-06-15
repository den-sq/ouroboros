import numpy as np

def generate_knot_vector(num_points, degree):
    # TODO: More efficient implementation

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