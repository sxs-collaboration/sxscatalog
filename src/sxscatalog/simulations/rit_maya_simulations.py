"""Container interface to the RIT and MAYA catalogs"""

import collections
import numpy as np
import pandas as pd
import requests

from ..utilities.string_converters import *

from .simulations import (
    Simulations,
    valid_vector,
    three_vector_dataframe,
    get,
)

# A helper function we need below
def promote_z_3vec(x):
    try:
        v = np.array([0., 0., float(x)])
    except:
        v = np.nan
    return v

class RITSimulations(Simulations):
    """Interface to the catalog of RIT simulations

    Creation
    --------
    You probably don't need to create this object yourself.  The
    easiest way to create this object is just to use the `sxs.load`
    function:

    ```python
    import sxs

    simulations = sxs.load("RITsimulations")
    ```

    """
    branches_url = "https://api.github.com/repos/sxs-collaboration/sxscatalogdata/branches"
    url = "https://raw.githubusercontent.com/sxs-collaboration/sxscatalogdata/refs/heads/{tag}/RIT_catalog.json"

    def __init__(self, sims):
        """Initialize the RITSimulations dictionary

        Note that the constructor is not generally useful from outside
        this class.  See `RITSimulations.load` for a more useful
        initialization function, or simply call
        `sxs.load("RITsimulations")`.

        """
        from ..metadata import Metadata
        # Note we really want the super of Simulations here,
        # not the super of RITSimulations!
        super(Simulations, self).__init__(
            (k, Metadata(sims[k])) for k in sorted(sims)
        )

    @classmethod
    def get_latest_release(cls):
        """Retrieve the most-recently published release of the catalog from github"""
        import os
        import requests
        from packaging.version import Version

        session = requests.Session()
        session.headers.update({"User-Agent": "curl/8.18.0"})
        if cls.branches_url.startswith("https://api.github.com/"):
            if (token := os.getenv("GITHUB_TOKEN")):
                session.headers.update({"Authorization": f"token {token}"})
        branches_response = session.get(cls.branches_url)
        branches_response.raise_for_status()
        branches_data = filter(lambda b: b["name"].startswith("RITv"),
                               branches_response.json())
        latest_release = max(branches_data,
                             key=lambda b: Version(b["name"].removeprefix("RITv")))
        return latest_release

    @classmethod
    def local(cls, *args):
        """Override the base class local() function, but we don't know how to do
        this for the RIT catalog."""
        raise NotImplementedError("TODO")

    @classmethod
    def load(
        cls,
        download=None, *,
        tag="",
        ignore_cached=False,
    ):  # Make sure to pass through any parameters from `load` and to `local`
        """Load the catalog of RIT simulations

        TODO documentation

        Parameters
        ----------
        download : {None, bool}, optional
            If False, this function will look for the simulations in
            the cache and raise an error if it is not found.  If
            True, this function will download the simulations and
            raise an error if the download fails.  If None (the
            default), it will try to download the file, warn but fall
            back to the cache if that fails, and only raise an error
            if the simulations is not found in the cache.  Note that
            this ignores the sxs configuration file entirely.

        Keyword-only Parameters
        -----------------------
        tag : str, optional
            The branch version extension of the simulations file to load.
            If not provided, the latest version will be used.
        ignore_cached : bool, optional
            If True, this function will ignore the cached version of
            the simulations attached to this class, and reload the
            simulations as if the cache did not exist.

        See Also
        --------
        sxs.sxs_directory : Locate cache directory Simulations.reload

        """
        if hasattr(cls, "_simulations") and not ignore_cached:
            return cls._simulations

        import json
        import zipfile
        import warnings
        from packaging.version import Version
        from ..utilities import sxs_directory, read_config, download_file

        progress = read_config("download_progress", True)

        if download is None:
            download = True

        if not tag:
            if download is not False:
                latest_release = cls.get_latest_release()
                tag = latest_release["name"]
                print(
                    f"Loading RIT simulations using latest tag '{tag}'."
                )
            else:
                # Files will be named RITsimulations_RITvXXXX.bz2
                tags = [
                    Version(f.stem.split("_")[-1].removeprefix("RITv"))
                    for f in sxs_directory("cache").glob("RITsimulations_*.bz2")
                ]
                if tags:
                    tag = f"RITv{max(tags)}"
                    warning = (
                        f"\nDownloads were turned off, so we are using the latest cached"
                        f"\nsimulations file, tagged {tag}, which may be out of date."
                    )
                    warnings.warn(warning)
                else:
                    raise ValueError(f"No simulations files found in the cache and {download=} was passed")

        # Normalize the tag to "RITv" followed by a normalized Version
        tag = tag.removeprefix("RIT") if tag.startswith("RIT") else tag
        tag = tag[1:] if tag.startswith("v") else tag
        tag = f"RITv{Version(tag)}"

        cache_path = sxs_directory("cache") / f"RITsimulations_{tag}.bz2"

        if not cache_path.exists():
            if download is False:  # Test if it literally *is* False, rather than just casts to False
                raise ValueError(f"Simulations not found in '{cache_path}' and downloading was turned off")
            else:
                # 1. Download the full json file (zipped in flight, but auto-decompressed on arrival)
                # 2. Zip to a temporary file (using bzip2, which is better than the in-flight compression)
                # 3. Replace the original simulations.zip with the temporary zip file
                # 4. Remove the full json file
                # 5. Make sure the temporary zip file is gone too
                temp_json = cache_path.with_suffix(".temp.json")
                temp_zip = cache_path.with_suffix(".temp.bz2")
                try:
                    download_file(cls.url.format(tag=tag), temp_json, progress=progress, if_newer=False)
                except Exception as e:
                    raise RuntimeError(
                        f"\nFailed to download '{cls.url.format(tag=tag)}'."
                        f"\nMaybe {tag=} does not exist?"
                    ) from e
                else:
                    if temp_json.exists():
                        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_BZIP2) as simulations_zip:
                            simulations_zip.write(temp_json, arcname="RITsimulations.json")
                        temp_zip.replace(cache_path)
                finally:
                    temp_json.unlink(missing_ok=True)
                    temp_zip.unlink(missing_ok=True)

        if not cache_path.exists():
            raise ValueError(f"Simulations not found in '{cache_path}' for unknown reasons")

        try:
            with zipfile.ZipFile(cache_path, "r") as simulations_zip:
                try:
                    with simulations_zip.open("RITsimulations.json") as simulations_json:
                        try:
                            simulations = json.load(simulations_json)
                        except Exception as e:
                            raise ValueError(f"Failed to parse 'RITsimulations.json' in '{cache_path}'") from e
                except Exception as e:
                    raise ValueError(f"Failed to open 'RITsimulations.json' in '{cache_path}'") from e
        except Exception as e:
            raise ValueError(f"Failed to open '{cache_path}' as a ZIP file") from e

        sims = cls(simulations)
        sims.__file__ = str(cache_path)
        sims.tag = tag

        if not ignore_cached:
            cls._simulations = sims
        return sims

    @property
    def dataframe(self):
        """Create pandas.DataFrame with metadata for all simulations

        NOTE: You might prefer to load this object directly with
        `sxs.load("dataframe")` instead of using this method.  The
        benefit to that is that `load` accepts all the same options as
        `Simulations.load`, so you can load a specific tag, local
        simulations, etc.

        The `pandas` package is the standard Python interface for
        heterogeneous data tables, like the one we have here.  This
        interface allows for more convenient slicing and querying of
        data than the list of `dict`s provided by the `Simulations`
        object.

        This can also be a more convenient way to access the metadata
        because the raw metadata has missing keys and mixed formats.
        Iif a key is missing from the metadata for a particular key,
        the dataframe will just have a `NaN` in that entry, rather
        than raising an exception.  Other keys may have unexpected
        entries — such as the `"reference_eccentricity"` field, which
        is *usually* a float but may be a string like "<0.0001" if the
        eccentricity is not known precisely, but is only bounded.  The
        dataframe introduces a new column called
        `"reference_eccentricity_bound"` that is always a float giving
        an upper bound on the eccentricity.

        See the `pandas` documentation for more information on how to
        use the resulting dataframe, or the `Simulations` tutorial for
        examples.

        """
        import numpy as np
        import pandas as pd

        if hasattr(self, "_dataframe"):
            return self._dataframe

        simulations = pd.DataFrame.from_dict(self, orient="index")

        # Convert just-z-components to 3-vectors
        for col in [
            "relaxed_chi1",
            "relaxed_chi2",
            "initial_bh_chi1",
            "initial_bh_chi2",
        ]:
            simulations[col] = simulations[col].fillna(
                simulations[col + "z"].map(promote_z_3vec)
            )

        sims_df = pd.DataFrame(pd.concat((
            get(simulations, "relaxed_mass_ratio_1_over_2", floater),
            get(simulations, "eccentricity", floater),
            get(simulations, "relaxed_time", floater),
            three_vector_dataframe(simulations, "relaxed_chi1"),
            three_vector_dataframe(simulations, "relaxed_chi2"),
            three_vector_dataframe(simulations, "relaxed_LNhat"),
            three_vector_dataframe(simulations, "relaxed_nhat"),
            get(simulations, "freq_start_22", floater),
            get(simulations, "freq_start_22_Hz_1Msun", floater),
            get(simulations, "relaxed_mass1", floater),
            get(simulations, "relaxed_mass2", floater),
            get(simulations, "relaxed_total_mass", floater),
            get(simulations, "peak_ampl_22", floater),
            get(simulations, "peak_omega_22", floater),
            get(simulations, "peak_luminosity_ergs_per_sec", floater),
            get(simulations, "final_mass", floater),
            get(simulations, "final_chi", floater),
            get(simulations, "final_kick", floater),
            get(simulations, "initial_data_type", "").astype("category"),
            get(simulations, "initial_orbital_angular_momentum", floater),
            get(simulations, "initial_separation", floater),
            get(simulations, "initial_ADM_energy", floater),
            three_vector_dataframe(simulations, "initial_ADM_angular_momentum"),
            get(simulations, "initial_mass1", floater),
            get(simulations, "initial_mass2", floater),
            get(simulations, "initial_total_mass", floater),
            three_vector_dataframe(simulations, "initial_bh_chi1"),
            three_vector_dataframe(simulations, "initial_bh_chi2"),
            get(simulations, "metadata_url", ""),
            get(simulations, "extrap_strain_url", ""),
            get(simulations, "extrap_psi4_url", ""),
            get(simulations, "catalog_tag", ""),
            get(simulations, "id_tag", ""),
            get(simulations, "resolution_tag", ""),
            get(simulations, "run_name", ""),
            get(simulations, "number_of_orbits", floater),
            get(simulations, "comments", []),
            get(simulations, "cfl", floater),
            get(simulations, "fd_order", floater),
            get(simulations, "eccentricity_measurement_method", ""),
            get(simulations, "evolution_system", ""),
        ), axis=1))

        # If `tag` is present, add it as an attribute
        if hasattr(self, "tag"):
            sims_df.tag = self.tag

        # See also `sxs.metadata.metadata._backwards_compatibility`;
        # it's probably a good idea to duplicate whatever is included
        # here in that function, just to make sure nothing slips
        # through the cracks.
        # ... anything?

        # We have ignored the following fields present in the
        # RITsimulations.json file (as of 2026-03-25), listed here with
        # the number of non-null entries:
        #
        # Msun                              824
        # authors_emails                   1881
        # code                             1881
        # code_bibtex_keys                 1881
        # data_type                        1881
        # dissipation_order                1881
        # eccentricity_bibtex_keys         1881
        # evolution_gauge                  1881
        # extrapolation_bibtex_keys        1881
        # initial_data_bibtex_keys         1881
        # number_of_cycles_22              1057
        # quasicircular_bibtex_keys        1881
        # simulation_bibtex_keys           1881
        # system_type                      1881

        self._dataframe = sims_df
        return sims_df

    table = dataframe

class MAYASimulations(Simulations):
    """Interface to the catalog of MAYA simulations

    Creation
    --------
    You probably don't need to create this object yourself.  The
    easiest way to create this object is just to use the `sxs.load`
    function:

    ```python
    import sxs

    simulations = sxs.load("MAYAsimulations")
    ```

    """
    branches_url = "https://api.github.com/repos/sxs-collaboration/sxscatalogdata/branches"
    url = "https://raw.githubusercontent.com/sxs-collaboration/sxscatalogdata/refs/heads/{tag}/MAYA_catalog.json"

    def __init__(self, sims):
        """Initialize the MAYASimulations dictionary

        Note that the constructor is not generally useful from outside
        this class.  See `MAYASimulations.load` for a more useful
        initialization function, or simply call
        `sxs.load("MAYAsimulations")`.

        """
        from ..metadata import Metadata
        # Note we really want the super of Simulations here,
        # not the super of MAYASimulations!
        super(Simulations, self).__init__(
            (k, Metadata(sims[k])) for k in sorted(sims)
        )

    @classmethod
    def get_latest_release(cls):
        """Retrieve the most-recently published release of the catalog from github"""
        import os
        import requests
        from packaging.version import Version

        session = requests.Session()
        session.headers.update({"User-Agent": "curl/8.18.0"})
        if cls.branches_url.startswith("https://api.github.com/"):
            if (token := os.getenv("GITHUB_TOKEN")):
                session.headers.update({"Authorization": f"token {token}"})
        branches_response = session.get(cls.branches_url)
        branches_response.raise_for_status()
        branches_data = filter(lambda b: b["name"].startswith("MAYAv"),
                               branches_response.json())
        latest_release = max(branches_data,
                             key=lambda b: Version(b["name"].removeprefix("MAYAv")))
        return latest_release

    @classmethod
    def local(cls, *args):
        """Override the base class local() function, but we don't know how to do
        this for the MAYA catalog."""
        raise NotImplementedError("TODO")

    @classmethod
    def load(
        cls,
        download=None, *,
        tag="",
        ignore_cached=False,
    ):  # Make sure to pass through any parameters from `load` and to `local`
        """Load the catalog of MAYA simulations

        TODO documentation

        Parameters
        ----------
        download : {None, bool}, optional
            If False, this function will look for the simulations in
            the cache and raise an error if it is not found.  If
            True, this function will download the simulations and
            raise an error if the download fails.  If None (the
            default), it will try to download the file, warn but fall
            back to the cache if that fails, and only raise an error
            if the simulations is not found in the cache.  Note that
            this ignores the sxs configuration file entirely.

        Keyword-only Parameters
        -----------------------
        tag : str, optional
            The branch version extension of the simulations file to load.
            If not provided, the latest version will be used.
        ignore_cached : bool, optional
            If True, this function will ignore the cached version of
            the simulations attached to this class, and reload the
            simulations as if the cache did not exist.

        See Also
        --------
        sxs.sxs_directory : Locate cache directory Simulations.reload

        """
        if hasattr(cls, "_simulations") and not ignore_cached:
            return cls._simulations

        import json
        import zipfile
        import warnings
        from packaging.version import Version
        from ..utilities import sxs_directory, read_config, download_file

        progress = read_config("download_progress", True)

        if download is None:
            download = True

        if not tag:
            if download is not False:
                latest_release = cls.get_latest_release()
                tag = latest_release["name"]
                print(
                    f"Loading MAYA simulations using latest tag '{tag}'."
                )
            else:
                # Files will be named MAYAsimulations_MAYAvXXXX.bz2
                tags = [
                    Version(f.stem.split("_")[-1].removeprefix("MAYAv"))
                    for f in sxs_directory("cache").glob("MAYAsimulations_*.bz2")
                ]
                if tags:
                    tag = f"MAYAv{max(tags)}"
                    warning = (
                        f"\nDownloads were turned off, so we are using the latest cached"
                        f"\nsimulations file, tagged {tag}, which may be out of date."
                    )
                    warnings.warn(warning)
                else:
                    raise ValueError(f"No simulations files found in the cache and {download=} was passed")

        # Normalize the tag to "MAYAv" followed by a normalized Version
        tag = tag.removeprefix("MAYA") if tag.startswith("MAYA") else tag
        tag = tag[1:] if tag.startswith("v") else tag
        tag = f"MAYAv{Version(tag)}"

        cache_path = sxs_directory("cache") / f"MAYAsimulations_{tag}.bz2"

        if not cache_path.exists():
            if download is False:  # Test if it literally *is* False, rather than just casts to False
                raise ValueError(f"Simulations not found in '{cache_path}' and downloading was turned off")
            else:
                # 1. Download the full json file (zipped in flight, but auto-decompressed on arrival)
                # 2. Zip to a temporary file (using bzip2, which is better than the in-flight compression)
                # 3. Replace the original simulations.zip with the temporary zip file
                # 4. Remove the full json file
                # 5. Make sure the temporary zip file is gone too
                temp_json = cache_path.with_suffix(".temp.json")
                temp_zip = cache_path.with_suffix(".temp.bz2")
                try:
                    download_file(cls.url.format(tag=tag), temp_json, progress=progress, if_newer=False)
                except Exception as e:
                    raise RuntimeError(
                        f"\nFailed to download '{cls.url.format(tag=tag)}'."
                        f"\nMaybe {tag=} does not exist?"
                    ) from e
                else:
                    if temp_json.exists():
                        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_BZIP2) as simulations_zip:
                            simulations_zip.write(temp_json, arcname="MAYAsimulations.json")
                        temp_zip.replace(cache_path)
                finally:
                    temp_json.unlink(missing_ok=True)
                    temp_zip.unlink(missing_ok=True)

        if not cache_path.exists():
            raise ValueError(f"Simulations not found in '{cache_path}' for unknown reasons")

        try:
            with zipfile.ZipFile(cache_path, "r") as simulations_zip:
                try:
                    with simulations_zip.open("MAYAsimulations.json") as simulations_json:
                        try:
                            simulations = json.load(simulations_json)
                        except Exception as e:
                            raise ValueError(f"Failed to parse 'MAYAsimulations.json' in '{cache_path}'") from e
                except Exception as e:
                    raise ValueError(f"Failed to open 'MAYAsimulations.json' in '{cache_path}'") from e
        except Exception as e:
            raise ValueError(f"Failed to open '{cache_path}' as a ZIP file") from e

        sims = cls(simulations)
        sims.__file__ = str(cache_path)
        sims.tag = tag

        if not ignore_cached:
            cls._simulations = sims
        return sims

    @property
    def dataframe(self):
        """Create pandas.DataFrame with metadata for all simulations

        NOTE: You might prefer to load this object directly with
        `sxs.load("dataframe")` instead of using this method.  The
        benefit to that is that `load` accepts all the same options as
        `Simulations.load`, so you can load a specific tag, local
        simulations, etc.

        The `pandas` package is the standard Python interface for
        heterogeneous data tables, like the one we have here.  This
        interface allows for more convenient slicing and querying of
        data than the list of `dict`s provided by the `Simulations`
        object.

        This can also be a more convenient way to access the metadata
        because the raw metadata has missing keys and mixed formats.
        Iif a key is missing from the metadata for a particular key,
        the dataframe will just have a `NaN` in that entry, rather
        than raising an exception.  Other keys may have unexpected
        entries — such as the `"reference_eccentricity"` field, which
        is *usually* a float but may be a string like "<0.0001" if the
        eccentricity is not known precisely, but is only bounded.  The
        dataframe introduces a new column called
        `"reference_eccentricity_bound"` that is always a float giving
        an upper bound on the eccentricity.

        See the `pandas` documentation for more information on how to
        use the resulting dataframe, or the `Simulations` tutorial for
        examples.

        """
        import numpy as np
        import pandas as pd

        if hasattr(self, "_dataframe"):
            return self._dataframe

        simulations = pd.DataFrame.from_dict(self, orient="index")

        sims_df = pd.DataFrame(pd.concat((
            get(simulations, "q", floater),
            get(simulations, "eta", floater),
            get(simulations, "eccentricity", floater),
            three_vector_dataframe(simulations, "a1"),
            three_vector_dataframe(simulations, "a2"),
            get(simulations, "f_lower_at_1MSUN", floater),
            get(simulations, "omega_orbital", floater),
            get(simulations, "m1", floater),
            get(simulations, "m2", floater),
            get(simulations, "m1_irr", floater),
            get(simulations, "m2_irr", floater),
            get(simulations, "mean_anomaly", floater),
            get(simulations, "merge_time", floater),
            get(simulations, "separation", floater),
            get(simulations, "name", ""),
            get(simulations, "lvcnr_file_size__GB_", floater),
            get(simulations, "maya_file_size__GB_", floater),
        ), axis=1))

        # If `tag` is present, add it as an attribute
        if hasattr(self, "tag"):
            sims_df.tag = self.tag

        # See also `sxs.metadata.metadata._backwards_compatibility`;
        # it's probably a good idea to duplicate whatever is included
        # here in that function, just to make sure nothing slips
        # through the cracks.
        # ... anything?

        # We have ignored the following fields present in the
        # MAYAsimulations.json file (as of 2026-03-25), listed here with
        # the number of non-null entries:
        #
        # ... anything?

        self._dataframe = sims_df
        return sims_df

    table = dataframe
