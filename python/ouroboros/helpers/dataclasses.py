import json
from dataclasses import fields, is_dataclass
import numpy as np


def dataclass_with_json(cls):
    if not is_dataclass(cls):
        raise TypeError("must be applied to a dataclass type")

    cls.to_json = to_json
    cls.save_to_json = save_to_json
    cls.load_from_json = classmethod(load_from_json)
    cls.copy_values_from_other = copy_values_from_other
    cls.to_dict = to_dict
    cls.from_dict = classmethod(from_dict)

    return cls


def to_json(self):
    return json.dumps(self.to_dict())


def save_to_json(self, json_path):
    with open(json_path, "w") as f:
        json.dump(self.to_dict(), f)


@classmethod
def load_from_json(cls, json_path):
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found at {json_path}")
        return None
    except json.JSONDecodeError:
        print(f"File at {json_path} is not a valid JSON file")
        return None

    return cls.from_dict(data)


def copy_values_from_other(self, other):
    for field in fields(self):
        setattr(self, field.name, getattr(other, field.name))


def to_dict(self):
    result = {}
    for field in fields(self):
        value = getattr(self, field.name)
        if isinstance(value, np.ndarray):
            result[field.name] = value.tolist()
        elif hasattr(value, "to_dict"):
            result[field.name] = value.to_dict()
        else:
            result[field.name] = value
    return result


@classmethod
def from_dict(cls, data):
    init_args = {}
    for field in fields(cls):
        field_type = field.type
        value = data.get(field.name)
        if issubclass(field_type, np.ndarray):
            init_args[field.name] = np.array(value) if value is not None else None
        elif hasattr(field_type, "from_dict"):
            init_args[field.name] = (
                field_type.from_dict(value) if value is not None else None
            )
        else:
            init_args[field.name] = value
    return cls(**init_args)
