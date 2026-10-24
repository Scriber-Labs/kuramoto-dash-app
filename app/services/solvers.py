"""Numerical and algebraic solver registry for Kuramoto dynamics."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp

try:
    from kuramoto.solvers.rotor import RotorSolver
except ImportError:
    RotorSolver = None

try:
    from kuramoto.solvers.rk45 import solve_kuramoto as solve_kuramoto_rk45
except ImportError:
    solve_kuramoto_rk45 = None


class SolverRegistry:
    """Extensible registry for Kuramoto equation numerical and algebraic solvers."""

    _solvers: Dict[str, Callable[..., Tuple[np.ndarray, np.ndarray]]] = {}
    _descriptions: Dict[str, str] = {}

    @classmethod
    def register(
        cls,
        name: str,
        solver_fn: Callable[..., Tuple[np.ndarray, np.ndarray]],
        description: str = "",
    ) -> None:
        """Register a new solver function."""
        cls._solvers[name] = solver_fn
        cls._descriptions[name] = description

    @classmethod
    def get_available(cls) -> List[Dict[str, str]]:
        """Return list of available solvers for UI dropdowns."""
        return [
            {"label": desc or key.upper(), "value": key}
            for key, desc in cls._descriptions.items()
        ]

    @classmethod
    def solve(
        cls,
        solver_name: str,
        omega: np.ndarray,
        adj_matrix: np.ndarray,
        k_coupling: float,
        t_span: float,
        dt: float,
        initial_phases: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Execute simulation using specified solver."""
        name = solver_name.lower()
        if name not in cls._solvers:
            name = "rk45"

        solver_fn = cls._solvers.get(name, cls._solve_rk45)
        return solver_fn(
            omega=omega,
            adj_matrix=adj_matrix,
            k_coupling=k_coupling,
            t_span=t_span,
            dt=dt,
            initial_phases=initial_phases,
            seed=seed,
            **kwargs,
        )

    # Built-in solver implementations
    @staticmethod
    def _solve_rk45(
        omega: np.ndarray,
        adj_matrix: np.ndarray,
        k_coupling: float,
        t_span: float,
        dt: float,
        initial_phases: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        n = len(omega)
        if initial_phases is None:
            rng = np.random.default_rng(seed)
            theta0 = rng.uniform(0, 2 * np.pi, n)
        else:
            theta0 = np.asarray(initial_phases, dtype=float)

        t_eval = np.arange(0.0, t_span + dt / 2.0, dt)

        if solve_kuramoto_rk45 is not None:
            try:
                res = solve_kuramoto_rk45(
                    omega=omega,
                    adj_matrix=adj_matrix,
                    k_coupling=k_coupling,
                    initial_phases=theta0,
                    t_eval=t_eval,
                )
                if isinstance(res, tuple) and len(res) == 2:
                    return res
            except Exception:
                pass

        def kuramoto_deriv(t: float, theta: np.ndarray) -> np.ndarray:
            phase_diff = theta[np.newaxis, :] - theta[:, np.newaxis]
            coupling_term = np.sum(adj_matrix * np.sin(phase_diff), axis=1)
            norm = n if n > 0 else 1.0
            return omega + (k_coupling / norm) * coupling_term

        sol = solve_ivp(
            kuramoto_deriv,
            (0.0, t_span),
            theta0,
            t_eval=t_eval,
            method="RK45",
            rtol=1e-6,
            atol=1e-8,
        )
        return sol.t, sol.y.T

    @staticmethod
    def _solve_euler(
        omega: np.ndarray,
        adj_matrix: np.ndarray,
        k_coupling: float,
        t_span: float,
        dt: float,
        initial_phases: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        n = len(omega)
        if initial_phases is None:
            rng = np.random.default_rng(seed)
            theta = rng.uniform(0, 2 * np.pi, n)
        else:
            theta = np.asarray(initial_phases, dtype=float).copy()

        t_steps = int(np.round(t_span / dt)) + 1
        times = np.linspace(0, t_span, t_steps)
        phases = np.zeros((t_steps, n), dtype=float)
        phases[0] = theta

        norm = float(n) if n > 0 else 1.0
        for step in range(1, t_steps):
            phase_diff = theta[np.newaxis, :] - theta[:, np.newaxis]
            coupling_term = np.sum(adj_matrix * np.sin(phase_diff), axis=1)
            dtheta = omega + (k_coupling / norm) * coupling_term
            theta = theta + dt * dtheta
            phases[step] = theta

        return times, phases

    @staticmethod
    def _solve_rotor(
        omega: np.ndarray,
        adj_matrix: np.ndarray,
        k_coupling: float,
        t_span: float,
        dt: float,
        initial_phases: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        n = len(omega)
        t_eval = np.arange(0.0, t_span + dt / 2.0, dt)

        if RotorSolver is not None:
            try:
                solver = RotorSolver(
                    n_oscillators=n,
                    dim=2,
                    seed=seed,
                    natural_frequencies=omega,
                    adjacency_matrix=adj_matrix,
                    initial_phases=initial_phases,
                )
                times, phases = solver.simulate(K=k_coupling, t_eval=t_eval)
                return times, phases
            except Exception:
                pass

        # Fallback to Euler if RotorSolver unavailable
        return SolverRegistry._solve_euler(
            omega=omega,
            adj_matrix=adj_matrix,
            k_coupling=k_coupling,
            t_span=t_span,
            dt=dt,
            initial_phases=initial_phases,
            seed=seed,
        )


# Register standard solvers
SolverRegistry.register(
    "rk45", SolverRegistry._solve_rk45, "RK45 (Adaptive Runge-Kutta)"
)
SolverRegistry.register(
    "euler", SolverRegistry._solve_euler, "Euler (Fixed-Step Explicit)"
)
SolverRegistry.register(
    "rotor", SolverRegistry._solve_rotor, "Rotor (Clifford Geometric Algebra Cl(2))"
)
