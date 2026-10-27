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
    from kuramoto.solvers.quantum_rotor import QuantumRotorSolver
except ImportError:
    QuantumRotorSolver = None

try:
    from kuramoto.solvers.rk45 import solve_kuramoto as solve_kuramoto_rk45
except ImportError:
    solve_kuramoto_rk45 = None

try:
    from kuramoto.model import KuramotoModel
except ImportError:
    KuramotoModel = None


SOLVER_CATEGORIES = {
    "Classical ODE": [
        ("rk45", "RK45 (Standard SciPy Dormand-Prince 5(4))"),
    ],
    "First-Order & Mean-Field Geometric Algebra (GA)": [
        ("vectorized_geometric", "Vectorized Geometric (Spin(n) Bivector Torque)"),
        ("euler_fast", "Fast Mean-Field Euler (O(N) Dense Network Acceleration)"),
        ("euler_geometric", "Clifford Multivector Euler"),
        ("euler_standard", "Standard Pairwise Euler"),
    ],
    "Higher-Order & Adaptive Lie-Group Solvers": [
        ("rkmk4", "RKMK4 (4th-Order Runge-Kutta-Munthe-Kaas Lie Group)"),
        ("dopri54", "Lie-DOPRI54 (7-Stage Embedded with FSAL & PI Control)"),
        ("midpoint_geometric", "Geometric Midpoint (2nd-Order Symplectic)"),
        ("predictor_corrector", "Predictor-Corrector (Embedded LTE Estimation)"),
        ("adaptive_embedded", "Adaptive Embedded (Step-Size Control)"),
    ],
    "Quantum Self-Consistent Field (SCF)": [
        ("quantum_statevector", "Quantum Statevector (Exact Unitary N-Qubit Evolution)"),
        ("quantum_expectation", "Quantum Expectation (Analytical Pauli Observable Extraction)"),
        ("shot_sampling", "NISQ Shot Sampling (Projective Measurement Simulation)"),
    ],
}


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
        cls._solvers[name.lower()] = solver_fn
        cls._descriptions[name.lower()] = description

    @classmethod
    def get_available(cls) -> List[Dict[str, str]]:
        """Return list of available solvers for UI dropdowns."""
        return [
            {"label": desc or key.upper(), "value": key}
            for key, desc in cls._descriptions.items()
        ]

    @classmethod
    def get_grouped_options(cls) -> List[Dict[str, Any]]:
        """Return grouped options formatted for Dash dcc.Dropdown."""
        options = []
        for group_label, solver_list in SOLVER_CATEGORIES.items():
            for val, label in solver_list:
                options.append({"label": f"[{group_label.split()[0]}] {label}", "value": val, "group": group_label})
        return options

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
        name = (solver_name or "rk45").strip().lower()

        # Handle aliases
        alias_map = {
            "rk45": "rk45",
            "euler": "euler_standard",
            "standard": "euler_standard",
            "euler_standard": "euler_standard",
            "fast": "euler_fast",
            "euler_fast": "euler_fast",
            "fast_euler": "euler_fast",
            "geometric": "euler_geometric",
            "euler_geometric": "euler_geometric",
            "rotor": "vectorized_geometric",
            "vectorized_geometric": "vectorized_geometric",
            "rotor_geometric": "vectorized_geometric",
            "rkmk": "rkmk4",
            "rkmk4": "rkmk4",
            "rk4": "rkmk4",
            "geometric_rk4": "rkmk4",
            "dopri": "dopri54",
            "dopri54": "dopri54",
            "adaptive_dopri54": "dopri54",
            "midpoint": "midpoint_geometric",
            "midpoint_geometric": "midpoint_geometric",
            "euler_midpoint": "midpoint_geometric",
            "pc": "predictor_corrector",
            "predictor_corrector": "predictor_corrector",
            "adaptive": "adaptive_embedded",
            "adaptive_embedded": "adaptive_embedded",
            "embedded": "adaptive_embedded",
            "quantum": "quantum_statevector",
            "quantum_rotor": "quantum_statevector",
            "quantum_scf": "quantum_statevector",
            "quantum_statevector": "quantum_statevector",
            "statevector": "quantum_statevector",
            "quantum_expectation": "quantum_expectation",
            "expectation": "quantum_expectation",
            "quantum_shot_sampling": "shot_sampling",
            "shot_sampling": "shot_sampling",
        }

        canonical_name = alias_map.get(name, name)
        clean_kwargs = {k: v for k, v in kwargs.items() if k != "solver_name"}

        if canonical_name in cls._solvers:
            solver_fn = cls._solvers[canonical_name]
            return solver_fn(
                omega=omega,
                adj_matrix=adj_matrix,
                k_coupling=k_coupling,
                t_span=t_span,
                dt=dt,
                initial_phases=initial_phases,
                seed=seed,
                **clean_kwargs,
            )

        return cls._solve_via_kuramoto_model(
            omega=omega,
            adj_matrix=adj_matrix,
            k_coupling=k_coupling,
            t_span=t_span,
            dt=dt,
            initial_phases=initial_phases,
            seed=seed,
            solver_name=canonical_name,
            **clean_kwargs,
        )

    # Built-in solver implementations
    @staticmethod
    def _solve_via_kuramoto_model(
        omega: np.ndarray,
        adj_matrix: np.ndarray,
        k_coupling: float,
        t_span: float,
        dt: float,
        initial_phases: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
        solver_name: str = "rk45",
        **kwargs: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Dispatch solve via KuramotoModel or RotorSolver."""
        n = len(omega)
        t_eval = np.arange(0.0, t_span + dt / 2.0, dt)

        if KuramotoModel is not None:
            try:
                # Filter kwargs for KuramotoModel and simulate
                sim_kwargs: Dict[str, Any] = {}
                if "adaptive_rtol" in kwargs:
                    sim_kwargs["adaptive_rtol"] = kwargs["adaptive_rtol"]
                    sim_kwargs["rtol"] = kwargs["adaptive_rtol"]
                if "adaptive_atol" in kwargs:
                    sim_kwargs["adaptive_atol"] = kwargs["adaptive_atol"]
                    sim_kwargs["atol"] = kwargs["adaptive_atol"]
                if "dt_min" in kwargs:
                    sim_kwargs["dt_min"] = kwargs["dt_min"]
                if "dt_max" in kwargs:
                    sim_kwargs["dt_max"] = kwargs["dt_max"]
                if "shots" in kwargs:
                    sim_kwargs["shots"] = kwargs["shots"]

                model = KuramotoModel(
                    n_oscillators=n,
                    natural_frequencies=omega,
                    adjacency_matrix=adj_matrix,
                    coupling_strength=k_coupling,
                    random_seed=seed,
                    solver_type=solver_name,
                )
                if initial_phases is not None:
                    model.phases = np.asarray(initial_phases, dtype=float).copy()

                # KuramotoModel.simulate() expects n_points, not dt.
                # Compute n_points from t_span and dt to match the requested resolution.
                n_points = max(2, int(np.round(t_span / dt)))
                # Pass dt_internal so the rotor solver uses the output dt directly
                # instead of defaulting to min(diff(t_eval)) * 0.1 which causes
                # excessive sub-stepping and very slow simulations.
                if "dt_internal" not in sim_kwargs:
                    sim_kwargs["dt_internal"] = dt
                dataset = model.simulate(t_span=t_span, n_points=n_points, **sim_kwargs)
                return dataset.time, dataset.phases
            except Exception:
                pass

        # Fallback to RotorSolver or standard RK45
        return SolverRegistry._solve_rk45(
            omega=omega,
            adj_matrix=adj_matrix,
            k_coupling=k_coupling,
            t_span=t_span,
            dt=dt,
            initial_phases=initial_phases,
            seed=seed,
            **kwargs,
        )

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
            rtol=kwargs.get("adaptive_rtol", 1e-6),
            atol=kwargs.get("adaptive_atol", 1e-8),
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
    def _solve_rotor_method(
        method_name: str,
        omega: np.ndarray,
        adj_matrix: np.ndarray,
        k_coupling: float,
        t_span: float,
        dt: float,
        initial_phases: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Dispatch rotor-based methods using the real clifford-based RotorSolver."""
        n = len(omega)
        t_eval = np.arange(0.0, t_span + dt / 2.0, dt)

        if RotorSolver is not None:
            try:
                if initial_phases is None:
                    rng = np.random.default_rng(seed)
                    init_phases = rng.uniform(0, 2 * np.pi, n)
                else:
                    init_phases = np.asarray(initial_phases, dtype=float)

                solver = RotorSolver(
                    n_oscillators=n,
                    dim=2,
                    seed=seed,
                    natural_frequencies=omega,
                    adjacency_matrix=adj_matrix,
                    initial_phases=init_phases,
                )
                sim_kwargs: Dict[str, Any] = {}
                if "adaptive_rtol" in kwargs:
                    sim_kwargs["adaptive_rtol"] = kwargs["adaptive_rtol"]
                if "adaptive_atol" in kwargs:
                    sim_kwargs["adaptive_atol"] = kwargs["adaptive_atol"]
                if "dt_min" in kwargs:
                    sim_kwargs["dt_min"] = kwargs["dt_min"]
                if "dt_max" in kwargs:
                    sim_kwargs["dt_max"] = kwargs["dt_max"]
                sim_kwargs["dt_internal"] = dt

                times, phases = solver.simulate(
                    K=k_coupling,
                    t_eval=t_eval,
                    method=method_name,
                    **sim_kwargs,
                )
                return times, phases
            except Exception:
                pass

        return SolverRegistry._solve_via_kuramoto_model(
            omega=omega,
            adj_matrix=adj_matrix,
            k_coupling=k_coupling,
            t_span=t_span,
            dt=dt,
            initial_phases=initial_phases,
            seed=seed,
            solver_name=method_name,
            **kwargs,
        )

    @staticmethod
    def _solve_quantum_method(
        scheme: str,
        omega: np.ndarray,
        adj_matrix: np.ndarray,
        k_coupling: float,
        t_span: float,
        dt: float,
        initial_phases: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, np.ndarray]:
        n = len(omega)
        t_eval = np.arange(0.0, t_span + dt / 2.0, dt)

        if QuantumRotorSolver is not None:
            try:
                q_solver = QuantumRotorSolver(
                    n_oscillators=n,
                    seed=seed,
                    adjacency_matrix=adj_matrix,
                    natural_frequencies=omega,
                    initial_phases=initial_phases,
                )
                shots_val = int(kwargs.get("shots", shots))
                times, phases = q_solver.simulate(
                    K=k_coupling,
                    t_eval=t_eval,
                    scheme=scheme,  # type: ignore[arg-type]
                    shots=shots_val,
                )
                return times, phases
            except Exception:
                pass

        return SolverRegistry._solve_via_kuramoto_model(
            omega=omega,
            adj_matrix=adj_matrix,
            k_coupling=k_coupling,
            t_span=t_span,
            dt=dt,
            initial_phases=initial_phases,
            seed=seed,
            solver_name=f"quantum_{scheme}" if scheme != "shot_sampling" else "shot_sampling",
            shots=shots,
            **kwargs,
        )


# Register all solvers
SolverRegistry.register("rk45", SolverRegistry._solve_rk45, "RK45 (Adaptive Runge-Kutta)")
SolverRegistry.register("euler", SolverRegistry._solve_euler, "Euler (Fixed-Step Explicit)")
SolverRegistry.register("euler_standard", SolverRegistry._solve_euler, "Standard Pairwise Euler")
SolverRegistry.register(
    "vectorized_geometric",
    lambda **kw: SolverRegistry._solve_rotor_method("vectorized_geometric", **kw),
    "Vectorized Geometric (Spin(n) Bivector Torque)",
)
SolverRegistry.register(
    "rotor",
    lambda **kw: SolverRegistry._solve_rotor_method("vectorized_geometric", **kw),
    "Rotor (Clifford Geometric Algebra Cl(2))",
)
SolverRegistry.register(
    "euler_fast",
    lambda **kw: SolverRegistry._solve_rotor_method("euler_fast", **kw),
    "Fast Mean-Field Euler (O(N) Acceleration)",
)
SolverRegistry.register(
    "euler_geometric",
    lambda **kw: SolverRegistry._solve_rotor_method("euler_geometric", **kw),
    "Clifford Multivector Euler",
)
SolverRegistry.register(
    "rkmk4",
    lambda **kw: SolverRegistry._solve_rotor_method("rkmk4", **kw),
    "RKMK4 (4th-Order Lie Group Integrator)",
)
SolverRegistry.register(
    "dopri54",
    lambda **kw: SolverRegistry._solve_rotor_method("dopri54", **kw),
    "Lie-DOPRI54 (7-Stage Embedded FSAL)",
)
SolverRegistry.register(
    "midpoint_geometric",
    lambda **kw: SolverRegistry._solve_rotor_method("midpoint_geometric", **kw),
    "Geometric Midpoint (2nd-Order Symplectic)",
)
SolverRegistry.register(
    "predictor_corrector",
    lambda **kw: SolverRegistry._solve_rotor_method("predictor_corrector", **kw),
    "Predictor-Corrector (Embedded LTE)",
)
SolverRegistry.register(
    "adaptive_embedded",
    lambda **kw: SolverRegistry._solve_rotor_method("adaptive_embedded", **kw),
    "Adaptive Embedded (Step-Size Control)",
)
SolverRegistry.register(
    "quantum_statevector",
    lambda **kw: SolverRegistry._solve_quantum_method("statevector", **kw),
    "Quantum Statevector (Exact Unitary Evolution)",
)
SolverRegistry.register(
    "quantum_expectation",
    lambda **kw: SolverRegistry._solve_quantum_method("expectation", **kw),
    "Quantum Expectation (Analytical Pauli Observables)",
)
SolverRegistry.register(
    "shot_sampling",
    lambda **kw: SolverRegistry._solve_quantum_method("shot_sampling", **kw),
    "NISQ Shot Sampling (Projective Measurement)",
)
