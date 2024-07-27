import os
from pathlib import Path
from tifffile import imread, TiffWriter
from .memory_usage import calculate_gigabytes_from_dimensions
import shutil


def load_and_save_tiff_from_slices(
    folder_name: str,
    output_file_path: str,
    delete_intermediate=True,
    compression=None,
    metadata={},
    resolution=None,
    resolutionunit=None,
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


def get_sorted_tif_files(directory):
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
    tif_files = sorted((file for file in files if file.endswith(".tif")))

    return tif_files


def join_path(*args):
    return str(Path(*args))
