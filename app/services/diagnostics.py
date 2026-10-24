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


# Register default diagnostics
DiagnosticRegistry.register(
    "graph_topology", lambda **kw: analyze_graph_topology(kw["adj_matrix"])
)
DiagnosticRegistry.register(
    "spectral_dynamics",
    lambda **kw: analyze_spectral_dynamics(kw["times"], kw["order_param"]),
)
