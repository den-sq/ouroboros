import json
from pydantic import BaseModel, ValidationError
import sys


def pretty_json_output(obj: object) -> str:
    return json.dumps(obj, indent=4)


def model_with_json(cls):
    """
    Add methods to the given class to serialize and deserialize the class to and from
    a dictionary, JSON string, and JSON file.

    Parameters
    ----------
    cls : BaseModel
        The class to add the methods to.

    Returns
    -------
    BaseModel
        The class with the added methods.
    """

    if not issubclass(cls, BaseModel):
        raise TypeError("model_with_json must be applied to a BaseModel type")

    cls.to_dict = cls.model_dump
    cls.from_dict = classmethod(cls.model_validate)
    cls.to_json = cls.model_dump_json
    cls.from_json = classmethod(cls.model_validate_json)
    cls.save_to_json = save_to_json
    cls.load_from_json = classmethod(load_from_json)
    cls.copy_values_from_other = copy_values_from_other

    return cls


def save_to_json(self: BaseModel, json_path: str):
    # Also specify encoding here for consistency
    with open(json_path, "w", encoding='utf-8') as f:
        # Add indent here for consistency? Or handle in Pydantic model
        f.write(self.to_json(indent=4))


@classmethod
def load_from_json(cls: type[BaseModel], json_path: str) -> BaseModel | None:
    """Loads a Pydantic model from a JSON file.

    Args:
        cls: The Pydantic model class.
        json_path: Path to the JSON file.

    Returns:
        An instance of the model, or None if loading fails.
    """
    try:
        # Explicitly use utf-8 encoding
        with open(json_path, "r", encoding='utf-8') as f:
            # Use model_validate_json directly for better error context from Pydantic
            result = cls.model_validate_json(f.read())
            return result
    except FileNotFoundError:
        print(f"Error: File not found at {json_path}", file=sys.stderr)
        return None
    except (ValidationError, json.JSONDecodeError) as e:
        # Catch specific Pydantic validation errors and JSON syntax errors
        print(f"Error loading {cls.__name__} from JSON file '{json_path}':\n{e}", file=sys.stderr)
        return None
    except Exception as e:
        # Catch other potential errors like permission denied, unicode issues etc.
        print(f"Error reading or parsing file '{json_path}': {e}", file=sys.stderr)
        return None


def copy_values_from_other(self: BaseModel, other: BaseModel):
    for field in self.model_fields.keys():
        setattr(self, field, getattr(other, field))
