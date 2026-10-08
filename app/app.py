"""Application entry point and server instance initialization for Kuramoto Lab."""

from __future__ import annotations

from pathlib import Path

from dash import Dash

from app.callbacks import register_callbacks
from app.layout import create_layout

INDEX_STRING = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        <link rel="icon" type="image/png" href="/assets/images/favicon.png">
        {%css%}
    </head>
    <body>
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
    app.run(host="0.0.0.0", port=8050, debug=True)
