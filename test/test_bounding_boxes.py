# BENCHMARK

from ouroboros.parse import parse_neuroglancer_json, neuroglancer_config_to_annotation
from ouroboros.spline import Spline
from ouroboros.slice import calculate_slice_rects
from ouroboros.bounding_boxes import calculate_bounding_boxes_with_bsp

DIST_BETWEEN_SLICES = 1
SLICE_WIDTH = 50
SLICE_HEIGHT = 50

def setup_calculate_bounding_boxes_with_bsp_demo():
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

    # Calculate the slice rects for each t value
    rects = calculate_slice_rects(equidistant_params, spline, SLICE_WIDTH, SLICE_HEIGHT, spline_points=equidistant_points)

    slice_volume = SLICE_WIDTH * SLICE_HEIGHT * DIST_BETWEEN_SLICES

    return rects, slice_volume

def test_calculate_bounding_boxes_with_bsp_demo(benchmark):
    rects, slice_volume = setup_calculate_bounding_boxes_with_bsp_demo()

    benchmark(lambda: calculate_bounding_boxes_with_bsp(rects, slice_volume))

