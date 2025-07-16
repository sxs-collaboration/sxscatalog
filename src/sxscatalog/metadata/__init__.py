"""Interface to SXS metadata files"""

from .metadata import Metadata
from .metric import MetadataMetric

formats = {
    None: Metadata,
    "": Metadata,
    "metadata": Metadata,
}


def metadata_version(metadata):
    """Guess the version from the metadata keys"""

    # Define the keys that are present in each version
    keys_v1 = {
        "relaxed_mass1",
    }

    keys_v2 = {
        "metadata_version",
        "number_of_orbits",
    }

    keys_v3 = {
        "internal_changelog",
        "internal_minor_version",
        "metadata_content_revision",
        "metadata_format_revision",
        "number_of_orbits_from_reference_time",
        "number_of_orbits_from_start",
        #"t_relaxed_algorithm",
    }

    # Get the keys from the simulation metadata
    metadata_keys = set(metadata.keys())

    # Check for the presence of keys to determine the version
    if keys_v3.issubset(metadata_keys):
        return "v3.0"
    elif keys_v2.issubset(metadata_keys):
        return "v2.0"
    elif keys_v1.issubset(metadata_keys):
        return "v1.1"
    else:
        return ""
