# Kuramoto Dash App - Developer Guide

This document provides technical guidelines, build/configuration instructions, testing conventions, and architectural details for developers contributing to the `kuramoto-dash-app` codebase.

---

## 0. Agent Guideline Bridge (Scriber Core)

Shared house rules, design system tokens, and reusable code templates are maintained in the [`scriber-core`](https://github.com/eigenscribe/scriber-core) submodule, mounted at `.scriber-core/`. Treat the following as canonical references when generating, reviewing, or styling code:

- **Python Rules**: `.scriber-core/house-rules/python-rules.md`
- **CSS / UI System**: `.scriber-core/house-rules/css-rules.md`
- **Python Numeric Template**: `.scriber-core/boilerplates/python/gold-standard-boilerplate.py`
- **Visualization Bootstrap Template**: `.scriber-core/boilerplates/python/visualization_boilerplate.py`
- **CSS Design System Template**: `.scriber-core/boilerplates/css/tse-boilerplate.css`
- **Visuals & Graphs Template**: `.scriber-core/boilerplates/notebooks/visuals-boilerplate.ipynb`

---

## 1. Build and Configuration Instructions

### 1.1 Environment Requirements
- **Python**: `>= 3.12`
- **Package Layout**: Modular `app/` package architecture
- **Package Manager**: Compatible with standard `pip`, `venv`, or `uv`

### 1.2 Setup and Installation

#### Option A: Using `uv` (Recommended)
```bash
# Sync dependencies and development tools
uv sync

# Run the Dash web application
uv run python -m app.app

# Run automated tests
uv run pytest
```

#### Option B: Using Standard Python `venv` & `pip`
```bash
# Create and activate virtual environment
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install package and dependencies in editable mode
pip install -e .
```

### 1.3 Core Dependencies & Integrations
- **Web & Dashboard**: `dash>=4.4.1`, `plotly>=7.1.0`
- **Simulation Engine & Numerical Compute**: `kuramoto-benchmark-suite` (editable local bridge or package), `numpy>=2.5`, `scipy>=1.18`, `networkx>=3.7`, `pandas>=3.0`
- **Styling & Visualization**: `matplotlib>=3.11`
- **Development & QA**: `pytest>=9.1.1`, `black>=26.5.1`, `ruff>=0.16.8`

---

## 2. Testing Information

### 2.1 Test Configuration
- **Configuration File**: `pyproject.toml` (`[tool.pytest.ini_options]`)
- **Test Discovery Root**: `tests/`
- **Test Modules**: `tests/test_app.py`, `tests/test_callbacks.py`, `tests/test_components.py`, `tests/services.py`, `tests/integration.py`

### 2.2 Executing Tests
```bash
# Run all tests
pytest
# or via uv:
uv run pytest

# Run tests with verbose output
pytest -v

# Run a specific test module
pytest tests/test_callbacks.py
```

### 2.3 Guidelines for Adding New Tests
1. **File Location & Naming**: Add unit and integration tests inside `tests/` matching `test_*.py` or configured patterns.
2. **Deterministic Reproducibility**: Always pass explicit `seed` parameters when verifying simulation models or random distributions.
3. **Component & Callback Isolation**: Test Dash component factories and reactive callback handlers with mock triggers and validated figure dictionaries.

---

## 3. Architecture & Code Style Guidelines

### 3.1 Structural Code Layout ("Gold Standard" Pattern)
Modules adhere to the narrative flow:
> *"What exists → What you're allowed to call → How it works → Proof it works"*

- **Number-Emoji Semantic Sectioning**:
  - `0️⃣` / `🎭` **Definitions, Constants & Types**: Type aliases (`NDArray`, `Final`), protocols, global constants.
  - `1️⃣` **Public API / Component Factories**: Reusable UI blocks, figure generators, service registries.
  - `2️⃣` / `3️⃣` **Internal Logic & Helpers**: Private functions (`_internal_*`) encapsulating data transformations, callbacks, and validation.
  - `💨` **Smoke Tests**: Built-in sanity checks when run as standalone scripts.
  - `🔥` **Entry Point**: `if __name__ == "__main__":` orchestrating local server execution or smoke testing.

### 3.2 Python House Rules & Type Safety
- Include `from __future__ import annotations` at the top of modules.
- Use modern RNG: always instantiate `np.random.default_rng(seed)` instead of legacy global seeds.
- Type annotate function arguments and return types.
- Maintain explicit `__all__` declarations across all package `__init__.py` files.
- NumPy-style docstrings on public classes, functions, and registries.

### 3.3 CSS & UI Design System
- Dark mode first design conforming to the Scriber Experience glassmorphic baseline (`#0d1117` background, frosted glass panels, glowing borders).
- High-contrast ADHD semantic spectrum:
  - Primary Electric Blue / Cyan (`#14b5ff` / `#00e8ff`)
  - Secondary Cosmic Purple / Violet (`#9b7dff` / `#7652f5`)
  - Tertiary Neon Green (`#22f792` / `#10b981`)
  - Quaternary Coral / Orange (`#f78166`)

---

## 4. Key Subsystem Architecture

- **`app.app`**: Dash server entry point, server initialization, and main entrypoint.
- **`app.layout`**: Master dashboard layout scaffolding, integrating hero, sidebar controls, grid analytics, metric cards, and timeline controls.
- **`app.config`**: Centralized default parameters, validation boundaries, and color maps.
- **`app.callbacks`**: Reactive Dash callback registrations:
  - `simulation.py`: State management, simulation triggers, and parameter synchronization.
  - `visualization.py`: Six synchronized Plotly charts, graph layout rendering, and metric cards.
  - `dataset.py`: Animation interval stepping and `.npz` benchmark dataset exports.
- **`app.components`**: Modular UI components:
  - `controls.py`: Sidebar accordion parameter controls and timeline playback bar.
  - `plots.py`: High-performance Plotly figure builders.
  - `cards.py`: Metric summary cards, mathematical formula cards, and headers.
  - `tables.py`: Summary diagnostics and data views.
- **`app.services`**: Extensible domain services:
  - `topology.py`: `TopologyRegistry` (All-to-All, Ring, Random, Small-World, Tree of Life, Custom Adjacency).
  - `solvers.py`: `SolverRegistry` (RK45, Euler, Rotor Cl(2) integration).
  - `distributions.py`: `DistributionRegistry` (Normal, Uniform, Bimodal, Golden Ratio, Custom).
  - `diagnostics.py`: `DiagnosticRegistry` (Fourier FFT, Welch PSD, Graph Invariants).
  - `simulation.py`: End-to-end dataset generation orchestration.
  - `benchmark.py`: Exporting compressed `.npz` benchmark archives.
  - `cli_bridge.py`: CLI command configuration and execution bridge.
  - `validation.py`: Parameter validation boundaries and sanitization.
