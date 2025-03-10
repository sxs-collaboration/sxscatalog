# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair==5.5.0",
#     "anywidget==0.9.15",
#     "marimo",
#     "numpy==2.1.3",
#     "pandas==2.2.3",
#     "pyarrow==19.0.1",
#     "requests==2.32.3",
#     "sxscatalog==3.0.0a5",
#     "traitlets==5.14.3",
# ]
# ///

import marimo

__generated_with = "0.11.17"
app = marimo.App(
    width="full",
    app_title="SXS Catalog",
    css_file="custom.css",
    html_head_file="",
)


@app.cell(hide_code=True)
def _():
    # Import the necessary libraries
    import marimo as mo
    import numpy as np
    import math
    import warnings
    import pyarrow  # For efficient dataframe manipulation
    import json
    import pandas as pd
    import altair as alt
    return alt, json, math, mo, np, pd, pyarrow, warnings


@app.cell(hide_code=True)
def _(mo):
    # Title and introduction
    mo.md(
        r"""
        # The SXS Catalog of Simulations

        The metadata describing all simulations published by the SXS collaboration can be loaded into [a dataframe](https://sxs.readthedocs.io/en/main/api/simulations/#simulationsdataframe-class) using [the `sxs` package](https://github.com/sxs-collaboration/sxs/) as
        ```python
        import sxs
        df = sxs.load("dataframe")
        ```
        That dataframe can be manipulated [as usual by pandas](https://pandas.pydata.org/pandas-docs/stable/user_guide/10min.html).
        See the [`sxs` documentation](https://sxs.readthedocs.io/en/main/tutorials/01-Simulations_and_Metadata/) for details about the metadata.

        This page presents the data in graphical and tabular form, allowing you to explore the data interactively.
        """
    ).style({"width": "68%", "margin": "0 auto"})
    return


@app.cell(hide_code=True)
def _(mo):
    @mo.cache
    def download_json():
        import requests
        response = requests.get("https://raw.githubusercontent.com/moble/sxscatalogdata/main/simulations.json")
        response.raise_for_status()
        data_as_string = response.text
        return data_as_string
    return (download_json,)


@app.cell(hide_code=True)
def _(download_json, json):
    ### NOTE: This cell is hidden from the user in marimo's "app view".
    ### These commands are mostly here for nicer display; actual users
    ### will probably only need the commands mentioned above.

    # We use the more basic `sxscatalog` package, because `sxs` has a lot of dependencies,
    # including `numba`, which does not run in the browser (yet).  Normally, we would load
    # this with `sim = sxs.load("simulations")`.
    import sxscatalog
    sim_dict = json.loads(download_json())
    sim = sxscatalog.simulations.simulations.Simulations(sim_dict)
    df0 = sim.dataframe  # We filter this below

    # The df object is actually a sxs.SimulationsDataFrame (so that we can have attributes like df.BBH),
    # which subclasses — but is not a — pd.DataFrame, so the fancy display doesn't work directly.
    #
    # Fortunately, we can get the fancy display either by calling mo.ui.dataframe(df) or by acting on df
    # with some function that returns a regular pd.DataFrame.
    return df0, sim, sim_dict, sxscatalog


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---

        The dataframe has several useful [attributes](https://sxs.readthedocs.io/en/main/api/simulations/#simulationsdataframe-class) that allow selecting important subsets of the data.  Use the radio buttons below to select those subsets.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # Display some radio buttons that select the attributes
    system_type = mo.ui.radio(
        ["BBH", "IMR (BBH)", "BHNS", "NSNS", "any"],
        value="any",
        inline=True,
        label="System type:"
    )
    eccentricity = mo.ui.radio(
        ["eccentric", "noneccentric", "hyperbolic", "any"],
        value="any",
        inline=True,
        label="Eccentricity:"
    )
    precession = mo.ui.radio(
        ["precessing", "nonprecessing", "any"],
        value="any",
        inline=True,
        label="Precession:"
    )
    deprecation = mo.ui.radio(
        ["deprecated", "undeprecated", "any"],
        value="undeprecated",
        inline=True,
        label="Deprecation:"
    )

    df_attributes = mo.vstack([
        system_type,
        eccentricity,
        precession,
        deprecation,
    ])
    df_attributes
    return deprecation, df_attributes, eccentricity, precession, system_type


@app.cell(hide_code=True)
def _(deprecation, df0, eccentricity, precession, system_type):
    # Now, we apply the selections from above to the dataframe

    df = df0  # Keep the original around as df0

    if system_type.value == "BBH":
        df = df.BBH
    elif system_type.value == "IMR (BBH)":
        df = df.IMR
    elif system_type.value == "BHNS":
        df = df.BHNS
    elif system_type.value == "NSNS":
        df = df.NSNS

    if eccentricity.value == "eccentric":
        df = df.eccentric
    elif eccentricity.value == "noneccentric":
        df = df.noneccentric
    elif eccentricity.value == "hyperbolic":
        df = df.hyperbolic

    if precession.value == "precessing":
        df = df.precessing
    elif precession.value == "nonprecessing":
        df = df.nonprecessing

    if deprecation.value == "deprecated":
        df = type(df)(df[df["deprecated"]])
    elif deprecation.value == "undeprecated":
        df = df.undeprecated

    # And drop any columns that pandas couldn't interpret (these are the 3-vector columns)
    df = df.select_dtypes(exclude=object)

    # Finally, we re-order the columns to put these at the front
    preferred_columns = [
        "reference_mass_ratio", "reference_chi_eff", "reference_chi1_perp", "reference_chi2_perp",
        "reference_chi1_mag", "reference_chi2_mag", "reference_eccentricity", "number_of_orbits",
    ]
    columns = preferred_columns + [c for c in df.columns if c not in preferred_columns]
    df = df[columns]

    df["SXS ID"] = list(df.index)
    return columns, df, preferred_columns


@app.cell(hide_code=True)
def _(mo, simple_filtering):
    # Brief instructions for the table
    (
        mo.md("---\nClick the column headings to sort or filter by any value.")
        if simple_filtering.value
        else mo.md("---\nClick the column headings to sort.  Add a transform to filter or otherwise alter the data table.")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    simple_filtering = mo.ui.checkbox(label="Simple filtering")
    simple_filtering
    return (simple_filtering,)


@app.cell(hide_code=True)
def _(df, mo, simple_filtering):
    if simple_filtering.value:
        table = mo.ui.table(df, page_size=20, show_column_summaries=True, max_columns=df.shape[1]+1)
    else:
        table = mo.ui.dataframe(df, page_size=20)
    table
    return (table,)


@app.cell(hide_code=True)
def _(mo, simple_filtering):
    mo.md(
        "We can plot selected columns from the filtered data above."
        + (
            "  If you select checkboxes in the table, only those rows will be plotted."
            if simple_filtering.value else ""
        )
    )
    return


@app.cell(hide_code=True)
def _(table):
    table_data = table.value if len(table.value) > 0 else table.data
    return (table_data,)


@app.cell(hide_code=True)
def _(df, mo):
    horizontal_axis = mo.ui.dropdown(
        options=df.columns.to_list(),
        value="reference_mass_ratio",
        label="Horizontal axis",
        allow_select_none=False,
    )
    vertical_axis = mo.ui.dropdown(
        options=df.columns.to_list(),
        value="reference_chi_eff",
        label="Vertical axis",
        allow_select_none=False,
    )
    marker_size = mo.ui.dropdown(
        options=df.columns.to_list(),
        label="Marker size",
    )
    marker_color = mo.ui.dropdown(
        options=df.columns.to_list(),
        label="Marker color",
    )

    selectors = [horizontal_axis, vertical_axis, marker_size, marker_color]

    mo.vstack([
        mo.hstack([horizontal_axis, vertical_axis], justify="space-around"),
        mo.hstack([marker_size, marker_color], justify="space-around")
    ], justify="space-around")
    return horizontal_axis, marker_color, marker_size, selectors, vertical_axis


@app.cell(hide_code=True)
def _(
    alt,
    horizontal_axis,
    marker_color,
    marker_size,
    mo,
    preferred_columns,
    selectors,
    table_data,
    vertical_axis,
):
    # Compose the plot
    used_selectors = ["SXS ID"] + preferred_columns + [
        s.value for s in selectors if s.value is not None and s.value not in preferred_columns
    ]
    #used_selectors = ["SXS ID"] + [s.value for s in selectors if s.value is not None]
    df_restricted = table_data[used_selectors]

    kwargs = dict(
        x=horizontal_axis.value,
        y=vertical_axis.value,
        tooltip=used_selectors,
    )
    if marker_size.value is not None:
        kwargs["size"] = marker_size.value
    if marker_color.value is not None:
        # Possible color schemes are listed on https://vega.github.io/vega/docs/schemes/
        kwargs["color"] = alt.Color(marker_color.value).scale(scheme="viridis")

    chart = mo.ui.altair_chart(
        alt.Chart(df_restricted, height=400)
        .mark_circle(
            stroke="#303030",
            strokeWidth=1,
            opacity=0.8,
        )
        .encode(**kwargs),
        legend_selection=True,
        label="SXS Simulations"
    )
    chart
    return chart, df_restricted, kwargs, used_selectors


@app.cell(hide_code=True)
def _(chart, mo):
    # Narrow dat the data further to just the data from (or selected in) the chart above
    chart_data = chart.value if len(chart.value) > 0 else chart.data

    (
        mo.md("The following data can be further restricted by selecting a point or region on the plot; otherwise all data in the plot will be used.")
        if len(chart.value) == 0 else
        None
    )
    return (chart_data,)


@app.cell(hide_code=True)
def _(chart_data, math, mo):
    # Show the code needed to load these simulations
    max_width = 6  # How many SXS IDs to allow on one line
    these_simulations =  ("this simulation" if len(chart_data)==1 else f"these {len(chart_data):,} simulations")
    load_code = (
        f"""sim = sxs.load("{chart_data.index[0]}")"""
        if len(chart_data)==1 else
        (
            "sims = [sxs.load(sim) for sim in [\"" + "\", \"".join(chart_data.index) + "\"]]"
            if len(chart_data) < max_width else
            (
                "sims = [sxs.load(sim) for sim in [\n    \""
                + "\",\n    \"".join(
                    "\", \"".join(chart_data.index[i:min(i+max_width, len(chart_data.index))])
                    for i in range(0, math.ceil(len(chart_data.index)/max_width)*max_width, max_width)
                )
                + "\"\n]]"
            )
        )
    )
    final_table = (
        mo.ui.table(chart_data.drop("SXS ID", axis=1), page_size=20)
        if len(chart_data) > 0
        else mo.md("Select a region in the plot above to see details here")
    )

    mo.vstack([
        mo.md(f"You can load {these_simulations} with\n"),
        mo.md(f"```python\n{load_code}\n```\n\n").style({"max-height": "300px", "overflow": "auto"}),
        mo.md(f"The metadata summary table for that selection follows:\n{final_table}"),
    ])
    return final_table, load_code, max_width, these_simulations


if __name__ == "__main__":
    app.run()
