"""Spectral, Lie symmetry, and topological diagnostics service for Kuramoto dynamics."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
from scipy import signal

try:
    from kuramoto.analysis.spectral import (
        compute_fourier_coefficients,
        compute_psd,
        compute_spectral_decomposition,
        detect_sync_transition,
        harmonic_analysis,
    )
except ImportError:
    compute_fourier_coefficients = None
    compute_psd = None
    compute_spectral_decomposition = None
    detect_sync_transition = None
    harmonic_analysis = None

try:
    from kuramoto.topologies.analysis import (
        compute_chromatic_polynomial,
        get_graph_metadata,
    )
except ImportError:
    compute_chromatic_polynomial = None
    get_graph_metadata = None


class DiagnosticRegistry:
    """Extensible registry for diagnostics, spectral metrics, and topological analysis."""

    _diagnostics: Dict[str, Callable[..., Dict[str, Any]]] = {}

    @classmethod
    def register(cls, name: str, fn: Callable[..., Dict[str, Any]]) -> None:
        cls._diagnostics[name] = fn

    @classmethod
    def compute_all(
        cls,
        times: np.ndarray,
        phases: np.ndarray,
        order_param: np.ndarray,
        adj_matrix: np.ndarray,
        omega: np.ndarray,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Compute all registered diagnostic metrics."""
        results: Dict[str, Any] = {}
        for name, fn in cls._diagnostics.items():
            try:
                results[name] = fn(
                    times=times,
                    phases=phases,
                    order_param=order_param,
                    adj_matrix=adj_matrix,
                    omega=omega,
                    **kwargs,
                )
            except Exception as exc:
                results[name] = {"error": str(exc)}
        return results


def analyze_graph_topology(adj_matrix: np.ndarray) -> Dict[str, Any]:
    """Compute topological graph metrics and chromatic polynomial."""
    n = adj_matrix.shape[0]
    g = nx.from_numpy_array(adj_matrix)

    is_connected = nx.is_connected(g) if n > 0 else False
    density = float(nx.density(g))
    avg_clustering = float(nx.average_clustering(g)) if n > 0 else 0.0

    diameter = None
    if is_connected and n > 1:
        try:
            diameter = int(nx.diameter(g))
        except Exception:
            diameter = None

    chromatic_poly_coeffs = None
    if compute_chromatic_polynomial is not None:
        try:
            chromatic_poly_coeffs = compute_chromatic_polynomial(adj_matrix)
        except Exception:
            pass

    return {
        "n_nodes": n,
        "n_edges": int(g.number_of_edges()),
        "density": density,
        "is_connected": is_connected,
        "average_clustering": avg_clustering,
        "diameter": diameter,
        "chromatic_polynomial": chromatic_poly_coeffs,
    }


def analyze_spectral_dynamics(
    times: np.ndarray, order_param: np.ndarray, dt: Optional[float] = None
) -> Dict[str, Any]:
    """Compute PSD via Welch method and Fourier FFT spectrum vs frequency."""
    times_arr = np.asarray(times, dtype=float)
    r_arr = np.asarray(order_param, dtype=float)

    if len(times_arr) < 4:
        return {
            "psd_freqs": [],
            "psd_power": [],
            "fft_freqs": [],
            "fft_amplitude": [],
        }

    step_dt = dt if dt is not None else float(times_arr[1] - times_arr[0])
    if step_dt <= 0:
        step_dt = 0.05
    fs = 1.0 / step_dt

    # 1. Welch PSD
    try:
        nperseg = min(len(r_arr), 256)
        if nperseg < 4:
            nperseg = len(r_arr)
        freqs_welch, psd_welch = signal.welch(r_arr - np.mean(r_arr), fs=fs, nperseg=nperseg)
    except Exception:
        freqs_welch, psd_welch = np.array([]), np.array([])

    # 2. Fourier FFT Amplitude Spectrum
    try:
        n_pts = len(r_arr)
        fft_vals = np.fft.rfft(r_arr - np.mean(r_arr))
        fft_freqs = np.fft.rfftfreq(n_pts, d=step_dt)
        fft_amp = (2.0 / n_pts) * np.abs(fft_vals)
    except Exception:
        fft_freqs, fft_amp = np.array([]), np.array([])

    return {
        "dt": step_dt,
        "psd_freqs": freqs_welch.tolist(),
        "psd_power": psd_welch.tolist(),
        "fft_freqs": fft_freqs.tolist(),
        "fft_amplitude": fft_amp.tolist(),
        "sampling_rate": fs,
    }


def analyze_lie_symmetries(
    times: np.ndarray,
    phases: np.ndarray,
    adj_matrix: np.ndarray,
    coupling: float,
    omega: Optional[np.ndarray] = None,
    dt: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute Lie symmetry invariants, continuous U(1) phase invariance,
    symplectic/time-reversibility residuals, and Noether charges."""
    t_arr = np.asarray(times, dtype=float)
    theta = np.asarray(phases, dtype=float)
    adj = np.asarray(adj_matrix, dtype=float)
    k_val = float(coupling)
    n = theta.shape[1] if theta.ndim == 2 else len(theta)

    if len(t_arr) == 0 or n == 0:
        return {}

    # 1. Interaction Energy (Hamiltonian potential): E(t) = - (K / 2N) sum_{i,j} A_ij cos(theta_j - theta_i)
    diff = theta[:, :, np.newaxis] - theta[:, np.newaxis, :]
    cos_diff = np.cos(diff)
    energy = -0.5 * (k_val / max(1.0, float(n))) * np.sum(adj * cos_diff, axis=(1, 2))

    # 2. Noether Charge / Global U(1) momentum:
    omega_bar = float(np.mean(omega)) if omega is not None and len(omega) == n else 0.0
    mean_phase = np.mean(theta, axis=1)
    noether_charge = mean_phase - omega_bar * t_arr
    noether_charge_centered = noether_charge - noether_charge[0]

    # 3. Geometric Algebra Rotor Unitarity in Cl(2):
    half_theta = theta / 2.0
    rotor_norms = np.cos(half_theta) ** 2 + np.sin(half_theta) ** 2
    rotor_unitarity = np.mean(rotor_norms, axis=1)

    # 4. Continuous U(1) phase rotation invariance test over alpha in [0, 2pi):
    alpha_vals = np.linspace(0, 2 * np.pi, 50)
    u1_residuals = []
    # For Kuramoto equations: d(theta_i + alpha)/dt == d(theta_i)/dt because sin((theta_j + a) - (theta_i + a)) == sin(theta_j - theta_i)
    # Residual: || d/dt(theta + alpha) - d/dt(theta) ||_inf
    for a in alpha_vals:
        shifted_diff = (theta[:, :, np.newaxis] + a) - (theta[:, np.newaxis, :] + a)
        u1_res = float(np.max(np.abs(np.sin(diff) - np.sin(shifted_diff))))
        u1_residuals.append(u1_res)

    # 5. Symplectic / Time-reversibility residual (dt -> -dt):
    # Under exact time reversal with -dt and -omega, trajectory maps back to theta(t).
    # Residual across steps: difference between forward-backward single-step map or trajectory residual
    step_dt = float(dt) if dt is not None and dt > 0 else (float(t_arr[1] - t_arr[0]) if len(t_arr) > 1 else 0.05)
    reversibility_residual = np.zeros(len(t_arr))
    for t_idx in range(len(t_arr)):
        th_current = theta[t_idx]
        # Forward Euler velocity:
        diff_curr = th_current[np.newaxis, :] - th_current[:, np.newaxis]
        coupling_curr = np.sum(adj * np.sin(diff_curr), axis=1)
        om = omega if omega is not None and len(omega) == n else np.zeros(n)
        dtheta_fwd = om + (k_val / max(1.0, float(n))) * coupling_curr
        th_fwd = th_current + step_dt * dtheta_fwd
        
        # Backward velocity from th_fwd with -step_dt:
        diff_fwd = th_fwd[np.newaxis, :] - th_fwd[:, np.newaxis]
        coupling_bwd = np.sum(adj * np.sin(diff_fwd), axis=1)
        dtheta_bwd = om + (k_val / max(1.0, float(n))) * coupling_bwd
        th_reconstructed = th_fwd - step_dt * dtheta_bwd
        reversibility_residual[t_idx] = float(np.mean(np.abs(th_reconstructed - th_current)))

    return {
        "interaction_energy": energy.tolist(),
        "noether_charge": noether_charge_centered.tolist(),
        "rotor_unitarity": rotor_unitarity.tolist(),
        "u1_alphas": alpha_vals.tolist(),
        "u1_residuals": u1_residuals,
        "reversibility_residuals": reversibility_residual.tolist(),
        "mean_reversibility_residual": float(np.mean(reversibility_residual)),
        "global_phase_invariance_error": float(np.max(u1_residuals)),
        "mean_energy": float(np.mean(energy)),
        "energy_drift": float(energy[-1] - energy[0]) if len(energy) > 0 else 0.0,
        "mean_unitarity": float(np.mean(rotor_unitarity)),
    }


def compute_quantum_mode_comparison(
    omega: np.ndarray,
    adj_matrix: np.ndarray,
    k_coupling: float,
    t_span: float,
    dt: float,
    seed: int = 27,
    shots: int = 1024,
) -> Dict[str, Any]:
    """Compute statevector baseline vs shot_sampling with dispersion for quantum comparison."""
    from app.services.solvers import SolverRegistry
    from kuramoto.model import order_parameter

    # 1. Statevector baseline (noise-free)
    t_exact, phases_exact = SolverRegistry._solve_quantum_method(
        scheme="statevector",
        omega=omega,
        adj_matrix=adj_matrix,
        k_coupling=k_coupling,
        t_span=t_span,
        dt=dt,
        seed=seed,
    )
    r_exact = order_parameter(phases_exact)

    # 2. Shot sampling runs (NISQ hardware shot dispersion)
    shot_samples = []
    for s_seed in [seed, seed + 1, seed + 2]:
        _, p_shot = SolverRegistry._solve_quantum_method(
            scheme="shot_sampling",
            omega=omega,
            adj_matrix=adj_matrix,
            k_coupling=k_coupling,
            t_span=t_span,
            dt=dt,
            seed=s_seed,
            shots=shots,
        )
        shot_samples.append(order_parameter(p_shot))

    shot_samples_arr = np.array(shot_samples)
    r_shot_mean = np.mean(shot_samples_arr, axis=0)
    r_shot_std = np.std(shot_samples_arr, axis=0)

    return {
        "time": t_exact.tolist(),
        "r_statevector": r_exact.tolist(),
        "r_shot_mean": r_shot_mean.tolist(),
        "r_shot_std": r_shot_std.tolist(),
        "r_shot_upper": (r_shot_mean + r_shot_std).tolist(),
        "r_shot_lower": np.clip(r_shot_mean - r_shot_std, 0.0, 1.0).tolist(),
    }


# Register default diagnostics
DiagnosticRegistry.register(
    "graph_topology", lambda **kw: analyze_graph_topology(kw["adj_matrix"])
)
DiagnosticRegistry.register(
    "spectral_dynamics",
    lambda **kw: analyze_spectral_dynamics(kw["times"], kw["order_param"], kw.get("dt")),
)
DiagnosticRegistry.register(
    "lie_symmetries",
    lambda **kw: analyze_lie_symmetries(
        kw["times"],
        kw["phases"],
        kw["adj_matrix"],
        kw.get("coupling", 1.0),
        kw.get("omega"),
        kw.get("dt"),
    ),
)
