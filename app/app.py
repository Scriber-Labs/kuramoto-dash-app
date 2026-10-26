"""Application entry point and server instance initialization for Kuramoto Lab."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure package path resolution works seamlessly across local runs and Plotly Cloud containers
_file_dir = Path(__file__).resolve().parent
_root_dir = _file_dir.parent
for _path_str in (str(_root_dir), str(_file_dir)):
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

# If loaded directly as the top-level 'app' module, declare __path__ so subpackages can be resolved
if "__path__" not in globals():
    __path__ = [str(_file_dir)]

from dash import Dash

try:
    from app.callbacks import register_callbacks
    from app.layout import create_layout
except (ImportError, ModuleNotFoundError):
    from callbacks import register_callbacks
    from layout import create_layout

def _resolve_assets_folder() -> str:
    """Resolve the assets directory across local development, packages, and cloud containers."""
    candidates = [
        _file_dir / "assets",
        _root_dir / "assets",
        Path.cwd() / "assets",
        Path.cwd() / "app" / "assets",
        Path("/home/appuser/app/assets"),
        Path("/home/appuser/assets"),
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "css").is_dir():
            return str(candidate.resolve())
    for candidate in candidates:
        if candidate.is_dir():
            return str(candidate.resolve())
    return str((_root_dir / "assets").resolve())


ASSETS_FOLDER = _resolve_assets_folder()

FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Aclonica&family=Fira+Code:wght@400;500;700&"
    "family=Merriweather:wght@300;400;700&"
    "family=Space+Grotesk:wght@400;500;600;700&display=swap"
)

INDEX_STRING = """<!DOCTYPE html>
<html data-theme="night" class="dark night-theme" style="color-scheme: dark;">
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        <link rel="icon" type="image/png" href="/assets/images/favicon.png">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Aclonica&family=Fira+Code:wght@400;500;700&family=Merriweather:wght@300;400;700&family=Space+Grotesk:wght@400;500;600;700&display=swap">
        {%css%}
    </head>
    <body class="night-theme">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

app = Dash(
    __name__,
    title="Kuramoto Lab",
    assets_folder=ASSETS_FOLDER,
    external_stylesheets=[FONTS_URL],
)
app.index_string = INDEX_STRING
app.layout = create_layout
register_callbacks(app)

server = app.server

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8050"))
    app.run(host=host, port=port, debug=True)
