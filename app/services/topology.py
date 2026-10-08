"""Topology registry and graph utilities for Kuramoto network configurations."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
import networkx as nx
import numpy as np

try:
    from kuramoto.topologies.loader import load_topology
    from kuramoto.topologies.tree_of_life import (
        SEFIROT_NAMES,
        SEFIROT_POSITIONS,
        TreeOfLifeTopology,
    )
    from kuramoto.topologies.analysis import (
        compute_chromatic_polynomial,
        get_graph_metadata,
    )
except ImportError:
    load_topology = None
    SEFIROT_NAMES = None
    SEFIROT_POSITIONS = None
    TreeOfLifeTopology = None
    compute_chromatic_polynomial = None
    get_graph_metadata = None


class TopologyRegistry:
    """Extensible registry for network topologies and adjacency matrix generation."""

    _generators: Dict[str, Callable[..., np.ndarray]] = {}
    _layouts: Dict[str, Callable[[int, Optional[np.ndarray]], Dict[int, tuple[float, float]]]] = {}
    _labels: Dict[str, Callable[[int], Dict[int, str]]] = {}
    _descriptions: Dict[str, str] = {}

    @classmethod
    def register(
        cls,
        name: str,
        generator: Callable[..., np.ndarray],
        description: str = "",
        layout_fn: Optional[Callable[[int, Optional[np.ndarray]], Dict[int, tuple[float, float]]]] = None,
        label_fn: Optional[Callable[[int], Dict[int, str]]] = None,
    ) -> None:
        """Register a new topology generator."""
        cls._generators[name] = generator
        cls._descriptions[name] = description
        if layout_fn is not None:
            cls._layouts[name] = layout_fn
        if label_fn is not None:
            cls._labels[name] = label_fn

    @classmethod
    def get_available(cls) -> List[Dict[str, str]]:
        """Return list of available topologies with labels and values for UI."""
        options = []
        for key, desc in cls._descriptions.items():
            options.append({"label": desc or key.replace("_", " ").title(), "value": key})
        return options

    @classmethod
    def generate(cls, name: str, n: int, **kwargs: Any) -> np.ndarray:
        """Generate an adjacency matrix for the requested topology."""
        if name not in cls._generators:
            # Fallback to load_topology or all-to-all
            if load_topology is not None:
                try:
                    return load_topology(name, n=n, **kwargs)
                except Exception:
                    pass
            # Default fallback
            return cls._generators.get("all_to_all", cls._generate_all_to_all)(n)

        return cls._generators[name](n, **kwargs)

    @classmethod
    def get_layout(cls, name: str, n: int, adjacency: Optional[np.ndarray] = None) -> Dict[int, tuple[float, float]]:
        """Get 2D node coordinates for plotting."""
        if name in cls._layouts:
            return cls._layouts[name](n, adjacency)
        # Default circular layout
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        return {i: (float(np.cos(a)), float(np.sin(a))) for i, a in enumerate(angles)}

    @classmethod
    def get_labels(cls, name: str, n: int) -> Dict[int, str]:
        """Get custom node labels if available."""
        if name in cls._labels:
            return cls._labels[name](n)
        return {i: f"Osc {i + 1}" for i in range(n)}

    # Built-in generator implementations
    @staticmethod
    def _generate_all_to_all(n: int, **kwargs: Any) -> np.ndarray:
        adj = np.ones((n, n), dtype=float)
        np.fill_diagonal(adj, 0.0)
        return adj

    @staticmethod
    def _generate_ring(n: int, k_nearest: int = 1, **kwargs: Any) -> np.ndarray:
        adj = np.zeros((n, n), dtype=float)
        for i in range(n):
            for step in range(1, k_nearest + 1):
                adj[i, (i + step) % n] = 1.0
                adj[i, (i - step) % n] = 1.0
        return adj

    @staticmethod
    def _generate_random(n: int, p: float = 0.2, seed: Optional[int] = None, **kwargs: Any) -> np.ndarray:
        rng = np.random.default_rng(seed)
        rand_mat = rng.random((n, n))
        adj = (rand_mat < p).astype(float)
        adj = np.triu(adj, 1)
        adj = adj + adj.T
        np.fill_diagonal(adj, 0.0)
        return adj

    @staticmethod
    def _generate_small_world(n: int, k: int = 4, p: float = 0.1, seed: Optional[int] = None, **kwargs: Any) -> np.ndarray:
        if load_topology is not None:
            try:
                return load_topology("small_world", n=n, k=k, p=p, seed=seed)
            except Exception:
                pass
        g = nx.watts_strogatz_graph(n=n, k=k if k < n else max(2, n - 1), p=p, seed=seed)
        return nx.to_numpy_array(g, dtype=float)

    @staticmethod
    def _generate_tree_of_life(n: int = 10, **kwargs: Any) -> np.ndarray:
        if load_topology is not None:
            try:
                return load_topology("tree_of_life")
            except Exception:
                pass
        if TreeOfLifeTopology is not None:
            tol = TreeOfLifeTopology()
            return tol.adjacency_matrix
        # Fallback 10-node Tree of Life adjacency
        edges = [
            (0, 1), (0, 2), (0, 5), (1, 2), (1, 3), (1, 5), (2, 4), (2, 5),
            (3, 4), (3, 5), (3, 6), (4, 5), (4, 7), (5, 6), (5, 7), (5, 8),
            (6, 7), (6, 8), (7, 8), (6, 9), (7, 9), (8, 9)
        ]
        adj = np.zeros((10, 10), dtype=float)
        for u, v in edges:
            adj[u, v] = 1.0
            adj[v, u] = 1.0
        return adj

    @staticmethod
    def _generate_custom(n: int, adjacency_matrix: Optional[np.ndarray] = None, **kwargs: Any) -> np.ndarray:
        if adjacency_matrix is not None:
            adj = np.asarray(adjacency_matrix, dtype=float)
            if adj.shape == (n, n):
                return adj
            if adj.ndim == 2 and adj.shape[0] == adj.shape[1]:
                return adj
        return TopologyRegistry._generate_all_to_all(n)


# Register default topologies
TopologyRegistry.register(
    "all_to_all",
    TopologyRegistry._generate_all_to_all,
    description="All-to-All (Complete)",
)
TopologyRegistry.register(
    "ring",
    TopologyRegistry._generate_ring,
    description="Ring (1D Lattice)",
)
TopologyRegistry.register(
    "random",
    TopologyRegistry._generate_random,
    description="Random (Erdős-Rényi)",
)
TopologyRegistry.register(
    "small_world",
    TopologyRegistry._generate_small_world,
    description="Small-World (Watts-Strogatz)",
)


def _tree_of_life_layout(n: int, adjacency: Optional[np.ndarray] = None) -> Dict[int, tuple[float, float]]:
    if SEFIROT_POSITIONS is not None:
        return {i: SEFIROT_POSITIONS.get(i, (0.0, 0.0)) for i in range(10)}
    # Default 10-node layout
    return {
        0: (0.0, 1.0),
        1: (0.8, 0.75),
        2: (-0.8, 0.75),
        3: (0.8, 0.25),
        4: (-0.8, 0.25),
        5: (0.0, 0.0),
        6: (0.8, -0.5),
        7: (-0.8, -0.5),
        8: (0.0, -0.75),
        9: (0.0, -1.0),
    }


def _tree_of_life_labels(n: int) -> Dict[int, str]:
    if SEFIROT_NAMES is not None:
        return {i: SEFIROT_NAMES[i] for i in range(min(n, len(SEFIROT_NAMES)))}
    default_names = [
        "Keter", "Chokhmah", "Binah", "Chesed", "Gevurah",
        "Tiferet", "Netzach", "Hod", "Yesod", "Malkhut"
    ]
    return {i: default_names[i] for i in range(min(n, len(default_names)))}


TopologyRegistry.register(
    "tree_of_life",
    TopologyRegistry._generate_tree_of_life,
    description="Tree of Life (Etz Hayim)",
    layout_fn=_tree_of_life_layout,
    label_fn=_tree_of_life_labels,
)
TopologyRegistry.register(
    "custom",
    TopologyRegistry._generate_custom,
    description="Custom Adjacency Matrix",
)


def parse_custom_adjacency(text: str, n_expected: Optional[int] = None) -> np.ndarray:
    """Parse a custom adjacency matrix from string format (CSV, space, or Python list)."""
    clean = text.strip()
    if not clean:
        n = n_expected or 10
        return TopologyRegistry._generate_all_to_all(n)

    try:
        # Check if python/json list format
        if clean.startswith("[") and clean.endswith("]"):
            import ast
            parsed = ast.literal_eval(clean)
            mat = np.array(parsed, dtype=float)
            if mat.ndim == 2 and mat.shape[0] == mat.shape[1]:
                return mat
    except Exception:
        pass

    # Parse line by line
    rows = []
    for line in clean.splitlines():
        line = line.strip().replace(",", " ").replace(";", " ")
        if not line:
            continue
        row = [float(val) for val in line.split() if val]
        if row:
            rows.append(row)

    mat = np.array(rows, dtype=float)
    if mat.ndim == 2 and mat.shape[0] == mat.shape[1]:
        return mat

    n = n_expected or 10
    return TopologyRegistry._generate_all_to_all(n)
