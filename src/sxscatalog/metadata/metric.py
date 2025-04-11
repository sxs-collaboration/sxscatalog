from ..utilities.string_converters import *
import numpy as np

class MetadataMetric:
    """A metric for comparing metadata.

    This class is designed to be used as a callable object that takes
    two collections of metadata (`sxs.Metadata`, `dict`, `pd.Series`)
    and returns a number measuring the distance between the metadata.
    
    This is intended to be used as a heuristic for sorting and
    filtering metadata, rather than as a strict metric for clustering
    or classification.  In particular, note that this does not account
    for the fact that parameters are typically measured at the
    reference time, which can be quite different for different
    systems.

    Note that calling an object of this class with two metadata
    collections will return the *squared* distance between them.

    Parameters
    ----------
    parameters : list of str, optional
        The names of the metadata fields to be compared.  The defaults
        are the mass ratio, spins, and eccentricity at the reference
        time.  Note that all of these fields *must* be present in
        *both* metadata collections — except for
        `reference_mass_ratio` or `reference_complex_eccentricity`
        which will be calculated from other parameters if not present.
        (The `Metadata.add_standard_parameters` method may be useful
        here.)
    metric : array_like, optional
        The matrix used to weight the differences in the parameters.
        The default is a diagonal matrix with ones on the diagonal.
    allow_different_object_types : bool, optional
        If True, metadata with different object types (BHBH, BHNS,
        NSNS) will be compared without penalty.  If False, metadata
        with different object types will be assigned an infinite
        distance.
    eccentricity_threshold1 : float, optional
        The threshold eccentricity below which we consider metadata1
        non-eccentric.  Default is 1e-2.
    eccentricity_threshold2 : float, optional
        The threshold eccentricity below which we consider metadata2
        non-eccentric.  Default is 1e-3.
    eccentricity_threshold_penalize_shorter : int, optional
        The number of orbits below which we penalize metadata2 for
        having a non-zero eccentricity when metadata1 does not.  This
        is intended to avoid ascribing small distances to systems with
        shorter inspirals.  Default is 20.

    The eccentricity is ignored if eccentricity is one of the
    parameters to be compared and all three of the following are true:
      1) the eccentricity in metadata1 is below
         `eccentricity_threshold1`,
      2) the eccentricity in metadata2 is below
         `eccentricity_threshold2`, and
      3) the number of orbits in metadata2 is longer than
         `eccentricity_threshold_penalize_shorter`.
    You may set these arguments to 0 to disable these features.

    """
    def __init__(
            self,
            parameters=[
                "reference_mass_ratio",
                "reference_dimensionless_spin1",
                "reference_dimensionless_spin2",
                "reference_complex_eccentricity",
            ],
            metric=None,
            allow_different_object_types=False,
            eccentricity_threshold1=1e-2,
            eccentricity_threshold2=1e-3,
            eccentricity_threshold_penalize_shorter=20,
    ):
        self.parameters = parameters
        self.metric = metric
        self.allow_different_object_types = allow_different_object_types
        self.eccentricity_threshold1 = eccentricity_threshold1
        self.eccentricity_threshold2 = eccentricity_threshold2
        self.eccentricity_threshold_penalize_shorter = eccentricity_threshold_penalize_shorter

    def __call__(self, metadata1, metadata2, debug=False):
        if not self.allow_different_object_types:
            type1 = (
                metadata1["object_types"]
                if "object_types" in metadata1
                else "".join(sorted([
                    metadata1.get("object1", "A").upper(),
                    metadata1.get("object2", "B").upper()
                ]))
            )
            type2 = (
                metadata2["object_types"]
                if "object_types" in metadata2
                else "".join(sorted([
                    metadata2.get("object1", "C").upper(),
                    metadata2.get("object2", "D").upper()
                ]))
            )
            if type1 != type2:
                return np.inf
        
        # Create empty lists because the element type will vary;
        # each element could be `float`, `complex`, or `list`.
        values1 = [np.nan] * len(self.parameters)
        values2 = [np.nan] * len(self.parameters)

        # Fill in the values with the metadata
        for values, metadata in [(values1, metadata1), (values2, metadata2)]:
            for i, parameter in enumerate(self.parameters):
                if parameter in metadata:
                    values[i] = metadata[parameter]
                elif parameter == "reference_mass_ratio":
                    values[i] = (
                        floater(metadata.get("reference_mass1", np.nan))
                        / floater(metadata.get("reference_mass2", np.nan))
                    )
                elif parameter == "reference_complex_eccentricity":
                    e = floaterbound(
                        metadata.get(
                            "reference_eccentricity_bound",
                             metadata.get("reference_eccentricity", np.nan)
                        )
                    )
                    l = floater(metadata.get("reference_mean_anomaly", np.nan))
                    values[i] = e * np.exp(1j * l)

        if debug:
            print(f"{self.parameters=}")
            print(f"{values1=}")
            print(f"{values2=}")

        if "reference_eccentricity" in self.parameters or "reference_complex_eccentricity" in self.parameters:
            i = (
                self.parameters.index("reference_eccentricity")
                if "reference_eccentricity" in self.parameters
                else self.parameters.index("reference_complex_eccentricity")
            )

            if abs(values1[i]) < self.eccentricity_threshold1:
                # Then we consider metadata1 a non-eccentric system...

                # ...and we ignore the eccentricity if metadata2 is also non-eccentric,
                # and longer than eccentricity_threshold_penalize_shorter.
                if (
                    abs(values2[i]) < self.eccentricity_threshold2
                    and metadata2.get(
                        "number_of_orbits",
                        metadata2.get("number_of_orbits_from_start", 0)
                    ) > self.eccentricity_threshold_penalize_shorter
                ):
                    values1[i] = values2[i]

        # Concatenate the values into a single 1-d array (even if some
        # entries are 3-vectors).
        difference = (
            np.concatenate(list(map(np.atleast_1d, values1)))
            - np.concatenate(list(map(np.atleast_1d, values2)))
        )

        if debug:
            print(f"{difference=}")

        metric = self.metric or np.diag(np.ones(len(difference)))

        return np.real(difference @ metric @ difference.conj())
