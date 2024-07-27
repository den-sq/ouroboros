from .bounding_boxes import BoundingBox
from .memory_usage import calculate_gigabytes_from_dimensions

from cloudvolume import CloudVolume, VolumeCutout

FLUSH_CACHE = False


class VolumeCache:
    def __init__(
        self,
        bounding_boxes: list[BoundingBox],
        link_rects: list[int],
        cloud_volume_interface: "CloudVolumeInterface",
        mip=None,
        flush_cache=FLUSH_CACHE,
    ) -> None:
        self.bounding_boxes = bounding_boxes
        self.link_rects = link_rects
        self.cv = cloud_volume_interface
        self.mip = mip
        self.flush_cache = flush_cache

        self.last_requested_slice = None

        # Stores the volume data for each bounding box
        self.volumes = [None] * len(bounding_boxes)

        # Indicates whether the a volume should be cached after the last slice to request it is processed
        self.cache_volume = [False] * len(bounding_boxes)
        self.cache_volume[link_rects[-1]] = VolumeCache.should_cache_last_volume(
            link_rects
        )

        self.init_cloudvolume()

    def to_dict(self):
        return {
            "bounding_boxes": [bb.to_dict() for bb in self.bounding_boxes],
            "link_rects": self.link_rects,
            "cv": self.cv.to_dict(),
            "mip": self.mip,
            "flush_cache": self.flush_cache,
        }

    @staticmethod
    def from_dict(data: dict):
        bounding_boxes = [BoundingBox.from_dict(bb) for bb in data["bounding_boxes"]]
        link_rects = data["link_rects"]
        cv = CloudVolumeInterface.from_dict(data["cv"])
        mip = data["mip"]
        flush_cache = data["flush_cache"]

        return VolumeCache(bounding_boxes, link_rects, cv, mip, flush_cache)

    def init_cloudvolume(self):
        if self.mip is None:
            self.mip = min(self.cv.available_mips)

    def get_volume_gigabytes(self):
        return calculate_gigabytes_from_dimensions(
            self.get_volume_shape(), self.get_volume_dtype()
        )

    def get_volume_shape(self):
        return self.cv.get_volume_shape(self.mip)

    def has_color_channels(self):
        return self.cv.has_color_channels

    def get_num_channels(self):
        return self.cv.num_channels

    def get_volume_dtype(self):
        return self.cv.dtype

    def get_volume_mip(self):
        return self.mip

    def set_volume_mip(self, mip: int):
        self.mip = mip

    def get_resolution_um(self):
        return self.cv.get_resolution_um(self.mip)

    @staticmethod
    def should_cache_last_volume(link_rects: list[int]):
        if link_rects[0] == link_rects[-1]:
            return True

        return False

    def volume_index(self, slice_index: int):
        return self.link_rects[slice_index]

    def request_volume_for_slice(self, slice_index: int):
        """
        Get the volume data for a slice index.

        Suitable for use in a loop that processes slices sequentially (not parallel).

        Download the volume if it is not already cached and remove the last requested volume if it is not to be cached.

        Parameters:
        ----------
            slice_index (int): The index of the slice to request.

        Returns:
        -------
            tuple: A tuple containing the volume data and the bounding box of the slice.
        """

        vol_index = self.volume_index(slice_index)
        bounding_box = self.bounding_boxes[vol_index]

        # Download the volume if it is not already cached
        if self.volumes[vol_index] is None:
            self.download_volume(vol_index, bounding_box)

        # Remove the last requested volume if it is not to be cached
        if (
            self.last_requested_slice is not None
            and self.last_requested_slice != vol_index
            and not self.cache_volume[self.last_requested_slice]
        ):
            self.remove_volume(self.last_requested_slice)

        self.last_requested_slice = vol_index

        return self.volumes[vol_index], bounding_box

    def remove_volume(self, volume_index: int):
        # Avoid removing the volume if it is cached for later
        if self.cache_volume[volume_index]:
            return

        self.volumes[volume_index] = None

    def download_volume(
        self, volume_index: int, bounding_box: BoundingBox, parallel=False
    ) -> VolumeCutout:
        bbox = bounding_box.to_cloudvolume_bbox()

        # Download the bounding box volume
        volume = self.cv.cv.download(bbox, mip=self.mip, parallel=parallel)

        # Store the volume in the cache
        self.volumes[volume_index] = volume

    def create_processing_data(self, volume_index: int, parallel=False):
        """
        Generate a data packet for processing a volume.

        Suitable for parallel processing.

        Parameters:
        ----------
            volume_index (int): The index of the volume to process.
            parallel (bool): Whether to download the volume in parallel (only do parallel if downloading in one thread).

        Returns:
        -------
            tuple: A tuple containing the volume data, the bounding box of the volume,
                    the slice indices associated with the volume, and a function to remove the volume from the cache.
        """

        bounding_box = self.bounding_boxes[volume_index]

        # Download the volume if it is not already cached
        if self.volumes[volume_index] is None:
            self.download_volume(volume_index, bounding_box, parallel=parallel)

        # Get all slice indices associated with this volume
        slice_indices = self.get_slice_indices(volume_index)

        return self.volumes[volume_index], bounding_box, slice_indices, volume_index

    def get_slice_indices(self, volume_index: int):
        return [i for i, v in enumerate(self.link_rects) if v == volume_index]

    def flush_local_cache(self):
        if self.flush_cache:
            self.cv.flush_cache()


class CloudVolumeInterface:
    def __init__(self, source_url: str):
        self.source_url = source_url

        self.cv = CloudVolume(self.source_url, parallel=True, cache=True)

        self.available_mips = self.cv.available_mips
        self.dtype = self.cv.dtype

    def to_dict(self):
        return {"source_url": self.source_url}

    @staticmethod
    def from_dict(data: dict):
        source_url = data["source_url"]
        return CloudVolumeInterface(source_url)

    @property
    def has_color_channels(self):
        return len(self.cv.shape) == 4

    @property
    def num_channels(self):
        return self.cv.shape[-1]

    def get_volume_shape(self, mip: int):
        return self.cv.mip_volume_size(mip)

    def get_resolution_nm(self, mip: int):
        return self.cv.mip_resolution(mip)

    def get_resolution_um(self, mip: int):
        return self.get_resolution_nm(mip) / 1000

    def flush_cache(self):
        self.cv.cache.flush()
