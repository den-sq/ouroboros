from pydantic import BaseModel, ValidationError


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
    with open(json_path, "w") as f:
        f.write(self.to_json())


@classmethod
def load_from_json(cls: BaseModel, json_path: str):
    try:
        with open(json_path, "r") as f:
            result = cls.from_json(f.read())
            return result
    except ValidationError as e:
        err = f"Error loading {cls.__name__} from JSON: {e}"
        print(err)
        return err
    except FileNotFoundError:
        err = f"File not found at {json_path}"
        print(err)
        return err
    except BaseException:
        err = f"File at {json_path} is not a valid JSON file"
        print(err)
        return err


def copy_values_from_other(self: BaseModel, other: BaseModel):
    for field in self.model_fields.keys():
        setattr(self, field, getattr(other, field))
