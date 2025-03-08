from .downloads import download_file
from .sxs_directories import (
    sxs_directory, read_config, write_config
)
from .sxs_identifiers import (
    sxs_identifier_regex, sxs_identifier_re,
    lev_regex, lev_re, lev_path_re,
    sxs_id_version_lev_regex, sxs_id_version_lev_re,
    sxs_id_version_lev_exact_regex, sxs_id_version_lev_exact_re,
    sxs_path_regex, sxs_path_re,
    sxs_id, sxs_id_and_version,
    lev_number, simulation_title, sxs_id_to_url,
)


def path_to_invenio(file_path):
    """Convert a file path to an invenio-compatible name"""
    import os
    return str(file_path).replace(os.path.sep, ":")


def invenio_to_path(file_name):
    """Convert an invenio-compatible name to a file path"""
    import os
    from pathlib import Path
    return Path(file_name.replace(":", os.path.sep))
