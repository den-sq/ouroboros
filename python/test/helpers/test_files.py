import os
from tifffile import imwrite
from ouroboros.helpers.files import (
    format_backproject_output_file,
    format_backproject_output_multiple,
    format_backproject_resave_volume,
    format_backproject_tempvolumes,
    format_slice_output_config_file,
    format_slice_output_file,
    format_slice_output_multiple,
    format_tiff_name,
    load_and_save_tiff_from_slices,
    get_sorted_tif_files,
    join_path,
    combine_unknown_folder,
    num_digits_for_n_files,
    parse_tiff_name,
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


def test_combine_unknown_folder_posix_no_slash():
    directory = "/path/to/directory"
    filename = "file.txt"
    combined = combine_unknown_folder(directory, filename)
    assert combined == "/path/to/directory/file.txt"


def test_combine_unknown_folder_posix_slash():
    directory = "/path/to/directory/"
    filename = "file.txt"
    combined = combine_unknown_folder(directory, filename)
    assert combined == "/path/to/directory/file.txt"


def test_combine_unknown_folder_win_no_slash():
    directory = "C:\\path\\to\\directory"
    filename = "file.txt"
    combined = combine_unknown_folder(directory, filename)
    assert combined == "C:\\path\\to\\directory\\file.txt"


def test_combine_unknown_folder_win_slash():
    directory = "C:\\path\\to\\directory\\"
    filename = "file.txt"
    combined = combine_unknown_folder(directory, filename)
    assert combined == "C:\\path\\to\\directory\\file.txt"


def test_format_slice_output_file():
    result = format_slice_output_file("test")
    assert isinstance(result, str)


def test_format_slice_output_multiple():
    result = format_slice_output_multiple("test")
    assert isinstance(result, str)


def test_format_slice_output_config_file():
    result = format_slice_output_config_file("test")
    assert isinstance(result, str)


def test_format_backproject_output_file():
    result = format_backproject_output_file("test")
    assert isinstance(result, str)
    assert result == "test-backprojected.tif"

    result = format_backproject_output_file("test", offset=(1, 2, 3))
    assert isinstance(result, str)
    assert result == "test-backprojected-1-2-3.tif"


def test_format_backproject_output_multiple():
    result = format_backproject_output_multiple("test")
    assert isinstance(result, str)
    assert result == "test-backprojected"

    result = format_backproject_output_multiple("test", offset=(1, 2, 3))
    assert isinstance(result, str)
    assert result == "test-backprojected-1-2-3"


def test_format_backproject_tempvolumes():
    result = format_backproject_tempvolumes("test")
    assert isinstance(result, str)


def test_format_backproject_resave_volume():
    result = format_backproject_resave_volume("test")
    assert isinstance(result, str)


def test_format_tiff_name():
    result = format_tiff_name(1, 3)
    assert isinstance(result, str)
    assert result == f"{str(1).zfill(3)}.tif"


def test_parse_tiff_name():
    result = parse_tiff_name("001.tif")
    assert isinstance(result, int)
    assert result == 1


def test_num_digits_for_n_files():
    result = num_digits_for_n_files(100)
    assert isinstance(result, int)
    assert result == 2
