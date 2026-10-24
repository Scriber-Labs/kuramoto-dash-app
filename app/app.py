"""Application entry point and server instance initialization for Kuramoto Lab."""

from __future__ import annotations

import os
from pathlib import Path

from dash import Dash

from app.callbacks import register_callbacks
from app.layout import create_layout

INDEX_STRING = """<!DOCTYPE html>
<html data-theme="night" class="dark night-theme" style="color-scheme: dark;">
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        <link rel="icon" type="image/png" href="/assets/images/favicon.png">
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

ASSETS_FOLDER = str(Path(__file__).resolve().parent.parent / "assets")

app = Dash(
    __name__,
    title="Kuramoto Lab",
    assets_folder=ASSETS_FOLDER,
)
app.index_string = INDEX_STRING
app.layout = create_layout
register_callbacks(app)

server = app.server

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8050"))
    app.run(host=host, port=port, debug=True)
