import os
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
    # Load the saved tifs in numerical order
    tif_files = get_sorted_tif_files(folder_name)

    # Read in the first tif file to determine if the resulting tif should be a bigtiff
    first_path = os.path.join(folder_name, tif_files[0])
    first_tif = imread(first_path)
    shape = (len(tif_files), *first_tif.shape)

    bigtiff = calculate_gigabytes_from_dimensions(shape, first_tif.dtype) > 4

    contiguous = compression is None

    # Save tifs to a new resulting tif
    with TiffWriter(output_file_path, bigtiff=bigtiff) as tif:
        for filename in tif_files:
            tif_path = os.path.join(folder_name, filename)
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
    # Get all files in the directory
    files = os.listdir(directory)

    # Filter to include only .tif files and sort them numerically
    tif_files = sorted(
        (file for file in files if file.endswith(".tif")),
        key=lambda x: int(os.path.splitext(x)[0]),
    )

    return tif_files
