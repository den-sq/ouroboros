from pathlib import Path
from ouroboros.helpers.parse import (
    NeuroglancerJSONModel,
    parse_neuroglancer_json,
    neuroglancer_config_to_annotation,
    neuroglancer_config_to_source,
)
from test.sample_data import generate_sample_neuroglancer_json


def test_parse_neuroglancer_json(tmp_path):
    # Generate a sample neuroglancer JSON file
    json_path = generate_sample_neuroglancer_json(tmp_path)

    # Parse the generated JSON file
    parsed_data, error = parse_neuroglancer_json(json_path)

    # Assert that there is no error
    assert error is None

    # Assert that the parsed data is a dictionary
    assert isinstance(parsed_data, NeuroglancerJSONModel)

    # Assert that the parsed data contains expected keys
    data = parsed_data.model_dump()

    assert "layers" in data
    assert len(data["layers"]) == 3
    assert data["layers"][0]["type"] == "annotation"
    assert data["layers"][1]["type"] == "image"
    assert data["layers"][2]["type"] == "image"

    # Extract the annotation layer
    annotations, error = neuroglancer_config_to_annotation(parsed_data, "annotations")

    # Assert that there is no error
    assert error is None

    # Assert that the annotations are a numpy array
    assert annotations is not None
    assert annotations.shape == (100, 3)

    # Extract the image layer
    source, error = neuroglancer_config_to_source(parsed_data, "image_layer")

    # Assert that there is no error
    assert error is None

    # Assert that the source is a string
    assert source is not None
    assert isinstance(source, str)

    # Clean up
    Path(json_path).unlink()
