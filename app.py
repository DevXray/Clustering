"""
app.py — Entry point: creates Dash instance, registers layout + callbacks, starts server.

Run:
    python app.py
Then open  http://localhost:8050
"""
import dash
import dash_bootstrap_components as dbc

# ── Create app ─────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        # DM Mono + Syne fonts
        "https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;0,500;1,400&family=Syne:wght@700;800;900&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="SFCM Dashboard — Kemiskinan Indonesia",
    update_title=None,
)
server = app.server   # expose for gunicorn / cloud deployment

# ── Register layout ────────────────────────────────────────────
from layout import create_layout  # noqa: E402
app.layout = create_layout()

# ── Register callbacks (side-effect import) ────────────────────
import callbacks  # noqa: F401, E402

# ── Run ────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(
        debug=True,
        host="localhost",
        port=8050,
        dev_tools_hot_reload=True,
    )
