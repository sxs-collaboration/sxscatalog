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
from .files import (
    md5checksum, lock_file_manager, find_simulation_directories, find_files
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

def consolidate_xyz_vectors(data):
    """Find instances of key triples <key>x, <key>y, <key>z and consolidate into
    vectors named <key>.  If <key> ends with a dash (-) or underscore (_), the
    trailing dash/underscore will be stripped. The argument to this function is
    modified and returned.

    """

    names = []

    for k in data:
        if k[-1] == 'z':
            base = k[:-1]
            if (((base + 'x') in data) and
                ((base + 'y') in data)):
                names.append(base)

    for name in names:
        vec = [data.pop(name + 'x'),
               data.pop(name + 'y'),
               data.pop(name + 'z')]

        if name[-1] in ['-', '_']:
            name = name[:-1]

        data[name] = vec

    return data
