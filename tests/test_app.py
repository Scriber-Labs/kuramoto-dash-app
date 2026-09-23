"""Unit tests for top-level Dash application instantiation and layout structure."""

from __future__ import annotations

from app.app import app, server
from app.layout import create_layout


def test_app_instance() -> None:
    assert app is not None
    assert app.title == "Kuramoto Lab"
    assert server is not None


def test_layout_structure() -> None:
    layout = create_layout()
    assert layout is not None
    # Verify presence of top-level children
    assert len(layout.children) >= 4
