"""UI Control components for simulation inputs and timeline scrubbing."""

from __future__ import annotations

from typing import Any

from dash import dcc, html

from app.config import DEFAULTS, MAX_OSCILLATORS, MIN_OSCILLATORS
from app.services.solvers import SolverRegistry


def control_group(label: str, component: Any, hint: str | None = None, group_id: str | None = None) -> html.Div:
    """Wrap a form input component with a styled label and optional hint."""
    children = [html.Label(label, className="field-label"), component]
    if hint:
        children.append(html.Small(hint, className="field-hint"))
    kwargs = {"className": "field"}
    if group_id:
        kwargs["id"] = group_id
    return html.Div(children, **kwargs)


def sidebar_controls() -> html.Aside:
    """Build the configuration sidebar panel with all interactive inputs and buttons."""
    solver_options = SolverRegistry.get_grouped_options()

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
                "Numerical Integrator / Solver",
                dcc.Dropdown(
                    id="solver",
                    options=solver_options,
                    value=DEFAULTS["solver"],
                    className="dash-dropdown solver-dropdown",
                    clearable=False,
                ),
                hint="Grouped by Classical, GA Mean-Field, Lie Group, and Quantum SCF paradigms.",
            ),
            # Conditional Adaptive Solver Controls Panel
            html.Div(
                id="adaptive-solver-panel",
                children=[
                    html.Div(
                        [
                            html.P("Adaptive Lie Step Controls", className="eyebrow", style={"fontSize": "11px", "marginBottom": "4px"}),
                            html.Div(
                                [
                                    control_group(
                                        "Rel Tol (rtol)",
                                        dcc.Input(
                                            id="adaptive-rtol",
                                            type="number",
                                            min=1e-12,
                                            max=1e-1,
                                            step=1e-6,
                                            value=DEFAULTS.get("adaptive_rtol", 1e-5),
                                        ),
                                    ),
                                    control_group(
                                        "Abs Tol (atol)",
                                        dcc.Input(
                                            id="adaptive-atol",
                                            type="number",
                                            min=1e-12,
                                            max=1e-1,
                                            step=1e-8,
                                            value=DEFAULTS.get("adaptive_atol", 1e-7),
                                        ),
                                    ),
                                ],
                                className="field-row",
                            ),
                            html.Div(
                                [
                                    control_group(
                                        "dt min",
                                        dcc.Input(
                                            id="dt-min",
                                            type="number",
                                            min=1e-6,
                                            max=0.1,
                                            step=1e-4,
                                            value=DEFAULTS.get("dt_min", 1e-4),
                                        ),
                                    ),
                                    control_group(
                                        "dt max",
                                        dcc.Input(
                                            id="dt-max",
                                            type="number",
                                            min=1e-3,
                                            max=2.0,
                                            step=0.01,
                                            value=DEFAULTS.get("dt_max", 0.5),
                                        ),
                                    ),
                                ],
                                className="field-row",
                            ),
                        ],
                        className="solver-subpanel",
                    )
                ],
                style={"display": "none"},
            ),
            # Conditional Quantum Solver Controls Panel
            html.Div(
                id="quantum-solver-panel",
                children=[
                    html.Div(
                        [
                            html.P("Quantum SCF & NISQ Noise", className="eyebrow", style={"fontSize": "11px", "marginBottom": "4px"}),
                            control_group(
                                "NISQ Projective Shots",
                                dcc.Slider(
                                    id="shots-slider",
                                    min=128,
                                    max=8192,
                                    step=128,
                                    value=DEFAULTS.get("shots", 1024),
                                    marks={
                                        128: "128",
                                        1024: "1k",
                                        2048: "2k",
                                        4096: "4k",
                                        8192: "8k",
                                    },
                                    tooltip={"placement": "bottom", "always_visible": False},
                                ),
                                "Simulates hardware shot noise on N-qubit state measurement.",
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "Export OpenQASM",
                                        id="export-qasm-btn",
                                        className="button button-secondary btn-hover color-9",
                                        style={"width": "100%", "marginTop": "6px", "fontSize": "12px", "padding": "6px 12px"},
                                    ),
                                    dcc.Download(id="download-qasm"),
                                ],
                                style={"marginTop": "6px"},
                            ),
                            html.Div(
                                id="qasm-viewer-container",
                                children=[
                                    dcc.Textarea(
                                        id="qasm-code-display",
                                        readOnly=True,
                                        style={
                                            "width": "100%",
                                            "height": "90px",
                                            "fontSize": "11px",
                                            "fontFamily": "monospace",
                                            "backgroundColor": "rgba(10, 14, 24, 0.8)",
                                            "color": "#00e8ff",
                                            "border": "1px solid rgba(0, 232, 255, 0.2)",
                                            "borderRadius": "4px",
                                            "marginTop": "8px",
                                            "display": "none",
                                        },
                                    ),
                                ],
                            ),
                        ],
                        className="solver-subpanel",
                    )
                ],
                style={"display": "none"},
            ),
            html.Div(
                id="rotor-symmetry-toggle-group",
                children=[
                    dcc.Checklist(
                        id="track-symmetries",
                        options=[
                            {
                                "label": " Track Lie symmetries & U(1) Noether charges",
                                "value": "track",
                            }
                        ],
                        value=["track"] if DEFAULTS.get("track_symmetries", False) else [],
                        className="symmetry-checklist",
                        inputClassName="checklist-input",
                    ),
                ],
                className="field",
                style={"marginTop": "-4px", "marginBottom": "12px"},
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
                        className="button button-play animation-button btn-hover color-11",
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
