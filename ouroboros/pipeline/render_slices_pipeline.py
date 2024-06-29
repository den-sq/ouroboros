from ouroboros.helpers.bounding_boxes import calculate_bounding_boxes_bsp_link_rects
from ouroboros.helpers.slice import calculate_slice_rects
from ouroboros.helpers.spline import Spline
from .pipeline import PipelineStep
from ouroboros.config import Config
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class RenderSlicesPipelineStep(PipelineStep):
    def __init__(self, render_vectors_and_points=False) -> None:
        super().__init__(inputs=("config", "sample_points"))

        self.render_vectors_and_points = render_vectors_and_points

    def _process(self, input_data: tuple[any]) -> None | str:
        config, sample_points, _ = input_data

        # Verify that a config object is provided
        if not isinstance(config, Config):
            return "Input data must contain a Config object."

        # Verify that sample points is given
        if not isinstance(sample_points, np.ndarray):
            return "Input data must contain an array of sample points."

        spline = Spline(sample_points, degree=3)

        # Generate a range of values to evaluate the spline at
        t_values = np.linspace(0, 1, 500)

        # Evaluate the spline over the given range
        spline_values = spline(t_values)
        x_spline, y_spline, z_spline = spline_values

        # Plot the sample points and the spline
        fig = plt.figure(0)
        ax3d = fig.add_subplot(111, projection="3d")

        x, y, z = np.array(sample_points).T

        min_dim = min(min(x), min(y), min(z))
        max_dim = max(max(x), max(y), max(z))

        # Enforce consistent sizing to maintain correct aspect ratio
        # (otherwise vectors appear skewed)
        ax3d.set_xlim(min_dim, max_dim)
        ax3d.set_ylim(min_dim, max_dim)
        ax3d.set_zlim(min_dim, max_dim)

        if self.render_vectors_and_points:
            ax3d.plot(x, y, z, color="orange")  # render the original points
        ax3d.plot(x_spline, y_spline, z_spline, color="black")

        # Plot equidistant points along the spline
        equidistant_params = spline.calculate_equidistant_parameters(
            config.dist_between_slices
        )
        equidistant_points = spline(equidistant_params)
        x_eq, y_eq, z_eq = equidistant_points
        if self.render_vectors_and_points:
            ax3d.plot(x_eq, y_eq, z_eq, "go")

        # Calculate the RMF frames
        rmf_tangents, rmf_normals, rmf_binormals = (
            spline.calculate_rotation_minimizing_vectors(equidistant_params)
        )
        rmf_tangents = rmf_tangents.T
        rmf_normals = rmf_normals.T
        rmf_binormals = rmf_binormals.T

        # Calculate the slice rects for each t value
        rects = calculate_slice_rects(
            equidistant_params,
            spline,
            config.slice_width,
            config.slice_height,
            spline_points=equidistant_points,
        )

        bounding_boxes, link_rects = calculate_bounding_boxes_bsp_link_rects(rects)

        # Plot the tangent, normal, and binormal vectors
        for i in range(len(equidistant_params)):
            x, y, z = x_eq[i], y_eq[i], z_eq[i]

            tangent = rmf_tangents[i]
            normal = rmf_normals[i]
            binormal = rmf_binormals[i]

            if self.render_vectors_and_points:
                ax3d.quiver(
                    x, y, z, tangent[0], tangent[1], tangent[2], length=30, color="r"
                )
                ax3d.quiver(
                    x, y, z, normal[0], normal[1], normal[2], length=30, color="b"
                )
                ax3d.quiver(
                    x, y, z, binormal[0], binormal[1], binormal[2], length=30, color="g"
                )

            plot_slices(ax3d, [rects[i]], color=choose_color_by_index(link_rects[i]))

        for box in bounding_boxes:
            prism = box.to_prism()
            plot_prism(ax3d, prism)

        fig.show()
        plt.show()

        return None


def plot_slices(axes, rects, color="blue"):
    rects = Poly3DCollection(rects, facecolors=color)
    rects.set_alpha(0.3)

    axes.add_collection(rects)


def plot_prism(axes, prism):
    prism = Poly3DCollection(prism, alpha=0, linewidths=1, edgecolors="black")

    axes.add_collection(prism)


def choose_color_by_index(index):
    colors = ["red", "orange", "yellow", "green", "blue", "purple"]
    return colors[index % len(colors)]
