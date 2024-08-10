import pytest
from pydantic import ValidationError
from ouroboros.helpers.bounding_boxes import BoundingBoxParams
from ouroboros.helpers.options import CommonOptions, SliceOptions, BackprojectOptions


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
        output_file_folder="./output/",
        output_file_name="output",
        straightened_volume_path="./volume.tif",
        slice_options_path="./slice-options.json",
    )
    json_path = tmp_path / "backproject_options.json"
    options.save_to_json(json_path)
    assert json_path.exists()
