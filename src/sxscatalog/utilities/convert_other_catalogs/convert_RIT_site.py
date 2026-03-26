#!/usr/bin/env python3


def fetch_RIT_catalog_data():
    """Fetch metadata from the RIT Catalog and parse as a dict.

    Scrape the RIT Catalog page and extract information about the numerical
    simulations. The RIT Catalog can be accessed through
    https://ccrg.rit.edu/numerical-simulations, but the actual data is hosted at
    https://ccrgpages.rit.edu/~RITCatalog/. Retrieve the simulation IDs,
    download links for extrapolated Psi4 and Strain data, and the metadata for
    each simulation. The metadata is parsed into a dict.

    Returns
    =======
    dict
        A dictionary mapping simulation name to metadata.

    """

    from ...metadata.metadata import Metadata

    import requests
    import tempfile
    from bs4 import BeautifulSoup

    RITcatalog_url = "https://ccrgpages.rit.edu/~RITCatalog/"

    session = requests.Session()

    response = session.get(RITcatalog_url)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to load page {RITcatalog_url}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Finds the table with id "example", i.e.,
    # the one that has the numerical simulations data

    table = soup.find("table", id="example")

    # Goes to tbody (table body) and finds all rows (tr)
    rows = table.find("tbody").find_all("tr")

    RITcatalogdata = {}

    # Goes through each row and extracts the data
    for row in rows:
        cells = row.find_all("td")
        if len(cells) == 0:
            continue

        sim_id = cells[0].get_text(strip=True)
        links = cells[2].find_all("a", href=True)

        if len(links) != 3:
            raise Exception(
                "Expecting 3 links, but getting an unexpected number of links "
                f"for simulation {sim_id}."
            )

        # Validate links contain expected keywords
        psi_link = strain_link = metadata_link = None
        for link in links:
            href = link["href"].lower()
            if "psi" in href:
                psi_link = link
            elif "strain" in href:
                strain_link = link
            elif "metadata" in href:
                metadata_link = link

        if not all([psi_link, strain_link, metadata_link]):
            raise Exception(f"Missing expected links for simulation {sim_id}.")

        RITcatalogdata[sim_id] = {}

        # Fetching metadata file
        metadata_response = session.get(RITcatalog_url + metadata_link["href"])
        if metadata_response.status_code != 200:
            raise Exception(f"Failed to load page for simulation {str(sim_id)}")

        # Parsing metadata content
        # Since from_txt_file needs a file path,
        # we create a temporary file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write(metadata_response.text)
            tmp_path = tmp.name
            tmp.seek(0)
            RITcatalogdata[sim_id] = Metadata.from_txt_file(tmp_path, cache_json=False)

            # from_txt_file() adds metadata_path, which is meaningless here.
            # _backwards_compatibility() adds number_of_orbits=NaN, which we
            # don't want. Throw away both of these keys.
            RITcatalogdata[sim_id].pop("metadata_path", None)

        RITcatalogdata[sim_id]["extrap_psi4_url"] = RITcatalog_url + psi_link["href"]
        RITcatalogdata[sim_id]["extrap_strain_url"] = (
            RITcatalog_url + strain_link["href"]
        )
        RITcatalogdata[sim_id]["metadata_url"] = RITcatalog_url + metadata_link["href"]

    return RITcatalogdata


if __name__ == "__main__":

    import json
    import argparse

    # absolute imports in a standalone script
    from sxscatalog.utilities.convert_other_catalogs.convert_RIT_site import (
        fetch_RIT_catalog_data,
    )
    from sxscatalog.utilities import consolidate_xyz_vectors

    parser = argparse.ArgumentParser(
        description="Fetch RIT Catalog data and save to JSON."
    )

    parser.add_argument(
        "--output",
        type=argparse.FileType("w"),
        default="RIT_catalog.json",
        help="Output JSON file name (default: %(default)s).",
    )
    parser.add_argument(
        "--consolidate-xyz-vectors",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="if triples of <key>x <key>y <key>z should be consolidated "
        "into vectors (default: %(default)s)",
    )

    args = parser.parse_args()

    data_dict = fetch_RIT_catalog_data()
    if args.consolidate_xyz_vectors:
        data_dict = {k: consolidate_xyz_vectors(v) for k, v in data_dict.items()}

    json.dump(data_dict, args.output, indent=2, sort_keys=True)
