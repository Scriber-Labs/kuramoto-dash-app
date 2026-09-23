# kuramoto-dash-app
Dash app interface for visualizing kuramoto model dynamics. Meant to be used in conjunction with kuramoto-benchmarke-suite

## Current File Tree
```aiignore
kuramoto-dash/
├── README.md
├── pyproject.toml
│
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── layout.py
│   │
│   ├── components/
│   ├── callbacks/
│   ├── services/
│   │   └── benchmark.py
│   └── config.py
│
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/              # ONLY if the existing Flask architecture needs it
│   └── ...
│
├── data/
│   └── examples/
│
├── notebooks/
│
├── tests/
│
└── docs/
    └── architecture.md
```