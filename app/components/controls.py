"""UI Control components for simulation inputs and timeline scrubbing."""

from __future__ import annotations

from typing import Any

from dash import dcc, html

from app.config import DEFAULTS, MAX_OSCILLATORS, MIN_OSCILLATORS


def control_group(label: str, component: Any, hint: str | None = None) -> html.Div:
    """Wrap a form input component with a styled label and optional hint."""
    children = [html.Label(label, className="field-label"), component]
    if hint:
        children.append(html.Small(hint, className="field-hint"))
    return html.Div(children, className="field")


def sidebar_controls() -> html.Aside:
    """Build the configuration sidebar panel with all interactive inputs and buttons."""
    return html.Aside(
        [
            html.Div(
                [
                    html.P("Simulation parameters", className="eyebrow"),
                    html.H3("Configure a run"),
                ],
                className="panel-heading",
            ),
            control_group(
                "Network",
                dcc.Dropdown(
                    id="network-type",
                    className="dash-dropdown",
                    options=[
                        {"label": "All-to-All", "value": "All-to-All"},
                        {"label": "Ring / Nearest Neighbor", "value": "Ring"},
                        {"label": "Random Sparse", "value": "Random"},
                        {
                            "label": "Small-World (Watts-Strogatz)",
                            "value": "Small-World",
                        },
                        {"label": "Tree of Life (Etz Hayim)", "value": "Tree of Life"},
                        {
                            "label": "Custom Adjacency Matrix",
                            "value": "Custom Adjacency",
                        },
                    ],
                    value=DEFAULTS["network_type"],
                    clearable=False,
                ),
            ),
            control_group(
                "Custom Adjacency Matrix (Rows/CSV/JSON)",
                dcc.Textarea(
                    id="custom-adjacency",
                    value=DEFAULTS["custom_adjacency"],
                    placeholder="0 1 1\n1 0 1\n1 1 0",
                    style={"width": "100%", "height": "60px", "fontSize": "12px"},
                ),
                "Used when Custom Adjacency Matrix is selected.",
            ),
            html.Div(
                [
                    control_group(
                        "Oscillators",
                        dcc.Input(
                            id="n-oscillators",
                            type="number",
                            min=MIN_OSCILLATORS,
                            max=MAX_OSCILLATORS,
                            step=1,
                            value=DEFAULTS["n_oscillators"],
                        ),
                    ),
                    control_group(
                        "Coupling K",
                        dcc.Input(
                            id="coupling",
                            type="number",
                            min=0,
                            max=20,
                            step=0.1,
                            value=DEFAULTS["coupling"],
                        ),
                    ),
                ],
                className="field-row",
            ),
            html.Div(
                [
                    control_group(
                        "Simulation time",
                        dcc.Input(
                            id="simulation-time",
                            type="number",
                            min=1,
                            max=500,
                            step=1,
                            value=DEFAULTS["simulation_time"],
                        ),
                    ),
                    control_group(
                        "Time step",
                        dcc.Input(
                            id="dt",
                            type="number",
                            min=0.001,
                            max=1.0,
                            step=0.005,
                            value=DEFAULTS["dt"],
                        ),
                    ),
                ],
                className="field-row",
            ),
            html.Div(
                id="nyquist-warning-banner",
                className="nyquist-banner nyquist-optimal",
            ),
            control_group(
                "Solver",
                dcc.RadioItems(
                    id="solver",
                    options=[
                        {"label": "RK45", "value": "RK45"},
                        {"label": "Euler", "value": "Euler"},
                        {"label": "Rotor (GA Cl(2))", "value": "Rotor"},
                    ],
                    value=DEFAULTS["solver"],
                    className="radio-row",
                    inputClassName="radio-input",
                ),
            ),
            control_group(
                "Natural frequencies",
                dcc.Dropdown(
                    id="frequency-distribution",
                    className="dash-dropdown",
                    options=[
                        {"label": "Normal", "value": "Normal"},
                        {"label": "Uniform", "value": "Uniform"},
                        {"label": "Bimodal", "value": "Bimodal"},
                        {"label": "Golden ratio sequence", "value": "Golden Ratio"},
                        {"label": "Custom values", "value": "Custom"},
                    ],
                    value=DEFAULTS["frequency_distribution"],
                    clearable=False,
                ),
            ),
            html.Div(
                [
                    control_group(
                        "Mean",
                        dcc.Input(
                            id="frequency-mean", type="number", step=0.1, value=0.0
                        ),
                    ),
                    control_group(
                        "Std. dev.",
                        dcc.Input(
                            id="frequency-std",
                            type="number",
                            min=0.01,
                            step=0.1,
                            value=1.0,
                        ),
                    ),
                ],
                className="field-row",
            ),
            control_group(
                "Custom values (comma-separated)",
                dcc.Input(
                    id="custom-frequencies",
                    type="text",
                    value=DEFAULTS["custom_frequencies"],
                ),
                "Used when Custom values is selected.",
            ),
            control_group(
                "Random seed",
                dcc.Input(
                    id="seed",
                    type="number",
                    min=0,
                    max=999999,
                    step=1,
                    value=DEFAULTS["seed"],
                ),
                "Same seed = same dataset.",
            ),
            html.Div(
                [
                    html.P("Benchmark export", className="eyebrow"),
                    html.P(
                        "The current run uses the benchmark-suite schema and can be downloaded "
                        "as a compressed NumPy archive.",
                        className="panel-note",
                    ),
                    html.Button(
                        "Download .npz dataset",
                        id="download-btn",
                        className="button button-secondary btn-hover color-4",
                    ),
                ],
                className="export-card",
            ),
        ],
        className="control-panel",
    )


def timeline_controls() -> html.Div:
    """Build the timeline scrubber card with simulation triggers, slider, and animation toggle button."""
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Button(
                                "Run simulation",
                                id="run-btn",
                                className="button button-primary btn-hover color-1",
                            ),
                            html.Button(
                                "Reset",
                                id="reset-btn",
                                className="button button-quiet btn-hover color-3",
                            ),
                        ],
                        className="button-row timeline-btn-group",
                        style={"margin": "0", "display": "flex", "gap": "10px"},
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Inspect time slice",
                                className="field-label",
                                style={"marginBottom": "4px"},
                            ),
                            dcc.Slider(
                                id="time-slider",
                                min=0,
                                max=1,
                                value=0,
                                step=1,
                                updatemode="drag",
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                        ],
                        className="timeline-slider-group",
                        style={"flex": "1", "minWidth": "240px"},
                    ),
                    html.Button(
                        "Pause animation",
                        id="play-btn",
                        className="button button-play animation-button btn-hover color-5",
                    ),
                ],
                className="timeline-controls",
            ),
            dcc.Loading(
                id="loading-simulation",
                type="dot",
                color="#00e8ff",
                className="simulation-loader",
                children=html.Div(id="run-status", className="run-status"),
            ),
        ],
        className="timeline-card",
    )
