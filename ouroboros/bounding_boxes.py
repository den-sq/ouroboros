import numpy as np

DEFAULT_SPLIT_THRESHOLD = 0.8

# TODO: Try binary space partitioning
# TODO: Make multiple bounding box strategies

class BoundingBox:
    def __init__(self, initial_rect, slice_volume, dist_between_slices, split_threshold=DEFAULT_SPLIT_THRESHOLD):
        x_min, x_max, y_min, y_max, z_min, z_max = BoundingBox.get_bounds(initial_rect)

        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.z_min = z_min
        self.z_max = z_max

        self.slice_volume = slice_volume
        self.dist_between_slices = dist_between_slices
        self.split_threshold = split_threshold # The threshold of wasted space for splitting the bounding box

        self.utilized_volume = self.slice_volume

        self.prev_tangent = None

    @staticmethod 
    def bound_rects(rects: np.ndarray):
        """
        Get the minimum bounding box of a set of slices.

        Parameters:
        ----------
            rects (numpy.ndarray): A 3D array of shape (n, 4, 3) containing the slices to bound.

        Returns:
        -------
            (numpy.ndarray): A new rect that bounds all the slices.
        """

        # Isolate the x, y, and z coordinates
        x_coords = rects[:, :, 0]
        y_coords = rects[:, :, 1]
        z_coords = rects[:, :, 2]

        # Find the minimum and maximum values for x, y, and z
        x_min = np.min(x_coords)
        x_max = np.max(x_coords)
        y_min = np.min(y_coords)
        y_max = np.max(y_coords)
        z_min = np.min(z_coords)
        z_max = np.max(z_coords)

        return BoundingBox.bounds_to_rect(x_min, x_max, y_min, y_max, z_min, z_max)


    @staticmethod
    def bounds_to_rect(x_min, x_max, y_min, y_max, z_min, z_max):
        return np.array([
            [x_min, y_max, z_max],
            [x_max, y_max, z_min],
            [x_max, y_min, z_min],
            [x_min, y_min, z_max]
        ])
    
    @staticmethod
    def get_bounds(rect: np.ndarray):
        x, y, z = rect.T
        x_min = min(x)
        x_max = max(x)
        y_min = min(y)
        y_max = max(y)
        z_min = min(z)
        z_max = max(z)

        return x_min, x_max, y_min, y_max, z_min, z_max
    
    def calculate_volume(self):
        return (self.x_max - self.x_min) * (self.y_max - self.y_min) * (self.z_max - self.z_min)
        
    def stretch_to_slice(self, rect: np.ndarray, tangent: np.ndarray, split=True):
        """
        Stretch the bounding box to fit a new slice, potentially splitting 
        the bounding box if the wasted space exceeds the split threshold.

        Parameters:
        ----------
            slice (numpy.ndarray): A 2D array of shape (4, 3) containing the slice to fit.
            tangent (numpy.ndarray): A 1D array of shape (3,) containing the tangent vector of the slice (assumed to be normalized).
            split (bool): Whether to split the bounding box if the wasted space exceeds the split threshold.

        Returns:
        -------
            (BoundingBox): The bounding box object that contains the slice (a new one if the previous one was split).
        """

        x_min, x_max, y_min, y_max, z_min, z_max = BoundingBox.get_bounds(rect)

        self.utilized_volume += self.slice_volume

        if split and self.utilized_volume < (1 - self.split_threshold) * self.calculate_volume() and self.prev_tangent is not None:
            # Determine the dominant axis of the tangent vector
            axis = np.argmax(np.abs(self.prev_tangent))

            # Calculate the bounds of the slice that is not covered by the current bounding box
            if axis == 0:
                if self.prev_tangent[0] > 0:
                    x_min = max(x_min, self.x_max)
                else:
                    x_max = min(x_max, self.x_min)
            elif axis == 1:
                if self.prev_tangent[1] > 0:
                    y_min = max(y_min, self.y_max)
                else:
                    y_max = min(y_max, self.y_min)
            else:
                if self.prev_tangent[2] > 0:
                    z_min = max(z_min, self.z_max)
                else:
                    z_max = min(z_max, self.z_min)
        
            return BoundingBox(BoundingBox.bounds_to_rect(x_min, x_max, y_min, y_max, z_min, z_max), 
                                self.slice_volume,
                                self.dist_between_slices,
                                split_threshold=self.split_threshold)
        
        self.x_min = min(self.x_min, x_min)
        self.x_max = max(self.x_max, x_max)
        self.y_min = min(self.y_min, y_min)
        self.y_max = max(self.y_max, y_max)
        self.z_min = min(self.z_min, z_min)
        self.z_max = max(self.z_max, z_max)

        self.prev_tangent = tangent

        return self
    
    def to_prism(self):
        vertices = np.array([
            [self.x_min, self.y_max, self.z_max],
            [self.x_max, self.y_max, self.z_max],
            [self.x_max, self.y_min, self.z_max],
            [self.x_min, self.y_min, self.z_max],
            [self.x_min, self.y_max, self.z_min],
            [self.x_max, self.y_max, self.z_min],
            [self.x_max, self.y_min, self.z_min],
            [self.x_min, self.y_min, self.z_min]
        ])

        faces = np.array([
            [vertices[0], vertices[1], vertices[2], vertices[3]], # Top
            [vertices[4], vertices[5], vertices[6], vertices[7]], # Bottom
            [vertices[0], vertices[1], vertices[5], vertices[4]], # Front
            [vertices[2], vertices[3], vertices[7], vertices[6]], # Back
            [vertices[0], vertices[3], vertices[7], vertices[4]], # Left
            [vertices[1], vertices[2], vertices[6], vertices[5]]  # Right
        ])

        return faces
    
def calculate_bounding_boxes(rects: np.ndarray, tangent_vectors: np.ndarray, slice_volume, dist_between_slices):
    bounding_box = BoundingBox(rects[0], slice_volume, dist_between_slices)
    bounding_boxes = [bounding_box]

    for i in range(1, len(rects)):
        rect = rects[i]
        tangent = tangent_vectors[i]

        next_bounding_box = bounding_box.stretch_to_slice(rect, tangent)

        if next_bounding_box is not bounding_box:
            bounding_boxes.append(next_bounding_box)
            bounding_box = next_bounding_box
    
    return bounding_boxes