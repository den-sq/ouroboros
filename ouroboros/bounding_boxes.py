import numpy as np

from cloudvolume import Bbox

DEFAULT_MIN_SLICES_PER_BOX = 5
DEFAULT_SPLIT_THRESHOLD = 0.9

# TODO: Associate slices with boxes

class BoundingBox:
    def __init__(self, initial_rect, split_threshold=DEFAULT_SPLIT_THRESHOLD):
        x_min, x_max, y_min, y_max, z_min, z_max = BoundingBox.get_bounds(initial_rect)

        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.z_min = z_min
        self.z_max = z_max

        self.split_threshold = split_threshold # The threshold of wasted space for splitting the bounding box

        self.utilized_volume = None

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
    def from_rects(rects: np.ndarray, split_threshold=DEFAULT_SPLIT_THRESHOLD):
        """
        Create a bounding box from a set of slices.

        Parameters:
        ----------
            rects (numpy.ndarray): A 3D array of shape (n, 4, 3) containing the slices to bound.

        Returns:
        -------
            (BoundingBox): The bounding box object that contains the slices.
        """

        return BoundingBox(BoundingBox.bound_rects(rects), split_threshold=split_threshold)

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
    
    def to_cloudvolume_bbox(self):
        return Bbox((self.x_min, self.y_min, self.z_min), (self.x_max, self.y_max, self.z_max))
    
    def calculate_volume(self):
        return (self.x_max - self.x_min) * (self.y_max - self.y_min) * (self.z_max - self.z_min)
    
    def should_be_divided(self, utilized_volume):
        return utilized_volume < (1 - self.split_threshold) * self.calculate_volume()
        
    def longest_dimension(self):
        x_range = self.x_max - self.x_min
        y_range = self.y_max - self.y_min
        z_range = self.z_max - self.z_min

        return np.argmax([x_range, y_range, z_range])

    def stretch_to_slice(self, rect: np.ndarray, tangent: np.ndarray, slice_volume, dist_between_slices, split=True):
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

        if self.utilized_volume is None:
            self.utilized_volume = slice_volume
        self.utilized_volume += slice_volume

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
                                slice_volume,
                                dist_between_slices,
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
    
def calculate_bounding_boxes_with_stretching(rects: np.ndarray, tangent_vectors: np.ndarray, slice_volume, dist_between_slices):
    """
    Calculate the bounding boxes of the slices by stretching and splitting a single bounding box.

    Parameters:
    ----------
        rects (numpy.ndarray): A 3D array of shape (n, 4, 3) containing the slices to bound.
        tangent_vectors (numpy.ndarray): A 2D array of shape (n, 3) containing the tangent vectors of the slices.
        slice_volume (float): The volume of a single slice.
        dist_between_slices (float): The distance between slices.

    Returns:
    -------
        (list): A list of bounding boxes that closely fit the slices.
    """
    
    bounding_box = BoundingBox(rects[0])
    bounding_boxes = [bounding_box]

    for i in range(1, len(rects)):
        rect = rects[i]
        tangent = tangent_vectors[i]

        next_bounding_box = bounding_box.stretch_to_slice(rect, tangent, slice_volume, dist_between_slices)

        if next_bounding_box is not bounding_box:
            bounding_boxes.append(next_bounding_box)
            bounding_box = next_bounding_box
    
    return bounding_boxes

def calculate_bounding_boxes_with_bsp(rects: np.ndarray, slice_volume, min_slices_per_box=DEFAULT_MIN_SLICES_PER_BOX, split_threshold=DEFAULT_SPLIT_THRESHOLD):
    """
    Use binary space partitioning to calculate the bounding boxes of the slices,
    starting with a bounding box that bounds all of the rects.

    Parameters:
    ----------
        rects (numpy.ndarray): A 3D array of shape (n, 4, 3) containing the slices to bound.

    Returns:
    -------
        (list): A list of bounding boxes that closely fit the slices.
    """

    # TODO: Consider adding a depth limit

    if len(rects) == 0:
        return []
    
    # Calculate the initial bounding box that encompasses all rects
    initial_bounding_box = BoundingBox.from_rects(rects, split_threshold=split_threshold)

    # Stack for iterative BSP: each item is a tuple (rects subset, bounding box, repeat entry)
    stack = [(rects, initial_bounding_box, False)]
    bounding_boxes = []

    while stack:
        current_rects, current_bounding_box, repeat = stack.pop()

        # Determine if further division is necessary or efficient
        if len(current_rects) <= min_slices_per_box or \
                not current_bounding_box.should_be_divided(slice_volume * len(current_rects)):
            bounding_boxes.append(current_bounding_box)
            continue

        # Determine the longest dimension to split along
        longest_dim = current_bounding_box.longest_dimension()

        # Split the current set of rects based on the median of the longest dimension
        median = np.median(current_rects[:, :, longest_dim])
        left_partition = current_rects[current_rects[:, :, longest_dim].mean(axis=1) < median]
        right_partition = current_rects[current_rects[:, :, longest_dim].mean(axis=1) >= median] 

        # Handle any unsplittable boxes
        if repeat and (len(left_partition) == 0 or len(right_partition) == 0):
            bounding_boxes.append(current_bounding_box)
            continue

        # Calculate bounding boxes for the partitions
        if len(left_partition) > 0:
            left_bounding_box = BoundingBox.from_rects(left_partition, split_threshold=split_threshold)
            stack.append((left_partition, left_bounding_box, len(right_partition) == 0))
        if len(right_partition) > 0:
            right_bounding_box = BoundingBox.from_rects(right_partition, split_threshold=split_threshold)
            stack.append((right_partition, right_bounding_box, len(left_partition) == 0))

    return bounding_boxes
    
def calculate_bounding_boxes_bsp_link_rects(rects: np.ndarray, slice_volume, min_slices_per_box=DEFAULT_MIN_SLICES_PER_BOX, split_threshold=DEFAULT_SPLIT_THRESHOLD):
    """
    Use binary space partitioning to calculate the bounding boxes of the slices,
    starting with a bounding box that bounds all of the rects.

    Parameters:
    ----------
        rects (numpy.ndarray): A 3D array of shape (n, 4, 3) containing the slices to bound.

    Returns:
    -------
        (list, list): A list of bounding boxes that closely fit the slices and a list 
                      mapping each rect index to its bounding box.
    """

    if len(rects) == 0:
        return [], []
    
    # Calculate the initial bounding box that encompasses all rects
    initial_bounding_box = BoundingBox.from_rects(rects, split_threshold=split_threshold)

    # Stack for iterative BSP: each item is a tuple (rect indices subset, bounding box, repeat entry)
    indices = np.arange(len(rects))
    stack = [(indices, initial_bounding_box, False)]
    bounding_boxes = []
    rect_to_box_map = [None] * len(rects)

    while stack:
        current_indices, current_bounding_box, repeat = stack.pop()
        current_rects = rects[current_indices]

        # Determine if further division is necessary or efficient
        if len(current_rects) <= min_slices_per_box or \
                not current_bounding_box.should_be_divided(slice_volume * len(current_rects)):
            bounding_boxes.append(current_bounding_box)
            for idx in current_indices:
                rect_to_box_map[idx] = len(bounding_boxes) - 1
            continue

        # Determine the longest dimension to split along
        longest_dim = current_bounding_box.longest_dimension()

        # Split the current set of rects based on the median of the longest dimension
        median = np.median(current_rects[:, :, longest_dim])
        left_mask = current_rects[:, :, longest_dim].mean(axis=1) < median
        right_mask = ~left_mask

        left_partition_indices = current_indices[left_mask]
        right_partition_indices = current_indices[right_mask]

        # Handle any unsplittable boxes
        if repeat and (len(left_partition_indices) == 0 or len(right_partition_indices) == 0):
            bounding_boxes.append(current_bounding_box)
            for idx in current_indices:
                rect_to_box_map[idx] = len(bounding_boxes) - 1
            continue

        # Calculate bounding boxes for the partitions
        if len(left_partition_indices) > 0:
            left_bounding_box = BoundingBox.from_rects(rects[left_partition_indices], split_threshold=split_threshold)
            stack.append((left_partition_indices, left_bounding_box, len(right_partition_indices) == 0))
        if len(right_partition_indices) > 0:
            right_bounding_box = BoundingBox.from_rects(rects[right_partition_indices], split_threshold=split_threshold)
            stack.append((right_partition_indices, right_bounding_box, len(left_partition_indices) == 0))

    return bounding_boxes, rect_to_box_map
