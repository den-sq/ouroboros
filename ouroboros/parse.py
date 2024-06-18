import json
import numpy as np

ParseResult = tuple[dict, None | json.JSONDecodeError]

def parse_neuroglancer_json(json_path) -> ParseResult:
    """
    Open and parse a neuroglancer state JSON string and return a dictionary of the parsed data.

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
        with open(json_path) as f:
            json_string = f.read()

            parsed_json = json.loads(json_string)

            return (parsed_json, None)
    except json.JSONDecodeError as e:
        return ({}, f"An error occurred while parsing the given JSON file: {str(e)}")
    except Exception as e:
        return ({}, f"An error occurred while opening the given JSON file: {str(e)}")

def neuroglancer_config_to_annotation(config, use_numpy=True):
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

            result = [data["point"] for data in annotations if data["type"] == "point"]

            if use_numpy:
                return np.array(result)
            return result
        
    return np.array()