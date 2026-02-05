#!/usr/bin/env python

if __name__ == "__main__":
    import argparse
    import json
    import pandas as pd
    from pathlib import Path

    from sxscatalog.utilities import consolidate_xyz_vectors

    parser = argparse.ArgumentParser(
        description="Compute the MAYA_catalog.json file from MAYAmetadata.pkl",
        epilog=(
            "Read the pandas dataframe of the pickle file, and "
            "arranges it so that it is similar to SXS catalog.json."
        ),
    )
    parser.add_argument(
        "filename",
        type=argparse.FileType("rb"),
        help="path to the MAYAmetadata.pkl file",
    )
    parser.add_argument(
        "--output",
        type=argparse.FileType("w"),
        default="MAYA_catalog.json",
        help="path to the output file (default: %(default)s).",
    )
    parser.add_argument(
        "--consolidate-xyz-vectors",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="if triples of <key>x <key>y <key>z should be consolidated "
        "into vectors (default: %(default)s)",
    )

    args = parser.parse_args()

    data = pd.read_pickle(args.filename)
    data_dict = data.to_dict(orient="index")

    if args.consolidate_xyz_vectors:
        data_dict = {k: consolidate_xyz_vectors(v) for k, v in data_dict.items()}

    json.dump(data_dict, args.output, indent=2, sort_keys=True)
