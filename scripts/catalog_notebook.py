# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair==5.5.0",
#     "anywidget==0.9.15",
#     "marimo",
#     "numpy==2.1.3",
#     "pandas==2.2.3",
#     "plotly==6.0.0",
#     "pyarrow==19.0.1",
#     "sxs==2024.0.44",
#     "traitlets==5.14.3",
# ]
# ///

import marimo

__generated_with = "0.11.17"
app = marimo.App(
    width="full",
    app_title="SXS Catalog",
    css_file="",
    html_head_file="",
)


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import traitlets
    import anywidget

    class CopyToClipboard(anywidget.AnyWidget):
        """Initialize a CopyToClipboard widget.

        Args:
            text_to_copy: String to copy to the clipboard when button is pressed.
        """
        text_to_copy = traitlets.Unicode("").tag(sync=True)
        top = traitlets.Unicode("").tag(sync=True)
        right = traitlets.Unicode("").tag(sync=True)

        _esm = """
        function render({ model, el }) {
            // Create a button element
            const button = document.createElement("button");
            button.innerHTML = `
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-clipboard-copy">
                <rect width="8" height="4" x="8" y="2" rx="1" ry="1"></rect>
                <path d="M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"></path>
                <path d="M16 4h2a2 2 0 0 1 2 2v4"></path>
                <path d="M21 14H11"></path>
                <path d="m15 10-4 4 4 4"></path>
              </svg>
            `;
            button.style.position = "absolute";
            button.style.top = model.get("top");
            button.style.right = model.get("right");

            // Add a click event listener to the button
            button.addEventListener("click", async () => {
                try {
                    // Copy the text to the clipboard
                    await navigator.clipboard.writeText(model.get("text_to_copy"));
                    console.log("Text copied to clipboard:", model.get("text_to_copy"));

                    // Change the button icon to a check mark for 1 second
                    const originalIcon = button.innerHTML;
                    button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check"><path d="M20 6L9 17l-5-5"/></svg>';
                    setTimeout(() => {
                        button.innerHTML = originalIcon;
                    }, 1000);
                } catch (err) {
                    console.error("Failed to copy text:", err);
                }
            });

            // Append the button to the widget's element
            el.appendChild(button);
        };

        export default {render};
        """

        def __init__(self, text_to_copy="", top="4em", right="0.5em", **kwargs):
            super().__init__(**kwargs)
            self.text_to_copy = text_to_copy
            self.top = top
            self.right = right
    return CopyToClipboard, anywidget, mo, traitlets


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
        """
    ).style({"width": "80%", "margin": "0 auto"})
    return


@app.cell(hide_code=True)
def _():
    ### NOTE: This cell is hidden from the user in marimo's "app view".
    ### These commands are mostly here for nicer display; actual users
    ### will probably only need the commands mentioned above.

    import sxs
    import numpy as np
    import math
    import warnings
    import pyarrow  # For efficient dataframe manipulation
    import pandas as pd

    # TODO: Pick which one of these is better
    import plotly.express as px
    import altair as alt

    sim = sxs.load("simulations", local=True)
    df0 = sim.dataframe  # We filter this below

    # The df object is actually a sxs.SimulationsDataFrame (so that we can have attributes like df.BBH),
    # which subclasses — but is not a — pd.DataFrame, so the fancy display doesn't work directly.
    #
    # Fortunately, we can get the fancy display either by callingmo.ui.dataame(df) or by acting on df
    # with some function that returns a regular pd.DataFrame.
    return alt, df0, math, np, pd, px, pyarrow, sim, sxs, warnings


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---

        The dataframe has several [useful attributes](https://sxs.readthedocs.io/en/main/api/simulations/#simulationsdataframe-class) that allow selecting important subsets of the data.  Use the radio buttons below to select those attributes.
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
        "We now plot selected columns from the filtered data above."
        + (
            "  If you have selected checkboxes in the table, only those will be plotted."
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

    mo.md("The following data can be further restricted by selecting a point or region on the plot; otherwise all data in the plot will be used.")
    return (chart_data,)


@app.cell(hide_code=True)
def _(CopyToClipboard, chart_data, math, mo):
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
    copy_load_code = CopyToClipboard(load_code, top="4.25em", right="0.85em")
    (
        mo.vstack([
            mo.md(f"You can load {these_simulations} with\n```python\n{load_code}\n```").style({"max-height": "300px"}),
            copy_load_code
        ]).style({"position": "relative", "overflow": "auto"})
        if len(chart_data) > 0
        else None
    )
    return copy_load_code, load_code, max_width, these_simulations


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""The following table shows only the data selected in the plot above.""")
    return


@app.cell(hide_code=True)
def _(chart_data, mo):
    (
        mo.ui.table(chart_data.drop("SXS ID", axis=1), page_size=20)
        if len(chart_data) > 0
        else mo.md("Select a region in the plot above to see details here")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---

        The following plot is just to show that plotly can do much the same things that altair can do.

          * Advantage: plotly has a clearer interface, with little icons to click to zoom, etc.
          * Advantage: plotly has a lasso selection option, which is cool
          * Disadvantage: it does not show a legend for marker sizes

        I have to think about whether it's worth it to try to make plotly work as well as altair.
        """
    )
    return


@app.cell(hide_code=True)
def _(
    horizontal_axis,
    marker_color,
    marker_size,
    mo,
    np,
    px,
    table_data,
    used_selectors,
    vertical_axis,
):
    # used_selectors = [s.value for s in selectors if s.value is not None]
    # df_restricted = table_data[used_selectors]
    kwargs2 = dict(
        x=horizontal_axis.value,
        y=vertical_axis.value,
        hover_data=used_selectors,
    )
    if marker_size.value is not None:
        kwargs2["size"] = table_data[marker_size.value].replace(np.nan, table_data[marker_size.value].median())
    if marker_color.value is not None:
        kwargs2["color"] = marker_color.value

    _plot = px.scatter(
        table_data, **kwargs2
    )

    plot = mo.ui.plotly(_plot)
    plot
    return kwargs2, plot


if __name__ == "__main__":
    app.run()
