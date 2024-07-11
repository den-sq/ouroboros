import numpy as np

from pydantic import BaseModel
from ouroboros.helpers.dataclasses import dataclass_with_json
from ouroboros.helpers.options import SliceOptions


class LayerModel(BaseModel):
    type: str
    name: str


class AnnotationModel(BaseModel):
    point: list[float]
    type: str


class AnnotationLayerModel(LayerModel):
    annotations: list[AnnotationModel]
    type: str
    name: str


class SourceModel(BaseModel):
    url: str


class ImageLayerModel(LayerModel):
    source: str | SourceModel
    type: str
    name: str


@dataclass_with_json
class NeuroglancerJSONModel(BaseModel):
    layers: list[AnnotationLayerModel | ImageLayerModel | LayerModel]


Result = tuple[any, None] | tuple[None, str]

ParseResult = tuple[NeuroglancerJSONModel | None, None | str]


def parse_neuroglancer_json(json_path: str) -> ParseResult:
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

    neuroglancer_json_or_error = NeuroglancerJSONModel.load_from_json(json_path)

    if isinstance(neuroglancer_json_or_error, str):
        return None, neuroglancer_json_or_error

    return neuroglancer_json_or_error, None


def neuroglancer_config_to_annotation(
    config: NeuroglancerJSONModel, options: SliceOptions
) -> Result:
    """
    Extract the first annotation from a neuroglancer state JSON dictionary as a numpy array.

    Parameters
    ----------
    config : NeuroglancerJSONModel
        The neuroglancer state JSON object.
    options : SliceOptions
        The options object containing the annotation layer name.

    Returns
    -------
    Result
        A tuple containing the annotation points and an error if one occurred.
    """

    try:
        for layer in config.layers:
            if (
                layer.type == "annotation"
                and layer.name == options.neuroglancer_annotation_layer
            ):
                annotations = layer.annotations

                return (
                    np.array(
                        [data.point for data in annotations if data.type == "point"]
                    ),
                    None,
                )
    except BaseException as e:
        return None, f"Error extracting annotations: {e}"

    return None, "The selected annotation layer was not found in the file."


def neuroglancer_config_to_source(
    config: NeuroglancerJSONModel, options: SliceOptions
) -> Result:
    """
    Extract the source URL from a neuroglancer state JSON dictionary.

    Parameters
    ----------
    config : NeuroglancerJSONModel
        The neuroglancer state JSON object.
    options : SliceOptions
        The options object containing the annotation layer name.

    Returns
    -------
    Result
        A tuple containing the source URL and an error if one occurred.
    """

    try:
        for layer in config.layers:
            if layer.type == "image" and layer.name == options.neuroglancer_image_layer:
                if isinstance(layer.source, str):
                    return layer.source, None
                elif isinstance(layer.source, SourceModel):
                    return layer.source.url, None
                else:
                    return None, "Invalid source format in the file."
    except BaseException as e:
        return None, f"Error extracting source URL: {e}"

    return None, "The selected image layer was not found in the file."
