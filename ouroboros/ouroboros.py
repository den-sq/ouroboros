import numpy as np

from .parse import parse_neuroglancer_json, neuroglancer_config_to_annotation, neuroglancer_config_to_source
from .spline import Spline
from .slice import calculate_slice_rects, generate_coordinate_grid_for_rect, slice_volume_from_grid
from .bounding_boxes import calculate_bounding_boxes_bsp_link_rects
from .volume_cache import VolumeCache

from tifffile import imwrite

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

DIST_BETWEEN_SLICES = 1
SLICE_WIDTH = 50
SLICE_HEIGHT = 50

def spline_demo():
    ng_config, error = parse_neuroglancer_json("data/sample-data.json")

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
    equidistant_params = spline.calculate_equidistant_parameters(DIST_BETWEEN_SLICES)
    equidistant_points = spline(equidistant_params)
    x_eq, y_eq, z_eq = equidistant_points
    ax3d.plot(x_eq, y_eq, z_eq, 'go')

    # Calculate the RMF frames
    rmf_tangents, rmf_normals, rmf_binormals = spline.calculate_rotation_minimizing_vectors(equidistant_params)
    rmf_tangents = rmf_tangents.T
    rmf_normals = rmf_normals.T
    rmf_binormals = rmf_binormals.T

    # Calculate the slice rects for each t value
    rects = calculate_slice_rects(equidistant_params, spline, SLICE_WIDTH, SLICE_HEIGHT, spline_points=equidistant_points)

    slice_volume = SLICE_WIDTH * SLICE_HEIGHT * DIST_BETWEEN_SLICES

    bounding_boxes, link_rects = calculate_bounding_boxes_bsp_link_rects(rects, slice_volume)

    # Plot the tangent, normal, and binormal vectors
    for i in range(len(equidistant_params)):
        x, y, z = x_eq[i], y_eq[i], z_eq[i]

        tangent = rmf_tangents[i]
        normal = rmf_normals[i]
        binormal = rmf_binormals[i]

        ax3d.quiver(x, y, z, tangent[0], tangent[1], tangent[2], length=30, color='r')
        ax3d.quiver(x, y, z, normal[0], normal[1], normal[2], length=30, color='b')
        ax3d.quiver(x, y, z, binormal[0], binormal[1], binormal[2], length=30, color='g')

        plot_slices(ax3d, [rects[i]], color=choose_color_by_index(link_rects[i]))

    for box in bounding_boxes:
        prism = box.to_prism()
        plot_prism(ax3d, prism)

    fig.show()
    plt.show()

def slice_demo():
    ng_config, error = parse_neuroglancer_json("data/sample-data.json")

    if error:
        print(error)
        return
    
    sample_points = neuroglancer_config_to_annotation(ng_config)

    if len(sample_points) == 0:
        print("No annotations found in the file.")
        return
        
    spline = Spline(sample_points, degree=3)

    # Plot equidistant points along the spline
    equidistant_params = spline.calculate_equidistant_parameters(DIST_BETWEEN_SLICES)
    equidistant_points = spline(equidistant_params)

    # Calculate the RMF frames
    rmf_tangents, rmf_normals, rmf_binormals = spline.calculate_rotation_minimizing_vectors(equidistant_params)
    rmf_tangents = rmf_tangents.T
    rmf_normals = rmf_normals.T
    rmf_binormals = rmf_binormals.T

    print(f"Generating {len(equidistant_params)} slices...")

    # Calculate the slice rects for each t value
    rects = calculate_slice_rects(equidistant_params, spline, SLICE_WIDTH, SLICE_HEIGHT, spline_points=equidistant_points)

    slice_volume = SLICE_WIDTH * SLICE_HEIGHT * DIST_BETWEEN_SLICES

    bounding_boxes, link_rects = calculate_bounding_boxes_bsp_link_rects(rects, slice_volume)

    print(f"{len(equidistant_params)} slices generated")

    source_url = neuroglancer_config_to_source(ng_config)

    if source_url is None:
        print("No source URL found in the file.")
        return
    
    volume_cache = VolumeCache(bounding_boxes, link_rects, source_url)

    # Test downloading all bounding boxes
    # for i in range(len(equidistant_params)):
    #     volume, bounding_box = volume_cache.request_volume_for_slice(i)
    # print(bounding_box.x_min, bounding_box.x_max, bounding_box.y_min, bounding_box.y_max, bounding_box.z_min, bounding_box.z_max)

    slices = []

    for i in range(len(equidistant_params)):
        if i % 10 == 0:
            print(f"Generating slice {i}...")

        grid = generate_coordinate_grid_for_rect(rects[i], SLICE_WIDTH, SLICE_HEIGHT)

        volume, bounding_box = volume_cache.request_volume_for_slice(i)

        slice_i = slice_volume_from_grid(volume, bounding_box, grid, SLICE_WIDTH, SLICE_HEIGHT)

        slices.append(slice_i)

    result = np.stack(slices, axis=0)

    print("Writing to file...")

    imwrite(f'./data/sample.tif', result, photometric='minisblack')

    # grid = generate_coordinate_grid_for_rect(rects[t], SLICE_WIDTH, SLICE_HEIGHT)

    # volume, bounding_box = volume_cache.request_volume_for_slice(t)

    # slice_t = slice_volume_from_grid(volume, bounding_box, grid, SLICE_WIDTH, SLICE_HEIGHT)

    # imwrite('./data/slice_t.tif', slice_t, photometric='minisblack')


def plot_slices(axes, rects, color='blue'):
    rects = Poly3DCollection(rects, facecolors=color)
    rects.set_alpha(0.3)

    axes.add_collection(rects)

def plot_prism(axes, prism):
    prism = Poly3DCollection(prism, alpha=0, linewidths=1, edgecolors='black')

    axes.add_collection(prism)

def choose_color_by_index(index):
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    return colors[index % len(colors)]