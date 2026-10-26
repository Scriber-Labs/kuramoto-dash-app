"""Plotly Cloud and WSGI deployment entrypoint for Kuramoto Lab."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure root and app package are discoverable
_root = Path(__file__).resolve().parent
_app_pkg = _root / "app"
for _p in (str(_root), str(_app_pkg)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

if "__path__" not in globals():
    __path__ = [str(_app_pkg)]

from app.app import app, server

if __name__ == "__main__":
    app.run(debug=True)
