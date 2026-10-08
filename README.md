# Kuramoto Lab (`kuramoto-dash-app`)

An interactive web dashboard for simulating, analyzing, and visualizing Kuramoto oscillator synchronization dynamics on complex networks. Built with **Dash** and **Plotly**, this application seamlessly integrates with [`kuramoto-benchmark-suite`](https://github.com/Scriber-Labs/kuramoto-benchmark-suite) for benchmark-grade numerical simulations, Geometric Algebra rotor dynamics, CLI workflows, and reproducible dataset generation.

---

## Features

- **Extensible Registry Architecture**:
  - Pluggable `TopologyRegistry`, `SolverRegistry`, `DistributionRegistry`, and `DiagnosticRegistry` allowing modular extension with new graph topologies, numerical solvers, probability distributions, and spectral metrics.

- **Interactive Parameter Exploration**:
  - **Oscillator Population**: Configurable count $N \in [2, 100]$ (automatically matched for fixed-size topologies like Tree of Life).
  - **Coupling Strength**: Adjustable global coupling $K \in [0.0, 20.0]$.
  - **Temporal Controls**: Configurable simulation duration $t$, step size $dt$, and random seed for deterministic runs.
  - **Network Topologies**:
    - **All-to-All**: Complete graph coupling.
    - **Ring**: 1D lattice nearest-neighbor ring coupling.
    - **Random**: Erdős-Rényi random network.
    - **Small-World**: Watts-Strogatz network with high clustering and short path lengths.
    - **Tree of Life**: Etz Hayim 10-node, 22-path canonical graph with specialized 2D coordinates and Sefirot labels.
    - **Custom Adjacency Matrix**: User-defined adjacency matrices entered via formatted text or matrix paste.
  - **Natural Frequency Distributions**: Normal (Gaussian), Uniform, Bimodal, Golden Ratio sequence, and Custom explicit frequency lists.
  - **Numerical & Algebraic Solvers**:
    - **RK45**: Adaptive 4th/5th order Runge-Kutta integrator with error control.
    - **Euler**: Explicit fixed-step integration.
    - **Rotor**: Clifford Geometric Algebra $\text{Cl}(2)$ rotor-based phase dynamics.

- **Six Synchronized Visual Analytics Charts**:
  - **Phase Field (Unit Circle)**: Real-time oscillator positions on the complex unit circle with collective order parameter vector $r e^{i \psi}$.
  - **Coupling Network**: Interactive 2D graph layout showing node connections, topology labels, and instantaneous oscillator phases.
  - **Order Parameter $r(t)$**: Coherence evolution over time quantifying phase synchronization ($0 \le r \le 1$).
  - **Natural Frequency Distribution**: Histogram and rug plot of sampled intrinsic frequencies $\omega_i$.
  - **Oscillator Phase History**: Color-mapped spatiotemporal heatmap of phase angles $\theta_i(t) \pmod{2\pi}$.
  - **Unwrapped Phase Trajectories**: Continuous trajectory traces over time for each individual oscillator.

- **Diagnostics & Spectral Analytics**:
  - Integrated Fourier analysis, Welch Power Spectral Density (PSD), harmonic cascade tracking, and graph topological invariants (density, connectivity, diameter, and chromatic polynomials).

- **Timeline & Playback Controls**:
  - Step through simulation frames using an interactive slider.
  - Play, pause, and reset animation playback with adjustable framerate heartbeat.

- **Benchmark Dataset Export & CLI Integration**:
  - One-click export of simulation runs into compressed `.npz` archive files containing time steps, phase matrices $\theta(t)$, natural frequencies $\omega$, network adjacency matrices $A$, order parameter history $r(t)$, graph metrics, and configuration metadata.
  - Built-in bridge to `kuramoto` CLI command configurations and execution pipelines.

---

## Project Structure

```text
kuramoto-dash-app/
├── app/
│   ├── callbacks/            # Reactive Dash callbacks
│   │   ├── dataset.py        # Animation timers and .npz dataset export
│   │   ├── simulation.py     # Simulation triggers and state updates
│   │   └── visualization.py  # Graph figures and metric card updates
│   ├── components/           # Reusable UI component factories
│   │   ├── cards.py          # Header, hero, metric, and formula cards
│   │   ├── controls.py       # Sidebar parameters and timeline controls
│   │   ├── plots.py          # Plotly figure generators (6 charts)
│   │   └── tables.py         # Summary tables and data views
│   ├── services/             # Extensible service layer & benchmark bridge
│   │   ├── benchmark.py      # Benchmark suite bridge & archive export
│   │   ├── cli_bridge.py     # kuramoto CLI runner & config generator
│   │   ├── diagnostics.py    # Spectral analysis, Fourier, PSD & graph metrics
│   │   ├── distributions.py  # Extensible frequency distribution registry
│   │   ├── simulation.py     # Simulation orchestration & workflow engine
│   │   ├── solvers.py        # Extensible solver registry (RK45, Euler, Rotor)
│   │   ├── topology.py       # Extensible graph topology & adjacency registry
│   │   └── validation.py     # Parameter validation boundaries
│   ├── app.py                # Dash server entry point
│   ├── config.py             # Default parameters, ranges, and color maps
│   └── layout.py             # Top-level application layout tree
├── assets/                   # Static styling, custom scripts, and branding
│   ├── css/
│   ├── images/
│   └── js/
├── docs/                     # Technical architecture documentation
├── notebooks/                # Exploratory Jupyter analysis notebooks
├── tests/                    # Automated test suite (unit and integration)
│   ├── integration.py
│   ├── services.py
│   ├── test_app.py
│   ├── test_callbacks.py
│   └── test_components.py
├── pyproject.toml            # Project dependencies and tool configurations
├── uv.lock                   # Lockfile for reproducible dependency resolution
└── README.md
```

---

## Installation & Setup

### Prerequisites

- **Python**: version `3.12` or higher
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

### 1. Clone the Repository

```bash
git clone https://github.com/Scriber-Labs/kuramoto-dash-app.git
cd kuramoto-dash-app
```

### 2. Install Dependencies

Using `uv`:
```bash
uv sync
```

Or using standard `pip`:
```bash
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

pip install -e .
```

---

## Running the Application

Start the Dash development server:

```bash
# Using uv
uv run python -m app.app

# Or with an activated virtual environment
python -m app.app
```

Once running, navigate to `http://localhost:5000` (or `http://127.0.0.1:5000`) in your web browser.

---

## Running Tests

Execute the automated test suite using `pytest`:

```bash
# Using uv
uv run pytest

# Or with an activated virtual environment
pytest
```

---

## Tech Stack

- **Framework**: [Dash](https://dash.plotly.com/) & [Flask](https://flask.palletsprojects.com/)
- **Visualizations**: [Plotly](https://plotly.com/python/)
- **Simulation Engine**: [`kuramoto-benchmark-suite`](https://github.com/Scriber-Labs/kuramoto-benchmark-suite), [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), [NetworkX](https://networkx.org/)
- **Testing**: [pytest](https://docs.pytest.org/)
- **Code Quality**: [Ruff](https://docs.astral.sh/ruff/), [Black](https://github.com/psf/black)

---

## License

This project is licensed under the [MIT License](LICENSE).
