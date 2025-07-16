"""Container interface to the catalog of SXS simulations"""

import collections
import numpy as np
import pandas as pd

from ..utilities.string_converters import *


class SimulationsDataFrame(pd.DataFrame):
    @property
    def BBH(self):
        """Restrict dataframe to just binary black hole systems"""
        return type(self)(self[self["object_types"] == "BHBH"])
    BHBH = BBH
    
    @property
    def BHNS(self):
        """Restrict dataframe to just black hole-neutron star systems"""
        return type(self)(self[self["object_types"] == "BHNS"])
    NSBH = BHNS
    
    @property
    def NSNS(self):
        """Restrict dataframe to just binary neutron star systems"""
        return type(self)(self[self["object_types"] == "NSNS"])
    BNS = NSNS

    @property
    def noneccentric(self):
        """Restrict dataframe to just non-eccentric systems (e<1e-3)"""
        return type(self)(self[self["reference_eccentricity_bound"] < 1e-3])

    @property
    def eccentric(self):
        """Restrict dataframe to just eccentric systems (e>=1e-3)"""
        return type(self)(self[self["reference_eccentricity_bound"] >= 1e-3])
    
    @property
    def nonprecessing(self):
        """Restrict dataframe to just nonprecessing systems
        
        The criterion used here is that the sum of the x-y components
        of the spins is less than 1e-3 at the reference time.
        Returns
        -------
        Simulations
            An instance of the Simulations class containing the loaded data.

        """
        return type(self)(self[
            (self["reference_chi1_perp"] + self["reference_chi2_perp"]) < 1e-3
        ])
    
    @property
    def precessing(self):
        """Restrict dataframe to just precessing systems
        
        The criterion used here is that the sum of the x-y components
        of the spins is at least 1e-3 at the reference time.
        """
        return type(self)(self[
            (self["reference_chi1_perp"] + self["reference_chi2_perp"]) >= 1e-3
        ])
    
    @property
    def IMR(self):
        """Restrict dataframe to just BBH IMR systems
        
        "IMR" stands for inspiral, merger, and ringdown.  Systems that
        will *not* be in this group include simulations that
        correspond to physical IMR systems, but were not continued
        through the merger.

        The criteria used here are just that the reference
        eccentricity and remnant mass are actual (finite) numbers.
        Currently, at least, the existence of a measured eccentricity
        means that the system is not hyperbolic or head-on.
        """
        df = self.BBH
        return type(df)(df[
            np.isfinite(df["reference_eccentricity"])
            & np.isfinite(df["remnant_mass"])
        ])
    
    @property
    def hyperbolic(self):
        """Restrict dataframe to just hyperbolic systems
        
        The criterion used here is that the (normalized) ADM mass is
        greater than 1.
        """
        total_mass = self["initial_mass1"] + self["initial_mass2"]
        normalized_ADM = self["initial_ADM_energy"] / total_mass
        return type(self)(self[
            np.isfinite(total_mass) & (total_mass > 0) & (normalized_ADM > 1)
        ])
    
    @property
    def deprecated(self):
        """Restrict dataframe to just simulations that are deprecated"""
        return type(self)(self[self["deprecated"]])
    
    @property
    def undeprecated(self):
        """Restrict dataframe to just simulations that are not deprecated"""
        return type(self)(self[~self["deprecated"]])


class Simulations(collections.OrderedDict):
    """Interface to the catalog of SXS simulations
    
    Creation
    --------
    You probably don't need to create this object yourself.  The
    easiest way to create this object is just to use the `sxs.load`
    function:

    ```python
    import sxs

    simulations = sxs.load("simulations")
    ```

    Note SXS members may also wish to read a local copy of the
    simulation annex, which can be done with
    ```python
    simulations = sxs.load("simulations", annex_dir="/path/to/SimulationAnnex.git")
    ```
    which will re-read the annex (which may take about a minute), or
    ```python
    simulations = sxs.load("simulations", local=True)
    ```
    if the annex has not been updated since the last time you
    used the `annex_dir` argument.  Once you have done this,
    calls to `sxs.load` will automatically use this local copy
    of the simulations.
    """
    releases_url = "https://api.github.com/repos/sxs-collaboration/sxscatalogdata/releases"
    url = "https://raw.githubusercontent.com/sxs-collaboration/sxscatalogdata/{tag}/simulations.json"

    def __init__(self, sims):
        """Initialize the Simulations dictionary

        Note that the constructor is not generally useful from outside
        this class.  See `Simulations.load` for a more useful
        initialization function, or simply call
        `sxs.load("simulations")`.

        """
        from ..metadata import Metadata
        super(Simulations, self).__init__(
            (k, Metadata(sims[k])) for k in sorted(sims)
        )

    @classmethod
    def get_latest_release(cls):
        """Retrieve the most-recently published release of the catalog from github"""
        import requests
        releases_response = requests.get(cls.releases_url)
        releases_response.raise_for_status()
        releases_data = releases_response.json()
        latest_release = max(releases_data, key=lambda r: r["published_at"])
        return latest_release

    @classmethod
    def local(
        cls,
        directory=None,
        *,
        download=None,
        output_file=None,
        compute_md5=False,
        show_progress=False,
        ignore_cached=False,
    ):
        """Load the local catalog of SXS simulations
        
        This function loads the standard public catalog, but also
        includes any local simulations found in the given directory.
        If no directory is provided, it will look for the local
        simulations file in the sxs cache directory.

        Parameters
        ----------
        directory : {None, str, Path}, optional
            A directory containing subdirectories of SXS simulations.
            See `sxs.local_simulations` for details about what is
            expected in this directory.  If None (the default), it
            will look for the local simulations file in the sxs cache
            directory.
        download : {None, bool}, optional
            Passed to `Simulations.load` when loading the public set
            of simulations.
        output_file : {None, str, Path}, optional
            If `directory` is not None, this will be passed to
            `sxs.write_local_simulations`.
        compute_md5 : bool, optional
            If `directory` is not None, this will be passed to
            `sxs.local_simulations`.
        show_progress : bool, optional
            If `directory` is not None, this will be passed to
            `sxs.local_simulations`.
        ignore_cached : bool, optional
            If True, this function will ignore the cached version of
            the `Simulations` object attached to this class, and
            reload the simulations as if the cache did not exist.

        See Also
        --------
        sxs.local_simulations : Search for local simulations
        sxs.write_local_simulations : Write local simulations to a
        file
        
        """
        import json
        from .local import write_local_simulations
        from ..utilities import sxs_directory

        if directory is not None:
            local_path = output_file
            local_simulations = write_local_simulations(
                directory,
                output_file=output_file,
                compute_md5=compute_md5,
                show_progress=show_progress
            )
        else:
            local_path = sxs_directory("cache") / "local_simulations.json"
            if not local_path.exists():
                if directory is not None:
                    raise ValueError(f"Writing local simulations for {directory=} failed")
                else:
                    raise ValueError(
                        f"Local simulations file not found, but no `directory` was provided.\n"
                        + "If called from `sxs.load`, just pass the name of the directory."
                    )
            with local_path.open("r") as f:
                local_simulations = json.load(f)
        simulations = cls.load(
            download,
            show_progress=show_progress,
            ignore_cached=ignore_cached
        )

        doi_versions = {
            k: v["DOI_versions"]
            for k,v in simulations.items()
            if "DOI_versions" in v
        }
        simulations.update(local_simulations)
        for k,v in doi_versions.items():
            simulations[k]["DOI_versions"] = v
        simulations.__file__ = str(local_path)
        return simulations

    @classmethod
    def load(
        cls,
        download=None, *,
        tag="",
        local=False,
        annex_dir=None,
        output_file=None,
        compute_md5=False,
        show_progress=False,
        ignore_cached=False,
    ):  # Make sure to pass through any parameters from `load` and to `local`
        """Load the catalog of SXS simulations

        Note that — unlike most SXS data files — the simulations file
        is updated frequently.  As a result, this function — unlike
        the loading functions for most SXS data files — will download
        the simulations by default each time it is called.  However,
        also note that this function is itself cached, meaning that
        the same dict will be returned on each call in a given python
        session.  If you want to avoid that behavior, use
        `Simulations.reload`.

        Parameters
        ----------
        download : {None, bool}, optional
            If False, this function will look for the simulations in
            the sxs cache and raise an error if it is not found.  If
            True, this function will download the simulations and
            raise an error if the download fails.  If None (the
            default), it will try to download the file, warn but fall
            back to the cache if that fails, and only raise an error
            if the simulations is not found in the cache.  Note that
            this ignores the sxs configuration file entirely.

        Keyword-only Parameters
        -----------------------
        tag : str, optional
            The git tag of the simulations file to load.  If not
            provided, the latest tag will be used.  This cannot be
            provided if either `local` or `annex_dir` is provided.
        local : {None, bool}, optional
            If True, this function will load *local* simulations from
            the sxs cache.  To prepare the cache, you may wish to call
            `sxs.write_local_simulations`.
        annex_dir : {None, str, Path}, optional
            If provided and `local=True`, this function will load
            local simulations from the given directory.  This is
            equivalent to calling `Simulations.local(directory)`.
        output_file : {None, str, Path}, optional
            If `annex_dir` is not None, this will be passed to
            `sxs.write_local_simulations`.
        compute_md5 : bool, optional
            If `annex_dir` is not None, this will be passed to
            `sxs.simulations.local_simulations`.
        show_progress : bool, optional
            If `annex_dir` is not None, this will be passed to
            `sxs.simulations.local_simulations`.
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

        if tag and (local or annex_dir is not None):
            raise ValueError("Cannot specify a `tag` with `local` or `annex_dir`")

        if local or (annex_dir is not None):
            simulations = cls.local(
                directory=annex_dir,
                download=download,
                output_file=output_file,
                compute_md5=compute_md5,
                show_progress=show_progress,
                ignore_cached=ignore_cached,
            )
            if not ignore_cached:
                cls._simulations = simulations
                return cls._simulations
            else:
                return simulations

        progress = read_config("download_progress", True)

        if download is None:
            download = True

        published_at = False
        if not tag:
            if download is not False:
                latest_release = cls.get_latest_release()
                tag = latest_release["tag_name"]
                published_at = latest_release["published_at"]
                print(
                    f"Loading SXS simulations using latest tag '{tag}', "
                    f"published at {published_at}."
                )
            else:
                tags = [
                    Version(f.stem.split("_")[-1]) # Chops off the "v" prefix so `max` works
                    for f in sxs_directory("cache").glob("simulations_*.bz2")
                ]
                if tags:
                    tag = f"v{max(tags)}"
                    warning = (
                        f"\nDownloads were turned off, so we are using the latest cached"
                        f"\nsimulations file, tagged {tag}, which may be out of date."
                    )
                    warnings.warn(warning)
                else:
                    raise ValueError(f"No simulations files found in the cache and {download=} was passed")

        # Normalize the tag to "v" followed by a normalized Version
        tag = f"v{Version(tag)}"

        cache_path = sxs_directory("cache") / f"simulations_{tag}.bz2"

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
                            simulations_zip.write(temp_json, arcname="simulations.json")
                        temp_zip.replace(cache_path)
                finally:
                    temp_json.unlink(missing_ok=True)
                    temp_zip.unlink(missing_ok=True)

        if not cache_path.exists():
            raise ValueError(f"Simulations not found in '{cache_path}' for unknown reasons")

        try:
            with zipfile.ZipFile(cache_path, "r") as simulations_zip:
                try:
                    with simulations_zip.open("simulations.json") as simulations_json:
                        try:
                            simulations = json.load(simulations_json)
                        except Exception as e:
                            raise ValueError(f"Failed to parse 'simulations.json' in '{cache_path}'") from e
                except Exception as e:
                    raise ValueError(f"Failed to open 'simulations.json' in '{cache_path}'") from e
        except Exception as e:
            raise ValueError(f"Failed to open '{cache_path}' as a ZIP file") from e

        sims = cls(simulations)
        sims.__file__ = str(cache_path)
        sims.tag = tag
        if published_at:
            sims.published_at = published_at

        if not ignore_cached:
            cls._simulations = sims
        return sims

    @classmethod
    def reload(cls, *args, **kwargs):
        """Reload the catalog of SXS simulations, without caching

        Clears the cache created by a previous call to
        `Simulations.load` and returns the result of calling it again.

        All arguments are passed on to `load`.  See also the
        `ignore_cached` argument of `load`.  This does basically the
        same thing, except that it re-establishes the cache with
        whatever is reloaded.

        See Also
        --------
        Simulations.load : Caching version of this function

        """
        if hasattr(cls, "_simulations"):
            delattr(cls, "_simulations")
        return cls.load(*args, **kwargs)

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

        # See also below for "number_of_orbits" field.
        # See also `sxs.metadata.metadata._backwards_compatibility`;
        # it's probably a good idea to duplicate whatever is included
        # here in that function, just to make sure nothing slips
        # through the cracks.
        for col in [
            "number_of_orbits", "number_of_orbits_from_start",
            "number_of_orbits_from_reference_time"
        ]:
            if col not in simulations.columns:
                simulations[col] = np.nan

        def valid_vector(value):
            # Check if the value is a list or array of length 3
            if isinstance(value, (list, np.ndarray)) and len(value) == 3:
                return value
            # Replace invalid entries with [nan, nan, nan]
            return [np.nan, np.nan, np.nan]

        def three_vector_dataframe(df, col):
            """Convert a column of vectors to components, magnitude, and original"""
            vectors = df.get(
                col, np.nan*np.ones((len(df),3))
            ).apply(valid_vector).tolist()
            df_vec = pd.DataFrame(
                vectors,
                columns=[f"{col}_{i}" for i in ["x", "y", "z"]],
                index=df.index  # Inherit the index from df
            )
            df_vec[f"{col}_mag"] = df_vec.apply(norm, axis=1)
            df_vec[col] = vectors
            return df_vec
        
        def get(df, col, mapper, new_name=None):
            new_name = new_name or col
            default_values = {
                floater: np.nan,
                floaterbound: np.nan,
                three_vec: np.array([np.nan, np.nan, np.nan]),
                norm: np.nan,
                datetime_from_string: pd.NaT,
            }
            try:
                default_value = default_values[mapper]
                use_mapper = True
            except:
                default_value = mapper
                use_mapper = False
            default_series = pd.Series(
                [default_value] * len(df),
                index=df.index,
                name=col
            )
            gotten = df.get(col, default_series)
            if use_mapper:
                gotten = gotten.map(mapper)
            return gotten.rename(new_name)

        sims_df = SimulationsDataFrame(pd.concat((
            get(simulations, "reference_mass_ratio", floater),
            get(simulations, "reference_chi_eff", floater),
            get(simulations, "reference_chi1_perp", floater),
            get(simulations, "reference_chi2_perp", floater),
            get(simulations, "reference_eccentricity", floater),
            get(simulations, "reference_eccentricity", floaterbound, new_name="reference_eccentricity_bound"),
            get(simulations, "reference_time", floater),
            three_vector_dataframe(simulations, "reference_dimensionless_spin1"),
            three_vector_dataframe(simulations, "reference_dimensionless_spin2"),
            get(simulations, "reference_mean_anomaly", floater),
            three_vector_dataframe(simulations, "reference_orbital_frequency"),
            (
                get(simulations, "reference_position1", three_vec)
                - get(simulations, "reference_position2", three_vec)
            ).map(norm).rename("reference_separation"),
            get(simulations, "reference_position1", three_vec),
            get(simulations, "reference_position2", three_vec),
            get(simulations, "reference_mass1", floater),
            get(simulations, "reference_mass2", floater),
            get(simulations, "reference_dimensionless_spin1", norm, new_name="reference_chi1_mag"),
            get(simulations, "reference_dimensionless_spin2", norm, new_name="reference_chi2_mag"),
            get(simulations, "relaxation_time", floater),
            # get(simulations, "merger_time", floater),
            get(simulations, "common_horizon_time", floater),
            get(simulations, "remnant_mass", floater),
            three_vector_dataframe(simulations, "remnant_dimensionless_spin"),
            three_vector_dataframe(simulations, "remnant_velocity"),
            # get(simulations, "final_time", floater),
            get(simulations, "EOS", np.nan).fillna(get(simulations, "eos", np.nan)),
            get(simulations, "disk_mass", floater),
            get(simulations, "ejecta_mass", floater),
            get(simulations, "object_types", "").astype("category"),
            get(simulations, "initial_data_type", "").astype("category"),
            get(simulations, "initial_separation", floater),
            get(simulations, "initial_orbital_frequency", floater),
            get(simulations, "initial_adot", floater),
            get(simulations, "initial_ADM_energy", floater),
            three_vector_dataframe(simulations, "initial_ADM_linear_momentum"),
            three_vector_dataframe(simulations, "initial_ADM_angular_momentum"),
            get(simulations, "initial_mass1", floater),
            get(simulations, "initial_mass2", floater),
            get(simulations, "initial_mass_ratio", floater),
            three_vector_dataframe(simulations, "initial_dimensionless_spin1"),
            three_vector_dataframe(simulations, "initial_dimensionless_spin2"),
            get(simulations, "initial_position1", three_vec),
            get(simulations, "initial_position2", three_vec),
            # get(simulations, "object1", "").astype("category"),
            # get(simulations, "object2", "").astype("category"),
            # get(simulations, "url", ""),
            # get(simulations, "simulation_name", ""),
            # get(simulations, "alternative_names", []),
            # get(simulations, "metadata_path", ""),
            # get(simulations, "end_of_trajectory_time", floater),
            # get(simulations, "merger_time", floater),
            get(simulations, "number_of_orbits", floater),
            get(simulations, "number_of_orbits_from_start", floater),
            get(simulations, "number_of_orbits_from_reference_time", floater),
            get(simulations, "DOI_versions", []),
            get(simulations, "keywords", []),
            get(simulations, "date_link_earliest", datetime_from_string),
            get(simulations, "date_run_earliest", datetime_from_string),
            get(simulations, "date_run_latest", datetime_from_string),
            get(simulations, "date_postprocessing", datetime_from_string),
        ), axis=1))

        # If `tag` or `published_at` are present, add them as attributes
        if hasattr(self, "tag"):
            sims_df.tag = self.tag
        if hasattr(self, "published_at"):
            sims_df.published_at = self.published_at

        # Add a column to indicate whether this simulation is deprecated
        sims_df.insert(0, "deprecated", (
            sims_df["keywords"].map(lambda ks: "deprecated" in ks)
        ))

        # See also `sxs.metadata.metadata._backwards_compatibility`;
        # it's probably a good idea to duplicate whatever is included
        # here in that function, just to make sure nothing slips
        # through the cracks.
        sims_df["number_of_orbits"] = sims_df["number_of_orbits"].fillna(
            sims_df["number_of_orbits_from_start"]
        )

        # We have ignored the following fields present in the
        # simulations.json file (as of 2024-08-04), listed here with
        # the number of non-null entries:
        #
        # alternative_names                2778
        # point_of_contact_email           2778
        # authors_emails                   2776
        # simulation_bibtex_keys           2778
        # code_bibtex_keys                 2778
        # initial_data_bibtex_keys         2778
        # quasicircular_bibtex_keys        2778
        # metadata_version                 2778
        # spec_revisions                   2778
        # spells_revision                  2778
        # merger_time                         9
        # final_time                         12
        # reference_spin1                     2
        # reference_spin2                     1
        # nitial_spin1                        2
        # initial_spin2                       2
        # remnant_spin                        2
        # initial_mass_withspin2              2
        # end_of_trajectory_time              3

        self._dataframe = sims_df
        return sims_df

    table = dataframe
