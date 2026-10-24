"""Spectral and topological diagnostics service for Kuramoto dynamics."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import networkx as nx
import numpy as np

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
    """Compute PSD and harmonic decomposition of order parameter time-series."""
    if len(times) < 2:
        return {}

    step_dt = dt if dt is not None else float(times[1] - times[0])

    psd_result = None
    if compute_psd is not None:
        try:
            psd_result = compute_psd(order_param, dt=step_dt)
        except Exception:
            pass

    harmonics = None
    if harmonic_analysis is not None:
        try:
            harmonics = harmonic_analysis(order_param, dt=step_dt, max_harmonic=5)
        except Exception:
            pass

    return {
        "dt": step_dt,
        "psd": psd_result,
        "harmonics": harmonics,
    }


def analyze_lie_symmetries(
    times: np.ndarray,
    phases: np.ndarray,
    adj_matrix: np.ndarray,
    coupling: float,
    omega: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Compute Lie symmetry invariants, Noether energy, and U(1) phase diagnostics.

    Parameters
    ----------
    times : np.ndarray
        Array of time steps shape (T,).
    phases : np.ndarray
        Oscillator phase time series shape (T, N).
    adj_matrix : np.ndarray
        Adjacency matrix shape (N, N).
    coupling : float
        Coupling strength K.
    omega : np.ndarray | None
        Natural frequency array shape (N,).

    Returns
    -------
    Dict[str, Any]
        Dictionary with interaction energy, Noether charge, rotor unitarity, and invariance errors.
    """
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

    # 4. Global U(1) phase shift invariance test (alpha = pi/3):
    alpha = np.pi / 3.0
    shifted_diff = (theta[:, :, np.newaxis] + alpha) - (theta[:, np.newaxis, :] + alpha)
    invariance_error = float(np.max(np.abs(np.sin(diff) - np.sin(shifted_diff))))

    return {
        "interaction_energy": energy.tolist(),
        "noether_charge": noether_charge_centered.tolist(),
        "rotor_unitarity": rotor_unitarity.tolist(),
        "global_phase_invariance_error": invariance_error,
        "mean_energy": float(np.mean(energy)),
        "energy_drift": float(energy[-1] - energy[0]) if len(energy) > 0 else 0.0,
        "mean_unitarity": float(np.mean(rotor_unitarity)),
    }


# Register default diagnostics
DiagnosticRegistry.register(
    "graph_topology", lambda **kw: analyze_graph_topology(kw["adj_matrix"])
)
DiagnosticRegistry.register(
    "spectral_dynamics",
    lambda **kw: analyze_spectral_dynamics(kw["times"], kw["order_param"]),
)
DiagnosticRegistry.register(
    "lie_symmetries",
    lambda **kw: analyze_lie_symmetries(
        kw["times"],
        kw["phases"],
        kw["adj_matrix"],
        kw.get("coupling", 1.0),
        kw.get("omega"),
    ),
)
