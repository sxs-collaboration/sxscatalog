# SPDX-FileCopyrightText: 2025-present Mike Boyle <michael.oliver.boyle@gmail.com>
#
# SPDX-License-Identifier: MIT

from .__about__ import __version__

from . import utilities
from . import metadata
from . import simulations


def load(location, download=None, **kwargs):
    from .simulations import Simulations

    if location == "simulations":
        return Simulations.load(
            download=download,
            tag=kwargs.get("tag", ""),
            local=kwargs.get("local", False),
            annex_dir=kwargs.get("annex_dir", None),
            output_file=kwargs.get("output_file", None),
            compute_md5=kwargs.get("compute_md5", False),
            show_progress=kwargs.get("show_progress", False)
        )

    elif location == "dataframe":
        return load("simulations", download=download, **kwargs).dataframe

    else:
        raise ValueError(
            f"\nUnknown location '{location}'. "
            "\nNote that this is `sxscatalog.load`, not `sxs.load`;"
            " perhaps you meant to use the latter."
        )
