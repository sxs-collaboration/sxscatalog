#!/usr/bin/env python


def convert_maya_pkl_to_json(filename, output="MAYA_catalog.json"):
    """Convert MAYA metadata pickle file to a json file.
    Parameters
    ==========
    filename : str or Path
        Relative or absolute path to the input pickle file.
    output : str or Path
        Path to the output json file.
    """
    import pandas as pd
    from pathlib import Path
    import json

    # Make sure the file exists
    path = Path(filename).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Could not find {path}")

    data = pd.read_pickle(path)
    data_dict = data.to_dict(orient="index")

    vectors = {"a1": ["a1x", "a1y", "a1z"], "a2": ["a2x", "a2y", "a2z"]}

    for values in data_dict.values():
        for spin_label, components in vectors.items():
            values[spin_label] = [values.pop(c) for c in components]

    with open(output, "w") as f:
        json.dump(data_dict, f)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute the MAYA_catalog.json file from MAYAmetadata.pkl",
        epilog=(
            "This simply reads the pandas dataframe of the pickle file, and arranges it so that it is similar to SXS catalog.json."
        ),
    )
    parser.add_argument(
        "filename",
        help="path to the MAYAmetadata.pkl file",
    )
    parser.add_argument(
        "--output",
        default="MAYA_catalog.json",
        help="path to the output file.",
    )
    args = parser.parse_args()

    convert_maya_pkl_to_json(
        args.filename,
        output=args.output,
    )
