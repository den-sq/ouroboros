import argparse
from multiprocessing import freeze_support
import sys

from ouroboros.common.pipelines import backproject_pipeline, slice_pipeline
from ouroboros.helpers.models import pretty_json_output
from ouroboros.helpers.options import (
    DEFAULT_BACKPROJECT_OPTIONS,
    DEFAULT_SLICE_OPTIONS,
    BackprojectOptions,
    SliceOptions,
)


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
        "options",
        type=str,
        help="The path to the options json file.",
    )
    parser_backproject.add_argument(
        "--verbose",
        action="store_true",
        help="Output timing statistics for the calculations.",
    )

    # Create the parser for the sample-options command
    subparsers.add_parser(
        "sample-options",
        help="Export sample options files into the current folder.",
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
    print(f"Loading slice options from: {args.options}")
    slice_options = SliceOptions.load_from_json(args.options)

    if isinstance(slice_options, str):
        print("Exiting due to errors loading slice options.", file=sys.stderr)
        sys.exit(1)

    print("Slice options loaded successfully.")
    pipeline, input_data = slice_pipeline(slice_options, True)

    _, error = pipeline.process(input_data)

    if error:
        print(f"Pipeline Error: {error}", file=sys.stderr)

    if args.verbose:
        print("\nCalculation Statistics:\n")
        stat_dict = {stat.pop("pipeline"): stat for stat in pipeline.get_step_statistics()}
        print(pretty_json_output(stat_dict))


def handle_backproject(args):
    print(f"Loading backproject options from: {args.options}")
    backproject_options = BackprojectOptions.load_from_json(args.options)

    if isinstance(backproject_options, str):
        print("Exiting due to errors loading backproject options.", file=sys.stderr)
        sys.exit(1)

    print("Backproject options loaded successfully."
          f"Loading slice options from: {backproject_options.slice_options_path}")

    slice_options = SliceOptions.load_from_json(backproject_options.slice_options_path)

    if isinstance(slice_options, str):
        print("Exiting due to errors loading slice options file specified within backproject options"
              f"({backproject_options.slice_options_path}).", file=sys.stderr)
        sys.exit(1)

    print("Slice options loaded successfully.")
    pipeline, input_data = backproject_pipeline(backproject_options, slice_options, True)

    _, error = pipeline.process(input_data)

    if error:
        print(f"Pipeline Error: {error}", file=sys.stderr)

    if args.verbose:
        print("\nCalculation Statistics:\n")
        stat_dict = {stat.pop("pipeline"): stat for stat in pipeline.get_step_statistics()}
        # print(stat_dict)
        print(pretty_json_output(stat_dict))


def handle_sample_options():
    # Create sample options files
    sample_slice_options = DEFAULT_SLICE_OPTIONS
    sample_backproject_options = DEFAULT_BACKPROJECT_OPTIONS

    # Save the sample options files
    sample_slice_options.save_to_json("./sample-slice-options.json")
    sample_backproject_options.save_to_json("./sample-backproject-options.json")


if __name__ == "__main__":
    # Necessary to run multiprocessing in child processes
    freeze_support()

    main()
