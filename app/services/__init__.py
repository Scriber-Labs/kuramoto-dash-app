"""Services package initialization."""

from app.services.benchmark import export_dataset_npz, package_simulation_payload
from app.services.cli_bridge import build_cli_config, run_cli_command
from app.services.diagnostics import (
    DiagnosticRegistry,
    analyze_graph_topology,
    analyze_spectral_dynamics,
)
from app.services.distributions import DistributionRegistry
from app.services.simulation import (
    build_adjacency,
    build_cli_simulation_json,
    collect_config,
    generate_dataset,
    generate_frequencies,
)
from app.services.solvers import SolverRegistry
from app.services.topology import TopologyRegistry, parse_custom_adjacency
from app.services.validation import (
    check_nyquist_sampling,
    validate_simulation_inputs,
)

__all__ = [
    "TopologyRegistry",
    "SolverRegistry",
    "DistributionRegistry",
    "DiagnosticRegistry",
    "parse_custom_adjacency",
    "analyze_graph_topology",
    "analyze_spectral_dynamics",
    "check_nyquist_sampling",
    "build_cli_config",
    "run_cli_command",
    "export_dataset_npz",
    "package_simulation_payload",
    "build_adjacency",
    "build_cli_simulation_json",
    "collect_config",
    "generate_dataset",
    "generate_frequencies",
    "validate_simulation_inputs",
]
