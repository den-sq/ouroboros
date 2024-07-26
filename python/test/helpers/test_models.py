from pydantic import BaseModel
from ouroboros.helpers.models import (
    model_with_json,
)


@model_with_json
class SampleModel(BaseModel):
    field1: int
    field2: str


def test_model_with_json(tmp_path):
    # Create an instance of SampleModel
    sample = SampleModel(field1=123, field2="test")

    # Test to_dict method
    assert sample.to_dict() == {"field1": 123, "field2": "test"}

    # Test from_dict method
    new_sample = SampleModel.from_dict({"field1": 456, "field2": "new_test"})
    assert new_sample.field1 == 456
    assert new_sample.field2 == "new_test"

    # Test save_to_json and load_from_json methods
    json_path = tmp_path / "sample_model.json"
    sample.save_to_json(json_path)
    loaded_sample = SampleModel.load_from_json(json_path)
    assert loaded_sample.field1 == 123
    assert loaded_sample.field2 == "test"

    # Test copy_values_from_other method
    another_sample = SampleModel(field1=789, field2="another_test")
    sample.copy_values_from_other(another_sample)
    assert sample.field1 == 789
    assert sample.field2 == "another_test"


def test_model_with_json_invalid_class():
    class InvalidClass:
        pass

    try:
        model_with_json(InvalidClass)
    except TypeError as e:
        assert str(e) == "model_with_json must be applied to a BaseModel type"
    else:
        assert False


def test_invalid_load_json(tmp_path):
    json_path = tmp_path / "invalid.json"
    with open(json_path, "w") as f:
        f.write("invalid json")

    loaded_sample = SampleModel.load_from_json(json_path)
    assert loaded_sample.startswith("Error loading SampleModel from JSON")


def test_file_not_found(tmp_path):
    json_path = tmp_path / "file_not_found.json"

    loaded_sample = SampleModel.load_from_json(json_path)
    assert loaded_sample.startswith("File not found at")
