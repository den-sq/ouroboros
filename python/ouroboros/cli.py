from multiprocessing import freeze_support

import argparse

from ouroboros.helpers.config import Config
from ouroboros.pipeline import (
    Pipeline,
    PipelineInput,
    ParseJSONPipelineStep,
    SlicesGeometryPipelineStep,
    VolumeCachePipelineStep,
    SaveParallelPipelineStep,
    BackprojectPipelineStep,
    SaveConfigPipelineStep,
    LoadConfigPipelineStep,
)
import json


def main():
    # Create a cli parser with the built-in library argparse
    parser = argparse.ArgumentParser(
        prog="Ouroboros CLI",
        description="A CLI for extracting ROIs from cloud-hosted 3D volumes for segmentation.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Create the parser for the slice command
    parser_slice = subparsers.add_parser(
        "slice", help="Slice the original volume along a path and save to a tiff file."
    )
    parser_slice.add_argument(
        "neuroglancer_json",
        type=str,
        help="The path to the neuroglancer json file with the source and annotation path.",
    )
    parser_slice.add_argument(
        "options",
        type=str,
        help="The path to the options json file.",
    )
    parser_slice.add_argument(
        "--verbose",
        action="store_true",
        help="Output timing statistics for the calculations.",
    )

    # Create the parser for the backproject command
    parser_backproject = subparsers.add_parser(
        "backproject",
        help="Project the straightened slices back into the space of the original volume.",
    )
    parser_backproject.add_argument(
        "straightened_volume",
        type=str,
        help="The tiff file representing the straightened (possibly segmented) volume.",
    )
    parser_backproject.add_argument(
        "config",
        type=str,
        help="The configuration file exported from the slicing process.",
    )
    parser_backproject.add_argument(
        "--options",
        type=str,
        help="By default, this command uses the config file to find options. Override those options with a path to another options json file.",
        default=None,
    )
    parser_backproject.add_argument(
        "--verbose",
        action="store_true",
        help="Output timing statistics for the calculations.",
    )

    # Create the parser for the sample-options command
    subparsers.add_parser(
        "sample-options",
        help="Export a sample options file into the current folder.",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Dispatch to the appropriate function
    match args.command:
        case "slice":
            handle_slice(args)
        case "backproject":
            handle_backproject(args)
        case "sample-options":
            handle_sample_options()
        case _:
            parser.print_help()


def handle_slice(args):
    config = Config.load_from_json(args.options)

    pipeline = Pipeline(
        [
            ParseJSONPipelineStep(),
            SlicesGeometryPipelineStep(),
            VolumeCachePipelineStep(),
            SaveParallelPipelineStep().with_progress_bar(),
            SaveConfigPipelineStep(),
        ]
    )

    input_data = PipelineInput(config=config, json_path=args.neuroglancer_json)

    _, error = pipeline.process(input_data)

    if error:
        print(error)

    if args.verbose:
        print("\nCalculation Statistics:\n")

        for stat in pipeline.get_step_statistics():
            print(json.dumps(stat, indent=4), "\n")


def handle_backproject(args):
    config = None

    if args.options:
        config = Config.load_from_json(args.options)

    pipeline = Pipeline(
        [
            LoadConfigPipelineStep()
            .with_custom_output_file_path(args.straightened_volume)
            .with_custom_options(config),
            BackprojectPipelineStep().with_progress_bar(),
            SaveConfigPipelineStep(),
        ]
    )

    input_data = PipelineInput(config_file_path=args.config)

    _, error = pipeline.process(input_data)

    if error:
        print(error)

    if args.verbose:
        print("\nCalculation Statistics:\n")

        for stat in pipeline.get_step_statistics():
            print(json.dumps(stat, indent=4), "\n")


def handle_sample_options():
    sample_options = Config(100, 100, "./output/", "sample")

    sample_options.save_to_json("./sample-options.json")


if __name__ == "__main__":
    # Necessary to run multiprocessing in child processes
    freeze_support()

    main()
