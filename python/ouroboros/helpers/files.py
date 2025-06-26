from functools import partial
import os
import shutil
from threading import Thread

import numpy as np
from numpy.typing import ArrayLike
from pathlib import Path
from tifffile import imread, TiffWriter, memmap

from .memory_usage import calculate_gigabytes_from_dimensions


def load_and_save_tiff_from_slices(
    folder_name: str,
    output_file_path: str,
    delete_intermediate: bool = True,
    compression: str = None,
    metadata: dict = {},
    resolution: tuple[int, int] = None,
    resolutionunit: str = None,
):
    """
    Load tiff files from a folder and save them to a new tiff file.

    Parameters
    ----------
    folder_name : str
        The folder containing the tiff files to load.
    output_file_path : str
        The path to save the resulting tiff file.
    delete_intermediate : bool, optional
        Whether to delete the intermediate tiff files after saving the resulting tiff file.
        The default is True.
    compression : str, optional
        The compression to use for the resulting tiff file.
        The default is None.
    metadata : dict, optional
        Metadata to save with the resulting tiff file.
        The default is {}.
    resolution : tuple[int, int], optional
        The resolution of the resulting tiff file.
        The default is None.
    resolutionunit : str, optional
        The resolution unit of the resulting tiff file.
        The default is None.
    """

    # Load the saved tifs in numerical order
    tif_files = get_sorted_tif_files(folder_name)

    # Read in the first tif file to determine if the resulting tif should be a bigtiff
    first_path = join_path(folder_name, tif_files[0])
    first_tif = imread(first_path)
    shape = (len(tif_files), *first_tif.shape)

    bigtiff = calculate_gigabytes_from_dimensions(shape, first_tif.dtype) > 4

    contiguous = compression is None

    # Save tifs to a new resulting tif
    with TiffWriter(output_file_path, bigtiff=bigtiff) as tif:
        for filename in tif_files:
            tif_path = join_path(folder_name, filename)
            tif_file = imread(tif_path)
            tif.write(
                tif_file,
                contiguous=contiguous,
                compression=compression,
                metadata=metadata,
                resolution=resolution,
                resolutionunit=resolutionunit,
                software="ouroboros",
            )

    # Delete slices folder
    if delete_intermediate:
        shutil.rmtree(folder_name)


def get_sorted_tif_files(directory: str) -> list[str]:
    """
    Get all .tif files in a directory and sort them numerically.

    Assumes that the files are named with a number at the beginning of the file name.
    E.g. 0001.tif, 0002.tif, 0003.tif, etc.

    Parameters
    ----------
    directory : str
        The directory to search for .tif files.

    Returns
    -------
    list[str]
        The sorted list of .tif files in the directory.
    """

    # Get all files in the directory
    files = os.listdir(directory)

    # Filter to include only .tif files and sort them numerically
    tif_files = sorted((file for file in files if file.endswith((".tif", ".tiff"))))

    return tif_files


def join_path(*args) -> str:
    return str(Path(*args))


def combine_unknown_folder(directory_path: str, filename: str) -> str:
    """
    Combine a directory path and a filename into a single path.

    Automatically determines the correct path separator to use based on the directory path.

    Parameters
    ----------
    directory_path : str
        The directory path.
    filename : str
        The filename.

    Returns
    -------
    str
        The combined path.
    """

    if not directory_path.endswith("/") and not directory_path.endswith("\\"):
        # Attempt to determine the correct path separator
        if "/" in directory_path:
            directory_path += "/"
        else:
            directory_path += "\\"

    return directory_path + filename


def format_slice_output_file(output_name: str) -> str:
    return output_name + ".tif"


def format_slice_output_multiple(output_name: str) -> str:
    return output_name + "-slices"


def format_slice_output_config_file(output_name: str) -> str:
    return output_name + "-configuration.json"


def format_backproject_output_file(output_name: str, offset: tuple[int] | None = None) -> str:
    if offset is not None:
        offset_str = "-".join(map(str, offset))
        return output_name + f"-backprojected-{offset_str}.tif"

    return output_name + "-backprojected.tif"


def format_backproject_output_multiple(
    output_name: str, offset: tuple[int] | None = None
) -> str:
    if offset is not None:
        offset_str = "-".join(map(str, offset))
        return output_name + f"-backprojected-{offset_str}"

    return output_name + "-backprojected"


def format_backproject_tempvolumes(output_name: str) -> str:
    return output_name + "-tempvolumes"


def format_backproject_resave_volume(output_name: str) -> str:
    return output_name + "-temp-straightened.tif"


def format_tiff_name(i: int, num_digits: int) -> str:
    return f"{str(i).zfill(num_digits)}.tif"


def parse_tiff_name(tiff_name: str) -> int:
    return int(tiff_name.split(".")[0])


def num_digits_for_n_files(n: int) -> int:
    return len(str(n - 1))


def np_convert(dtype: np.dtype, source: ArrayLike, normalize=True):
    if not normalize:
        return source.astype(dtype)
    if np.issubdtype(dtype, np.integer):
        dtype_range = np.iinfo(dtype).max - np.iinfo(dtype).min
        source_range = np.max(source) - np.min(source)

        # Avoid divide by 0, esp. as numpy segfaults when you do.
        if source_range == 0.0:
            source_range = 1.0

        return (source * max(int(dtype_range / source_range), 1)).astype(dtype)
    elif np.issubdtype(dtype, np.floating):
        return source.astype(dtype)


def generate_tiff_write(write_func, compression, micron_resolution, backprojection_offset):
    # Volume cache resolution is in voxel size, but .tiff XY resolution is in voxels per unit, so we invert.
    resolution = [1.0 / voxel_size for voxel_size in micron_resolution[:2] * 0.0001]
    resolutionunit = "CENTIMETER"
    # However, Z Resolution doesn't have an inbuilt property or strong convention, so going with this atm.
    metadata = {
        "spacing": micron_resolution[2],
        "unit": "um"
    }

    if backprojection_offset is not None:
        metadata["backprojection_offset_min_xyz"] = backprojection_offset

    return partial(write_func,
                   contiguous=compression is None or compression == "none",
                   compression=compression,
                   metadata=metadata,
                   resolution=resolution,
                   resolutionunit=resolutionunit,
                   software="ouroboros")


def write_memmap_with_create(file_path: os.PathLike, indicies: tuple[np.ndarray], data: np.ndarray,
                             shape: tuple, dtype: type):
    if file_path.exists():
        try:
            target_file = memmap(file_path)
        except BaseException as be:
            print(f"MM: {be} - {file_path} ")
            import time
            time.sleep(0.5)
            target_file = memmap(file_path)
    else:
        if shape is None or dtype is None:
            raise ValueError(f"Must have shape ({shape} given) and dtype ({dtype} given) when creating a memmap.")
        target_file = memmap(file_path, shape=shape, dtype=dtype)
        target_file[:] = 0

    def ab(flags: np.ndarray[bool], index):
        return tuple(dim[flags] for dim in index) if isinstance(index, tuple) else index[flags]

    if indicies is not None and data is not None:
        exist = target_file[indicies] != 0
        if np.any(exist):
            target_file[ab(exist, indicies)] = np.mean([target_file[indicies][exist], data[exist]],
                                                       axis=0, dtype=target_file.dtype)
            target_file[ab(np.invert(exist), indicies)] = data[np.invert(exist)]
        else:
            target_file[indicies] = data
    elif indicies is not None or data is not None:
        raise ValueError(f"Could not write data as indicies (None? {indicies is None})"
                         f"or data (None? {data is None}) were missing.")
    del target_file


def rewrite_by_dimension(writeable, tif_write, base_path, dtype=np.uint16, is_single=False, write_start=0,
                         use_threads=True):
    # Gets contiguous elements starting at 0 for single_file writing for accuracy
    write_here = writeable[writeable == (np.indices(writeable.shape) + write_start)] if is_single else writeable
    write_later = np.setdiff1d(write_here, writeable)

    # image path inputs
    img_paths = [base_path.joinpath(f"{index:05}.tiff") for index in write_here]
    threads = []

    def make_args(img):
        return (np_convert(dtype, imread(img)), ) if is_single else (img, np_convert(dtype, imread(img), False))

    if use_threads:
        threads = [Thread(target=tif_write, args=make_args(img)) for img in img_paths]
        for thread in threads:
            thread.start()
    else:
        for img in img_paths:
            tif_write(*make_args(img))

    return threads, write_later, write_here
