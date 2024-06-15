import json
import numpy as np

ParseResult = tuple[dict, None | json.JSONDecodeError]

def parse_neuroglancer_json(json_string) -> ParseResult:
    """
    Parse a neuroglancer state JSON string and return a dictionary of the parsed data.

    Parameters
    ----------
    json_string : str
        The JSON string to parse.

    Returns
    -------
    ParseResult
        A tuple containing the parsed JSON dictionary and an error if one occurred.
    """
    try:
        return (json.loads(json_string), None)
    except json.JSONDecodeError as e:
        return ({}, e)

def neuroglancer_config_to_annotation(config):
    """
    Extract the first annotation from a neuroglancer state JSON dictionary as a numpy array.
    
    Parameters
    ----------
    config : dict
        The neuroglancer state JSON dictionary.

    Returns
    -------
    numpy.ndarray
        The annotation as a numpy array.
    """
    # TODO: add try except here in case the json is invalid
    # or use pydantic to validate

    for layer in config["layers"]:
        if layer["type"] == "annotation":
            annotations = layer["annotations"]

            return np.array([data["point"] for data in annotations if data["type"] == "point"])
        
    return np.array()