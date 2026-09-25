# Kuramoto Lab (`kuramoto-dash-app`)

An interactive web dashboard for simulating, analyzing, and visualizing Kuramoto oscillator synchronization dynamics on complex networks. Built with **Dash** and **Plotly**, this application operates in conjunction with [`kuramoto-benchmark-suite`](https://github.com/Scriber-Labs/kuramoto-benchmark-suite) for benchmark-grade numerical simulations and reproducible dataset generation.

---

## Features

- **Interactive Parameter Exploration**:
  - **Oscillator Population**: Configurable count $N \in [2, 100]$.
  - **Coupling Strength**: Adjustable global coupling $K \in [0.0, 20.0]$.
  - **Temporal Controls**: Configurable simulation duration $t$, step size $dt$, and random seed for deterministic runs.
  - **Network Topologies**: All-to-All, Ring (1D lattice), and Random networks.
  - **Natural Frequency Distributions**: Normal (Gaussian), Uniform, Bimodal, Golden Ratio, and Custom frequency lists.
  - **Numerical Solvers**: High-precision Runge-Kutta 4th/5th order (`RK45`) and `Euler` integration.

- **Six Synchronized Visual Analytics Charts**:
  - **Phase Field (Unit Circle)**: Real-time oscillator positions on the complex unit circle with the collective order parameter vector $r e^{i \psi}$.
  - **Coupling Network**: Interactive 2D graph layout showing node connections and instantaneous oscillator phases.
  - **Order Parameter $r(t)$**: Coherence evolution over time quantifying phase synchronization ($0 \le r \le 1$).
  - **Natural Frequency Distribution**: Histogram and rug plot of sampled intrinsic frequencies $\omega_i$.
  - **Oscillator Phase History**: Color-mapped spatiotemporal heatmap of phase angles $\theta_i(t) \pmod{2\pi}$.
  - **Unwrapped Phase Trajectories**: Continuous trajectory traces over time for each individual oscillator.

- **Timeline & Playback Controls**:
  - Step through simulation frames using an interactive slider.
  - Play, pause, and reset animation playback with adjustable framerate heartbeat.

- **Benchmark Dataset Export**:
  - One-click export of simulation runs into compressed `.npz` archive files containing time steps, phase matrices $\theta(t)$, natural frequencies $\omega$, network adjacency matrices $A$, order parameter history $r(t)$, and configuration metadata.

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
│   ├── services/             # Core simulation and validation services
│   │   ├── benchmark.py      # Benchmark suite bridge & archive export
│   │   ├── simulation.py     # Numerical integration and topology setup
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