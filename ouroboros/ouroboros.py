import numpy as np

from .parse import parse_neuroglancer_json, neuroglancer_config_to_annotation
from .spline import fit_spline, evaluate_spline

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
        
    tck = fit_spline(sample_points, degree=3)

    # Generate a range of values to evaluate the spline at
    t_values = np.linspace(0, 1, 500)

    # Evaluate the spline over the given range
    x_spline, y_spline, z_spline = evaluate_spline(tck, t_values).T

    # Plot the sample points and the spline
    import matplotlib.pyplot as plt

    fig = plt.figure(0)
    ax3d = fig.add_subplot(111, projection='3d')

    x, y, z = sample_points.T

    ax3d.plot(x, y, z, 'b')
    ax3d.plot(x_spline, y_spline, z_spline, 'g')
    fig.show()
    plt.show()
