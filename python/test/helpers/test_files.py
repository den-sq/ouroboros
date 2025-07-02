import os
from pathlib import Path

import numpy as np
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
    np_convert,
    generate_tiff_write,
    write_memmap_with_create,
    rewrite_by_dimension
)


def test_load_and_save_tiff_from_slices(tmp_path):
    slices_folder = tmp_path / "slices"
    slices_folder.mkdir()

    input_names = [slices_folder / f"slice_{i:03d}.tif" for i in range(5)]

    # Change some names to .tiff to ensure both .tif and .tiff are read.
    from random import randrange
    for i in [randrange(5) for j in range(2)]:
        input_names[i] = input_names[i].with_suffix('.tiff')

    # Create some sample tiff files
    for name in input_names:
        imwrite(name, data=[[i]])

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
    import random

    # Generate some sample tiff files
    filenames = [Path(tmp_path, f"{i:03d}.tif") for i in range(101)]

    # Ensure both .tif and .tiff files are handled.
    for i in [random.randrange(101) for j in range(35)]:
        filenames[i] = filenames[i].with_suffix('.tiff')

    original_filenames = [path.name for path in filenames]

    # Randomize the order
    random.shuffle(filenames)

    # Create the files
    for path in filenames:
        path.touch()

    sorted_files = get_sorted_tif_files(str(tmp_path))
    assert sorted_files == original_filenames


def test_get_sorted_tif_files_prefix(tmp_path):
    import random

    # Generate some sample tiff files
    filenames = [Path(tmp_path, f"slice_{i:03d}.tif") for i in range(101)]

    # Ensure both .tif and .tiff files are handled.
    for i in [random.randrange(101) for j in range(35)]:
        filenames[i] = filenames[i].with_suffix('.tiff')

    original_filenames = [path.name for path in filenames]

    # Randomize the order
    random.shuffle(filenames)

    # Create the files
    for path in filenames:
        path.touch()

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


def test_np_convert():
    float_data = np.linspace(0, 1, 16)
    int_data = np_convert(np.uint16, float_data)

    assert np.all(int_data == np.arange(0, np.iinfo(np.uint16).max + 1, np.iinfo(np.uint16).max // 15))
    assert np.all(np_convert(np.float32, int_data) == int_data.astype(np.float32))


def test_generate_tiff_write(tmp_path):
    micron_resolution = np.array([0.7, 0.7, 0.7])
    backprojection_offset = (55, 44, 77)
    compression = "zlib"
    temp_file = tmp_path.joinpath("foot.tiff")

    import tifffile as tf
    import json
    write_func = tf.imwrite

    tiff_write = generate_tiff_write(write_func, compression, micron_resolution, backprojection_offset)
    tiff_write(temp_file, np.arange(0, 64).reshape(8, 8))

    with tf.TiffFile(temp_file) as tif:
        print(tif.pages[0].tags)
        assert tif.pages[0].tags["ResolutionUnit"].value == tf.RESUNIT.CENTIMETER
        assert tif.pages[0].tags["Software"].value == "ouroboros"
        assert tif.pages[0].tags["Compression"].value == tf.COMPRESSION.ADOBE_DEFLATE
        assert tif.pages[0].tags["XResolution"].value == (4294967295, 300648)
        assert tif.pages[0].tags["YResolution"].value == (4294967295, 300648)
        json_metadata = json.loads(tif.pages[0].tags["ImageDescription"].value)
        assert json_metadata["spacing"] == 0.7
        assert json_metadata["unit"] == "um"
        assert json_metadata["backprojection_offset_min_xyz"] == [55, 44, 77]


def test_write_memmap_with_create(tmp_path):
    temp_file = tmp_path.joinpath("foot.tiff")
    indicies = (np.zeros((10), dtype=np.uint16), np.arange(0, 10, dtype=np.uint16))
    data = np.random.rand((10)) * 4
    shape = (10, 10)
    dtype = np.float32

    write_memmap_with_create(temp_file, indicies, data, shape, dtype)

    import tifffile as tf

    x = tf.imread(temp_file)
    assert np.allclose(x[indicies], data)
    assert np.all(np.nonzero(x)[0] == indicies[0]) and np.all(np.nonzero(x)[1] == indicies[1])

    second_indicies = (np.zeros((3), dtype=np.uint16), np.arange(5, 8, dtype=np.uint16))
    second_values = np.random.rand((3)) * 6

    write_memmap_with_create(temp_file, second_indicies, second_values, shape, dtype)

    assert np.all(np.nonzero(x)[0] == indicies[0]) and np.all(np.nonzero(x)[1] == indicies[1])

    x = tf.imread(temp_file)
    assert np.allclose(x[second_indicies], np.mean([data[5:8], second_values], axis=0))


def test_rewrite_by_dimension(tmp_path):
    writeable = np.zeros(10)
    writeable[2:7] = 1

    import tifffile as tf

    # Write basic files
    for i in range(2, 7):
        tf.imwrite(tmp_path.joinpath(f"{i:05}.tiff"), np.full((8, 8), i, dtype=np.float32))

    micron_resolution = np.array([0.7, 0.7, 0.7])
    backprojection_offset = (55, 44, 77)
    compression = "zlib"

    tiff_write = generate_tiff_write(imwrite, compression, micron_resolution, backprojection_offset)

    pool = rewrite_by_dimension(writeable, tiff_write, tmp_path)

    for writer in pool:
        writer.join()

    assert np.all(writeable[2:7] == 2)
    assert np.all(writeable[0:2] == 0)
    assert np.all(writeable[7:] == 0)

    for i in np.flatnonzero(writeable == 2):
        x = tf.imread(tmp_path.joinpath(f"{i:05}.tiff"))
        assert x.dtype == np.uint16


def test_rewrite_by_dimension_unthreaded(tmp_path):
    writeable = np.zeros(10)
    writeable[2:7] = 1

    import tifffile as tf

    # Write basic files
    for i in range(2, 7):
        tf.imwrite(tmp_path.joinpath(f"{i:05}.tiff"), np.full((8, 8), i, dtype=np.float32))

    micron_resolution = np.array([0.7, 0.7, 0.7])
    backprojection_offset = (55, 44, 77)
    compression = "zlib"

    tiff_write = generate_tiff_write(imwrite, compression, micron_resolution, backprojection_offset)

    pool = rewrite_by_dimension(writeable, tiff_write, tmp_path, use_threads=False)

    for writer in pool:
        writer.join()

    assert np.all(writeable[2:7] == 2)
    assert np.all(writeable[0:2] == 0)
    assert np.all(writeable[7:] == 0)

    for i in np.flatnonzero(writeable == 2):
        x = tf.imread(tmp_path.joinpath(f"{i:05}.tiff"))
        assert x.dtype == np.uint16
