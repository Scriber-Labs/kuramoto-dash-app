"""Unit tests for callback registrations and execution handlers."""

from __future__ import annotations

from dash import Dash

from app.callbacks import (
    register_callbacks,
)
from app.callbacks.dataset import handle_advance_animation, handle_toggle_animation
from app.callbacks.simulation import handle_run_or_reset, render_nyquist_banner
from app.callbacks.visualization import (
    handle_update_animation_visuals,
    handle_update_quantum_comparison_visual,
    handle_update_spectral_visual,
    handle_update_static_visuals,
    handle_update_symmetry_visual,
    handle_update_u1_visual,
    handle_update_visuals,
)
from app.services import collect_config, generate_dataset, package_simulation_payload


def test_nyquist_banner_callback_rendering() -> None:
    # Test undersampled rendering with RK45
    banner_under = render_nyquist_banner(
        dt=0.8,
        coupling=2.0,
        frequency_distribution="Normal",
        frequency_mean=0.0,
        frequency_std=2.0,
        custom_frequencies="",
        n_oscillators=24,
        seed=27,
        solver="RK45",
    )
    assert banner_under is not None
    assert "nyquist-warning" in banner_under.className

    # Test undersampled rendering with Euler (specific Euler warning message)
    banner_euler = render_nyquist_banner(
        dt=0.8,
        coupling=2.0,
        frequency_distribution="Normal",
        frequency_mean=0.0,
        frequency_std=2.0,
        custom_frequencies="",
        n_oscillators=24,
        seed=27,
        solver="Euler",
    )
    assert banner_euler is not None
    assert "nyquist-warning" in banner_euler.className

    # Test optimal rendering
    banner_opt = render_nyquist_banner(
        dt=0.05,
        coupling=2.0,
        frequency_distribution="Normal",
        frequency_mean=0.0,
        frequency_std=1.0,
        custom_frequencies="",
        n_oscillators=24,
        seed=27,
        solver="RK45",
    )
    assert banner_opt is not None
    assert "nyquist-success" in banner_opt.className


def test_register_callbacks() -> None:
    app = Dash(__name__)
    register_callbacks(app)
    assert len(app.callback_map) > 0


def test_simulation_callback_execution() -> None:
    # Test reset action
    data, max_f, val, status = handle_run_or_reset(
        triggered_id="reset-btn",
        n_oscillators=10,
        coupling=2.0,
        simulation_time=5.0,
        dt=0.1,
        seed=42,
        frequency_distribution="Normal",
        network_type="All-to-All",
        solver="RK45",
        frequency_mean=0.0,
        frequency_std=1.0,
        custom_frequencies="",
    )
    assert data is None
    assert max_f == 1
    assert val == 0
    assert "Ready" in status

    # Test run action with adaptive solver and symmetry tracking
    data, max_f, val, status = handle_run_or_reset(
        triggered_id="run-btn",
        n_oscillators=6,
        coupling=2.0,
        simulation_time=2.0,
        dt=0.1,
        seed=42,
        frequency_distribution="Normal",
        network_type="Ring",
        solver="dopri54",
        frequency_mean=0.0,
        frequency_std=1.0,
        custom_frequencies="",
        track_symmetries=["track"],
        adaptive_rtol=1e-5,
        adaptive_atol=1e-7,
        dt_min=1e-4,
        dt_max=0.5,
    )
    assert data is not None
    assert "time" in data
    assert "symmetries" in data
    assert data["symmetries"] is not None
    assert max_f > 0
    assert "Generated" in status


def test_visualization_callback_execution() -> None:
    # Test empty state
    res_empty = handle_update_visuals(data=None, frame=0)
    assert len(res_empty) == 7

    # Test populated state
    cfg = collect_config(4, 1.0, 1.0, 0.1, 42, "Normal", "Ring", "rkmk4")
    ds = generate_dataset(**cfg)
    payload = package_simulation_payload(ds, cfg)

    res_populated = handle_update_visuals(data=payload, frame=2)
    assert len(res_populated) == 7
    # Verify all figure outputs are valid Plotly figures
    for fig in res_populated[:6]:
        assert hasattr(fig, "to_plotly_json")

    # Test separated animation and static visual handlers
    anim_res = handle_update_animation_visuals(payload, frame=2)
    assert len(anim_res) == 3
    assert hasattr(anim_res[0], "to_plotly_json")  # Unit circle
    assert hasattr(anim_res[1], "to_plotly_json")  # Order plot

    static_res = handle_update_static_visuals(payload)
    assert len(static_res) == 4
    for fig in static_res:
        assert hasattr(fig, "to_plotly_json")

    # Test symmetry, U(1), spectral, and quantum visual handlers
    sym_fig = handle_update_symmetry_visual(payload, frame=2)
    assert hasattr(sym_fig, "to_plotly_json")

    u1_fig = handle_update_u1_visual(payload)
    assert hasattr(u1_fig, "to_plotly_json")

    spectral_fig = handle_update_spectral_visual(payload)
    assert hasattr(spectral_fig, "to_plotly_json")

    quantum_fig = handle_update_quantum_comparison_visual(payload)
    assert hasattr(quantum_fig, "to_plotly_json")


def test_dataset_callback_handlers() -> None:
    data = {"time": [0.0, 0.1, 0.2, 0.3]}
    assert handle_advance_animation(data, 0) == 1
    assert handle_advance_animation(data, 3) == 0

    disabled, text = handle_toggle_animation("run-btn", True)
    assert disabled is False
    assert text == "Pause animation"

    disabled, text = handle_toggle_animation("reset-btn", False)
    assert disabled is True
    assert text == "Play animation"
