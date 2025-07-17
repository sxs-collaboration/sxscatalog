# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair==5.5.0",
#     "anywidget==0.9.18",
#     "marimo",
#     "numpy==2.3.1",
#     "pandas==2.3.1",
#     "pyarrow==20.0.0",
#     "pyodide-http==0.2.2",
#     "requests==2.32.4",
#     "sxscatalog==3.0.17",
#     "traitlets==5.14.3",
# ]
# ///

import marimo

__generated_with = "0.14.11"
app = marimo.App(
    width="full",
    app_title="SXS Catalog",
    css_file="custom.css",
    html_head_file="",
)


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md(r"""<h1 style="text-align: center;">The SXS Catalog of Simulations</h1>""")
    return (mo,)


@app.cell(hide_code=True)
def _():
    # Import the libraries needed just for demonstrations in this notebook
    import numpy as np
    import math
    import warnings
    import pyarrow  # For efficient dataframe manipulation
    import json
    import pandas as pd
    import altair as alt
    import pyodide_http

    # This patches `requests` to work in the browser, so that we can load the SXS catalog data
    pyodide_http.patch_all()
    return alt, math, pd


@app.cell(hide_code=True)
def _(pd):
    # Import the sxs package and load the dataframe

    # NOTE: We use the more basic `sxscatalog` package, because `sxs` cannot run in the browser
    # because it depends on `numba`, and because marimo cannot interact with the filesystem to
    # persistently cache large data files.  Normally, we would use `sxs` itself and load the
    # dataframe with `sim = sxs.load("simulations", tag={tag})`.
    import sxscatalog

    current_time = pd.Timestamp.now().strftime("%H:%M on %B %d, %Y")

    # First, we'll get the latest release so that we can write it in the notebook;
    # `sxscatalog.load("dataframe")` would do this on its own.
    latest_release = sxscatalog.simulations.Simulations.get_latest_release()
    tag_name = latest_release["tag_name"]
    release_published = pd.to_datetime(latest_release["published_at"]).strftime("%B %d, %Y")

    # Note that we load the dataframe as `df0`, so that we can filter it below as `df`
    df0 = sxscatalog.load("dataframe", tag=tag_name)

    # The dataframe is actually a sxs.SimulationsDataFrame (so that we can have attributes like df.BBH),
    # which subclasses — but is not a — pd.DataFrame, so marimo fanciness doesn't work if the dataframe
    # is just output raw.  We can get the fancy display either by calling mo.ui.dataframe(df) or by
    # acting on df with some function that returns a regular pd.DataFrame.
    return current_time, df0, release_published, tag_name


@app.cell(hide_code=True)
def _(current_time, mo, release_published, tag_name):
    # Title and introduction
    mo.md(
        rf"""
        This page presents metadata from version {tag_name[1:]} of the SXS catalog, which was released on {release_published}, and is the current release as of <span data-tooltip="{current_time}">when you opened this page</span>.

        The metadata can be loaded into [a dataframe](https://sxs.readthedocs.io/en/main/api/simulations/#simulationsdataframe-class) using [the `sxs` package](https://github.com/sxs-collaboration/sxs/):
        ```python
        import sxs
        df = sxs.load("dataframe", tag="{tag_name}")
        ```

        That dataframe can be manipulated [as usual by pandas](https://pandas.pydata.org/pandas-docs/stable/user_guide/10min.html).
        See the [`sxs` documentation](https://sxs.readthedocs.io/en/main/tutorials/01-Simulations_and_Metadata/) for details about the metadata.

        Below, the dataframe is presented in graphical and tabular form, allowing you to explore it interactively.
        """
    ).style({"max-width": "725px", "margin": "0 auto"})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        rf"""
    ---
    The dataframe has several useful [attributes](https://sxs.readthedocs.io/en/main/api/simulations/#simulationsdataframe-class) that allow selecting important subsets of the data.  Use the buttons below to select those subsets.
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
    return deprecation, eccentricity, precession, system_type


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

    df.reset_index(names="SXS ID", inplace=True)
    return df, preferred_columns


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
        value="reference_chi1_perp",
        label="Marker size",
    )
    marker_color = mo.ui.dropdown(
        options=df.columns.to_list(),
        value="reference_chi2_perp",
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
    return (chart,)


@app.cell(hide_code=True)
def _(chart, mo):
    # Narrow dat the data further to just the data from (or selected in) the chart above
    chart_data = chart.value if len(chart.value) > 0 else chart.data

    (
        mo.md(
            "The following data can be further restricted by selecting a point or "
            "region on the plot; otherwise all data in the plot will be used."
        )
        if len(chart.value) == 0 else
        None
    )
    return (chart_data,)


@app.cell(hide_code=True)
def _(chart_data, math, mo, tag_name):
    # Show the code needed to load these simulations
    max_width = 6  # How many SXS IDs to allow on one line
    these_simulations =  ("this simulation" if len(chart_data)==1 else f"these {len(chart_data):,} simulations")
    load_code = (
        f"""import sxs\ndf = sxs.load("dataframe", tag="{tag_name}")\n"""
        + (
            f"""sim = sxs.load("{chart_data["SXS ID"][0]}")"""
            if len(chart_data)==1 else
            (
                "sims = [sxs.load(sxs_id) for sxs_id in [\"" + "\", \"".join(chart_data["SXS ID"]) + "\"]]"
                if len(chart_data) < max_width else
                (
                    "sims = [sxs.load(sxs_id) for sxs_id in [\n    \""
                    + "\",\n    \"".join(
                        "\", \"".join(chart_data["SXS ID"][i:min(i+max_width, len(chart_data["SXS ID"]))])
                        for i in range(0, math.ceil(len(chart_data["SXS ID"])/max_width)*max_width, max_width)
                    )
                    + "\"\n]]"
                )
            )
        )
    )
    final_table = (
        mo.ui.table(chart_data.drop("SXS ID", axis=1), page_size=20, show_download=False)
        if len(chart_data) > 0
        else mo.md("Select a region in the plot above to see details here")
    )

    mo.vstack([
        mo.md(f"You can load {these_simulations} with\n"),
        mo.md(f"```python\n{load_code}\n```\n\n").style({"max-height": "300px", "overflow": "auto"}),
        mo.md(f"The metadata summary table for that selection follows:\n{final_table}"),
    ])
    return


if __name__ == "__main__":
    app.run()
