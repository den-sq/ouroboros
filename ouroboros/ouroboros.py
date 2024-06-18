import numpy as np

from .parse import parse_neuroglancer_json, neuroglancer_config_to_annotation
from .spline import Spline
from .slice import calculate_slice_rects

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def spline_demo():
    ng_config, error = parse_neuroglancer_json("test/sample-data.json")

    if error:
        print(error)
        return
    
    sample_points = neuroglancer_config_to_annotation(ng_config)

    if len(sample_points) == 0:
        print("No annotations found in the file.")
        return
        
    spline = Spline(sample_points, degree=3)

    # Generate a range of values to evaluate the spline at
    t_values = np.linspace(0, 1, 500)

    # Evaluate the spline over the given range
    spline_values = spline(t_values)
    x_spline, y_spline, z_spline = spline_values

    # Plot the sample points and the spline
    fig = plt.figure(0)
    ax3d = fig.add_subplot(111, projection='3d')

    x, y, z = np.array(sample_points).T

    min_dim = min(min(x), min(y), min(z))
    max_dim = max(max(x), max(y), max(z))

    # Enforce consistent sizing to maintain correct aspect ratio
    # (otherwise vectors appear skewed)
    ax3d.set_xlim(min_dim, max_dim)
    ax3d.set_ylim(min_dim, max_dim)
    ax3d.set_zlim(min_dim, max_dim)
    
    ax3d.plot(x, y, z, color='orange') # render the original points
    ax3d.plot(x_spline, y_spline, z_spline, color='black')

    # Plot equidistant points along the spline
    equidistant_params = spline.calculate_equidistant_parameters(50)
    equidistant_points = spline(equidistant_params)
    x_eq, y_eq, z_eq = equidistant_points
    ax3d.plot(x_eq, y_eq, z_eq, 'go')

    # Calculate the tangent, normal, and binormal vectors
    tangent_vectors, normal_vectors, binormal_vectors = spline.calculate_vectors(equidistant_params)

    # Transpose the vectors for easier indexing (3, n) -> (n, 3)
    tangent_vectors = tangent_vectors.T
    normal_vectors = normal_vectors.T
    binormal_vectors = binormal_vectors.T

    # Calculate the slice rects for each t value
    rects = calculate_slice_rects(equidistant_params, spline, 50, 50, spline_points=equidistant_points)

    # Plot the tangent, normal, and binormal vectors
    for i in range(len(equidistant_params)):
        x, y, z = x_eq[i], y_eq[i], z_eq[i]

        tangent = tangent_vectors[i]
        normal = normal_vectors[i]
        binormal = binormal_vectors[i] 

        ax3d.quiver(x, y, z, tangent[0], tangent[1], tangent[2], length=30, color='r')
        ax3d.quiver(x, y, z, normal[0], normal[1], normal[2], length=30, color='b')
        ax3d.quiver(x, y, z, binormal[0], binormal[1], binormal[2], length=30, color='g')

    plot_slices(ax3d, rects)

    fig.show()
    plt.show()

def plot_slices(axes, rects):
    rects = Poly3DCollection(rects)
    rects.set_alpha(0.5)

    axes.add_collection(rects)