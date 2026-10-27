"""JSON configuration, collapsible sections, and solver sync callbacks."""

from __future__ import annotations

import json
from typing import Any, Tuple

from dash import Dash, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate

from app.config import DEFAULTS


# 0️⃣ JSON Examples

_JSON_EXAMPLE_BASIC = {
    "n_oscillators": 24,
    "coupling": 2.0,
    "simulation_time": 50.0,
    "dt": 0.05,
    "seed": 27,
    "frequency_distribution": "Normal",
    "frequency_mean": 0.0,
    "frequency_std": 1.0,
    "network_type": "All-to-All",
    "solver": "rk45",
}

_JSON_EXAMPLE_ADVANCED = {
    "n_oscillators": 50,
    "coupling": 3.5,
    "simulation_time": 100.0,
    "dt": 0.02,
    "seed": 42,
    "frequency_distribution": "Bimodal",
    "frequency_mean": 0.0,
    "frequency_std": 0.5,
    "network_type": "Small-World",
    "solver": "dopri54",
    "track_symmetries": True,
}

_JSON_EXAMPLE_CUSTOM_FREQ = {
    "n_oscillators": 10,
    "coupling": 1.5,
    "simulation_time": 30.0,
    "dt": 0.05,
    "seed": 7,
    "frequency_distribution": "Custom",
    "custom_frequencies": "-2, -1, -0.5, 0, 0.5, 1, 2, 3, 4, 5",
    "network_type": "Ring",
    "solver": "euler",
}


# 1️⃣ Public Helpers

def _parse_json_config(json_str: str) -> Tuple[dict[str, Any], str | None]:
    """Parse a JSON string into a config dict. Returns (config, error_message)."""
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return {}, "JSON must be an object ({}), not an array or primitive."
        return data, None
    except json.JSONDecodeError as exc:
        return {}, f"Invalid JSON: {exc}"


def _build_status(message: str, success: bool = True) -> html.Div:
    """Build a status message component."""
    icon = "✓" if success else "✗"
    color = "#22f792" if success else "#f78166"
    return html.Div(
        f"{icon} {message}",
        style={
            "fontSize": "12px",
            "color": color,
            "padding": "6px 10px",
            "borderRadius": "4px",
            "backgroundColor": f"{color}15",
            "border": f"1px solid {color}40",
        },
    )


def _build_error_status(message: str) -> html.Div:
    """Build an error status component."""
    return _build_status(message, success=False)


# 2️⃣ Internal Callback Logic

def register_json_callbacks(app: Dash) -> None:
    """Register JSON config import/export, example loading, and collapsible section callbacks."""

    # ── Apply JSON Config ──
    @app.callback(
        Output("n-oscillators", "value", allow_duplicate=True),
        Output("coupling", "value", allow_duplicate=True),
        Output("simulation-time", "value", allow_duplicate=True),
        Output("dt", "value", allow_duplicate=True),
        Output("seed", "value", allow_duplicate=True),
        Output("frequency-distribution", "value", allow_duplicate=True),
        Output("frequency-mean", "value", allow_duplicate=True),
        Output("frequency-std", "value", allow_duplicate=True),
        Output("custom-frequencies", "value", allow_duplicate=True),
        Output("network-type", "value", allow_duplicate=True),
        Output("solver", "value", allow_duplicate=True),
        Output("solver-hero", "value", allow_duplicate=True),
        Output("json-config-input", "value"),
        Output("json-config-status", "children"),
        Input("apply-json-btn", "n_clicks"),
        State("json-config-input", "value"),
        prevent_initial_call=True,
    )
    def apply_json_config(
        n_clicks: int | None,
        json_str: str | None,
    ):
        """Parse JSON and update all input fields."""
        if not json_str or not json_str.strip():
            raise PreventUpdate

        data, error = _parse_json_config(json_str.strip())
        if error:
            # Return current values unchanged + error status
            raise PreventUpdate

        # Extract values with defaults
        n_osc = int(data.get("n_oscillators", DEFAULTS["n_oscillators"]))
        coupling = float(data.get("coupling", DEFAULTS["coupling"]))
        sim_time = float(data.get("simulation_time", DEFAULTS["simulation_time"]))
        dt_val = float(data.get("dt", DEFAULTS["dt"]))
        seed_val = int(data.get("seed", DEFAULTS["seed"]))
        freq_dist = data.get("frequency_distribution", DEFAULTS["frequency_distribution"])
        freq_mean = float(data.get("frequency_mean", DEFAULTS["frequency_mean"]))
        freq_std = float(data.get("frequency_std", DEFAULTS["frequency_std"]))
        custom_freq = data.get("custom_frequencies", DEFAULTS["custom_frequencies"])
        network = data.get("network_type", DEFAULTS["network_type"])
        solver_val = data.get("solver", DEFAULTS["solver"])

        # Normalize network type for dropdown matching
        network_map = {
            "all-to-all": "All-to-All",
            "all_to_all": "All-to-All",
            "ring": "Ring",
            "nearest-neighbor": "Ring",
            "nearest_neighbor": "Ring",
            "random": "Random",
            "small-world": "Small-World",
            "small_world": "Small-World",
            "tree-of-life": "Tree of Life",
            "tree_of_life": "Tree of Life",
            "custom": "Custom Adjacency",
            "custom-adjacency": "Custom Adjacency",
            "custom_adjacency": "Custom Adjacency",
        }
        network_key = network.lower().replace(" ", "_")
        network_display = network_map.get(network_key, network)

        status = _build_status(f"Applied config: {n_osc} oscillators, K={coupling}, {solver_val}")

        return (
            n_osc,
            coupling,
            sim_time,
            dt_val,
            seed_val,
            freq_dist,
            freq_mean,
            freq_std,
            custom_freq,
            network_display,
            solver_val,
            solver_val,
            json_str,  # Keep textarea value
            status,
        )

    # ── Export Current Config as JSON ──
    @app.callback(
        Output("json-config-input", "value", allow_duplicate=True),
        Output("json-config-status", "children", allow_duplicate=True),
        Input("export-json-btn", "n_clicks"),
        State("n-oscillators", "value"),
        State("coupling", "value"),
        State("simulation-time", "value"),
        State("dt", "value"),
        State("seed", "value"),
        State("frequency-distribution", "value"),
        State("frequency-mean", "value"),
        State("frequency-std", "value"),
        State("custom-frequencies", "value"),
        State("network-type", "value"),
        State("solver", "value"),
        prevent_initial_call=True,
    )
    def export_json_config(
        n_clicks: int | None,
        n_osc, coupling, sim_time, dt_val, seed_val,
        freq_dist, freq_mean, freq_std, custom_freq,
        network, solver_val,
    ):
        """Export current input values as formatted JSON."""
        config = {
            "n_oscillators": n_osc,
            "coupling": coupling,
            "simulation_time": sim_time,
            "dt": dt_val,
            "seed": seed_val,
            "frequency_distribution": freq_dist,
            "frequency_mean": freq_mean,
            "frequency_std": freq_std,
        }
        if custom_freq:
            config["custom_frequencies"] = custom_freq
        config["network_type"] = network
        config["solver"] = solver_val

        json_str = json.dumps(config, indent=2)
        status = _build_status("Current config exported to JSON textarea")
        return json_str, status

    # ── Load JSON Examples ──
    @app.callback(
        Output("json-config-input", "value", allow_duplicate=True),
        Output("json-example-display", "children", allow_duplicate=True),
        Output("json-config-status", "children", allow_duplicate=True),
        Input("json-example-basic", "n_clicks"),
        Input("json-example-advanced", "n_clicks"),
        Input("json-example-custom", "n_clicks"),
        State("json-config-input", "value"),
        prevent_initial_call=True,
    )
    def load_json_example(
        basic_clicks, advanced_clicks, custom_clicks,
        current_value,
    ):
        """Load a JSON example into the textarea."""
        triggered_id = ctx.triggered_id if hasattr(ctx, 'triggered_id') else None

        if triggered_id == "json-example-basic":
            example = _JSON_EXAMPLE_BASIC
            label = "Basic"
        elif triggered_id == "json-example-advanced":
            example = _JSON_EXAMPLE_ADVANCED
            label = "Advanced"
        elif triggered_id == "json-example-custom":
            example = _JSON_EXAMPLE_CUSTOM_FREQ
            label = "Custom Freq"
        else:
            raise PreventUpdate

        json_str = json.dumps(example, indent=2)
        status = _build_status(f"Loaded {label} example — click 'Apply Config' to use")
        return (
            json_str,
            html.Pre(
                json_str,
                style={
                    "fontSize": "10px",
                    "fontFamily": "'Fira Code', monospace",
                    "backgroundColor": "rgba(0, 0, 0, 0.3)",
                    "color": "#8b949e",
                    "padding": "8px",
                    "borderRadius": "4px",
                    "overflow": "auto",
                    "maxHeight": "150px",
                    "whiteSpace": "pre-wrap",
                    "wordBreak": "break-word",
                },
            ),
            status,
        )

    # ── Collapsible Section Toggles ──
    @app.callback(
        Output("content-core", "style", allow_duplicate=True),
        Output("toggle-core-icon", "children", allow_duplicate=True),
        Input("toggle-core", "n_clicks"),
        State("content-core", "style"),
        prevent_initial_call=True,
    )
    def toggle_core(n_clicks: int | None, current_style: dict | None):
        """Toggle Core Parameters section."""
        if current_style is None:
            current_style = {"display": "block"}
        is_visible = current_style.get("display", "block") != "none"
        return (
            {"display": "none" if is_visible else "block"},
            "▸" if not is_visible else "▾",
        )

    @app.callback(
        Output("content-network", "style", allow_duplicate=True),
        Output("toggle-network-icon", "children", allow_duplicate=True),
        Input("toggle-network", "n_clicks"),
        State("content-network", "style"),
        prevent_initial_call=True,
    )
    def toggle_network(n_clicks: int | None, current_style: dict | None):
        """Toggle Network & Frequencies section."""
        if current_style is None:
            current_style = {"display": "none"}
        is_visible = current_style.get("display", "none") != "none"
        return (
            {"display": "none" if is_visible else "block"},
            "▸" if not is_visible else "▾",
        )

    @app.callback(
        Output("content-advanced", "style", allow_duplicate=True),
        Output("toggle-advanced-icon", "children", allow_duplicate=True),
        Input("toggle-advanced", "n_clicks"),
        State("content-advanced", "style"),
        prevent_initial_call=True,
    )
    def toggle_advanced(n_clicks: int | None, current_style: dict | None):
        """Toggle Advanced Options section."""
        if current_style is None:
            current_style = {"display": "none"}
        is_visible = current_style.get("display", "none") != "none"
        return (
            {"display": "none" if is_visible else "block"},
            "▸" if not is_visible else "▾",
        )

    # ── Sync Hero Solver with Sidebar Solver ──
    @app.callback(
        Output("solver", "value", allow_duplicate=True),
        Input("solver-hero", "value"),
        prevent_initial_call=True,
    )
    def sync_hero_to_sidebar_solver(hero_solver: str | None):
        """Sync hero solver dropdown to sidebar solver dropdown."""
        if hero_solver is None:
            raise PreventUpdate
        return hero_solver

    @app.callback(
        Output("solver-hero", "value", allow_duplicate=True),
        Input("solver", "value"),
        prevent_initial_call=True,
    )
    def sync_sidebar_to_hero_solver(sidebar_solver: str | None):
        """Sync sidebar solver dropdown to hero solver dropdown."""
        if sidebar_solver is None:
            raise PreventUpdate
        return sidebar_solver
