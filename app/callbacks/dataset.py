"""Dataset export and animation playback callbacks."""

from __future__ import annotations

from typing import Any

from dash import Dash, Input, Output, State, ctx, dcc, no_update

from app.services.benchmark import export_dataset_npz


def handle_advance_animation(
    stored_data: dict[str, Any] | None,
    current_frame: int | None,
) -> Any:
    """Advance current frame index by 1 or loop back to 0."""
    if not stored_data:
        return no_update
    max_frame = max(0, len(stored_data.get("time", [])) - 1)
    current = max(0, min(int(current_frame or 0), max_frame))
    return 0 if current >= max_frame else current + 1


def handle_toggle_animation(
    triggered_id: str | None,
    is_disabled: bool,
) -> tuple[bool, str]:
    """Toggle play/pause animation heartbeat state."""
    if triggered_id == "run-btn":
        return False, "Pause animation"
    if triggered_id == "reset-btn":
        return True, "Play animation"
    next_disabled = not bool(is_disabled)
    return next_disabled, "Play animation" if next_disabled else "Pause animation"


def register_dataset_callbacks(app: Dash) -> None:
    """Register animation progression and benchmark download callbacks."""

    @app.callback(
        Output("time-slider-label", "children"),
        Input("time-slider", "value"),
        State("simulation-store", "data"),
    )
    def update_time_label(
        frame: int | None,
        stored_data: dict[str, Any] | None,
    ) -> str:
        """Display the actual time value corresponding to the current slider frame."""
        if not stored_data or "time" not in stored_data or not stored_data["time"]:
            return "t = 0.00s"
        time_arr = stored_data["time"]
        idx = max(0, min(int(frame or 0), len(time_arr) - 1))
        return f"t = {float(time_arr[idx]):.2f}s"

    @app.callback(
        Output("time-slider", "value", allow_duplicate=True),
        Input("heartbeat", "n_intervals"),
        State("simulation-store", "data"),
        State("time-slider", "value"),
        prevent_initial_call=True,
    )
    def advance_animation(
        _: int | None,
        stored_data: dict[str, Any] | None,
        current_frame: int | None,
    ) -> Any:
        return handle_advance_animation(stored_data, current_frame)

    @app.callback(
        Output("heartbeat", "disabled"),
        Output("play-btn", "children"),
        Input("play-btn", "n_clicks"),
        Input("run-btn", "n_clicks"),
        Input("reset-btn", "n_clicks"),
        State("heartbeat", "disabled"),
        prevent_initial_call=True,
    )
    def toggle_animation(
        _: int | None,
        __: int | None,
        ___: int | None,
        is_disabled: bool,
    ) -> tuple[bool, str]:
        return handle_toggle_animation(getattr(ctx, "triggered_id", None), is_disabled)

    @app.callback(
        Output("dataset-download", "data"),
        Input("download-btn", "n_clicks"),
        State("simulation-store", "data"),
        prevent_initial_call=True,
    )
    def download_dataset(_: int | None, data: dict[str, Any] | None) -> Any:
        if not data:
            return None

        dataset_data: dict[str, Any] = data

        def write_dataset(file_object: Any) -> None:
            export_dataset_npz(dataset_data, file_object)

        return dcc.send_bytes(write_dataset, "kuramoto_benchmark.npz")
