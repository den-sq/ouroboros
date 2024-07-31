import pytest
from pydantic import ValidationError
from ouroboros.helpers.bounding_boxes import BoundingBoxParams
from ouroboros.helpers.options import CommonOptions, SliceOptions, BackprojectOptions


def test_common_options_defaults():
    options = CommonOptions(
        slice_width=100,
        slice_height=100,
        output_file_folder="./output/",
        output_file_name="output",
    )
    assert options.slice_width == 100
    assert options.slice_height == 100
    assert options.output_file_folder == "./output/"
    assert options.output_file_name == "output"
    assert options.dist_between_slices == 1
    assert not options.flush_cache
    assert not options.connect_start_and_end
    assert options.make_single_file
    assert options.max_ram_gb == 0


def test_slice_options_defaults():
    options = SliceOptions(
        neuroglancer_json="./neuroglancer.json",
        slice_width=100,
        slice_height=100,
        output_file_folder="./output/",
        output_file_name="output",
    )
    assert options.neuroglancer_json == "./neuroglancer.json"
    assert options.neuroglancer_image_layer == ""
    assert options.neuroglancer_annotation_layer == ""
    assert options.slice_width == 100
    assert options.slice_height == 100
    assert options.output_file_folder == "./output/"
    assert options.output_file_name == "output"
    assert options.dist_between_slices == 1
    assert not options.flush_cache
    assert not options.connect_start_and_end
    assert options.make_single_file
    assert options.max_ram_gb == 0


def test_backproject_options_defaults():
    options = BackprojectOptions(
        slice_width=100,
        slice_height=100,
        output_file_folder="./output/",
        output_file_name="output",
        straightened_volume_path="./volume.tif",
        config_path="./config.json",
    )
    assert options.slice_width == 100
    assert options.slice_height == 100
    assert options.output_file_folder == "./output/"
    assert options.output_file_name == "output"
    assert options.straightened_volume_path == "./volume.tif"
    assert options.config_path == "./config.json"
    assert options.backproject_min_bounding_box
    assert not options.make_backprojection_binary
    assert options.backprojection_compression == "zlib"


def test_common_options_validation():
    with pytest.raises(ValidationError):
        CommonOptions()


def test_slice_options_validation():
    with pytest.raises(ValidationError):
        SliceOptions(
            slice_width=100,
            slice_height=-1,
            output_file_folder="./output/",
            output_file_name="output",
        )


def test_backproject_options_validation():
    with pytest.raises(ValidationError):
        BackprojectOptions(
            slice_width=100,
            slice_height=100,
            output_file_folder="./output/",
            output_file_name="output",
        )


def test_common_options_to_json(tmp_path):
    options = CommonOptions(
        slice_width=100,
        slice_height=100,
        output_file_folder="./output/",
        output_file_name="output",
    )
    json_path = tmp_path / "common_options.json"
    options.save_to_json(json_path)
    assert json_path.exists()


def test_slice_options_to_json(tmp_path):
    options = SliceOptions(
        slice_width=100,
        slice_height=100,
        output_file_folder="./output/",
        output_file_name="output",
        neuroglancer_json="./neuroglancer.json",
    )
    json_path = tmp_path / "slice_options.json"
    options.save_to_json(json_path)
    assert json_path.exists()


def test_slice_options_from_json():
    options = SliceOptions(
        slice_width=100,
        slice_height=100,
        output_file_folder="./output/",
        output_file_name="output",
        neuroglancer_json="./neuroglancer.json",
        bounding_box_params=BoundingBoxParams(max_depth=10, target_slices_per_box=120),
    )
    json_output = options.to_json()
    loaded_options = SliceOptions.from_json(json_output)

    assert isinstance(loaded_options.bounding_box_params, BoundingBoxParams)
    assert not isinstance(loaded_options, str)
    assert loaded_options == options


def test_backproject_options_to_json(tmp_path):
    options = BackprojectOptions(
        slice_width=100,
        slice_height=100,
        output_file_folder="./output/",
        output_file_name="output",
        straightened_volume_path="./volume.tif",
        config_path="./config.json",
    )
    json_path = tmp_path / "backproject_options.json"
    options.save_to_json(json_path)
    assert json_path.exists()
