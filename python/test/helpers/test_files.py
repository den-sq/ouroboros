import os
from tifffile import imwrite
from ouroboros.helpers.files import (
    load_and_save_tiff_from_slices,
    get_sorted_tif_files,
    join_path,
)


def test_load_and_save_tiff_from_slices(tmp_path):
    slices_folder = tmp_path / "slices"
    slices_folder.mkdir()

    # Create some sample tiff files
    for i in range(5):
        imwrite(slices_folder / f"slice_{i:03d}.tif", data=[[i]])

    output_file_path = tmp_path / "output.tif"
    load_and_save_tiff_from_slices(
        folder_name=str(slices_folder),
        output_file_path=str(output_file_path),
        delete_intermediate=True,
        compression=None,
        metadata={"test": "metadata"},
        resolution=(300, 300),
        resolutionunit="inch",
    )

    assert output_file_path.exists()

    # Make sure the intermediate files were deleted
    assert len(list(tmp_path.iterdir())) == 1


def test_get_sorted_tif_files(tmp_path):
    # Generate some sample tiff files
    filenames = [f"{i:03d}.tif" for i in range(101)]
    original_filenames = filenames.copy()

    # Randomize the order
    import random

    random.shuffle(filenames)

    # Create the files
    for filename in filenames:
        (tmp_path / filename).touch()

    sorted_files = get_sorted_tif_files(str(tmp_path))
    assert sorted_files == original_filenames


def test_get_sorted_tif_files_prefix(tmp_path):
    # Generate some sample tiff files
    filenames = [f"slice_{i:03d}.tif" for i in range(101)]
    original_filenames = filenames.copy()

    # Randomize the order
    import random

    random.shuffle(filenames)

    # Create the files
    for filename in filenames:
        (tmp_path / filename).touch()

    sorted_files = get_sorted_tif_files(str(tmp_path))
    assert sorted_files == original_filenames


def test_join_path():
    path = join_path("folder", "subfolder", "file.txt")
    assert path == os.path.join("folder", "subfolder", "file.txt")
