"""CLI configuration builder and execution bridge for kuramoto CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Dict, List, Optional


def build_cli_config(
    n_oscillators: int,
    coupling_strength: float,
    topology: str,
    timesteps: int,
    dt: float,
    seed: Optional[int] = None,
    solver: str = "rk45",
    distribution_type: str = "normal",
    distribution_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a standard JSON configuration dictionary compatible with the kuramoto CLI."""
    dist_config: Dict[str, Any] = {"type": distribution_type}
    if distribution_params:
        dist_config.update(distribution_params)
    else:
        if distribution_type == "normal":
            dist_config.update({"mean": 0.0, "std": 1.0})
        elif distribution_type == "uniform":
            dist_config.update({"low": -1.0, "high": 1.0})

    return {
        "n_oscillators": int(n_oscillators),
        "coupling_strength": float(coupling_strength),
        "topology": str(topology),
        "timesteps": int(timesteps),
        "dt": float(dt),
        "seed": seed if seed is not None else 42,
        "solver": str(solver),
        "frequency_distribution": dist_config,
    }


def run_cli_command(args: List[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Execute a kuramoto CLI command using subprocess if CLI is installed."""
    exe = shutil.which("kuramoto")
    if not exe:
        # Try running via python module
        cmd = ["python", "-m", "kuramoto.cli"] + args
    else:
        cmd = [exe] + args

    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
