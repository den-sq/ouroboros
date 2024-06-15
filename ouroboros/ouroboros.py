import numpy as np
from scipy.interpolate import splprep, splev

from .parse import parse_neuroglancer_json, neuroglancer_config_to_annotation
from .spline import generate_knot_vector

def spline_demo():
    try:
        with open("test/sample-data.json") as f:
            ng_config, error = parse_neuroglancer_json(f.read())

            if error:
                print("Error occurred while parsing the file:", str(error))
                return
    except Exception as e:
        print("Error occurred while opening the file:", str(e))
        return
    
    sample_points = neuroglancer_config_to_annotation(ng_config)

    if sample_points.size == 0:
        print("No annotations found in the file.")
        return
    
    # Fit a spline to the sample points
    degree = 3
    
    # Create a knot vector with degree + 1 knots at the start and end
    knots = generate_knot_vector(sample_points.shape[0], degree)

    x, y, z = sample_points.T

    # Fit a B-spline to the sample points
    # t = knots, c = coefficients, k = degree
    tck, u = splprep([x, y, z], u=knots, k=degree)
    x_knots, y_knots, z_knots = splev(tck[0], tck)

    # t_values = np.linspace(knots[degree], knots[-degree-1], 100)

    # Evaluate the spline at 100 points
    # spline_points = bspline(t_values)

    # Plot the sample points and the spline
    import matplotlib.pyplot as plt

    fig2 = plt.figure(2)
    ax3d = fig2.add_subplot(111, projection='3d')
    ax3d.plot(x, y, z, 'r*')
    ax3d.plot(x_knots, y_knots, z_knots, 'go')
    fig2.show()
    plt.show()

    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')

    # # Plot the B-spline curve
    # ax.plot(spline_points[:, 0], spline_points[:, 1], spline_points[:, 2], 'b-', label='B-spline curve')

    # # Plot the control points
    # ax.plot(sample_points[:, 0], sample_points[:, 1], sample_points[:, 2], 'ro-', label='Sample points')

    # ax.legend()
    # plt.show()
