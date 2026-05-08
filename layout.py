"""
layout.py — Full Dash page layout, neobrutalism theme, zero sidebar
"""
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dash_table

from constants import NEO, CLUSTER_COLORS


# ──────────────────────────────────────────────────────────────
# STYLE HELPERS
# ──────────────────────────────────────────────────────────────
def neo_card(children, extra_style=None):
    s = {
        "background": NEO["card"],
        "border": f"3px solid {NEO['border']}",
        "boxShadow": NEO["shadow"],
        "padding": "20px 22px",
        "marginBottom": "24px",
    }
    if extra_style:
        s.update(extra_style)
    return html.Div(children, style=s)


def section_title(text, color=None):
    return html.P(text, style={
        "fontFamily": "DM Mono, monospace",
        "fontSize": "10px",
        "fontWeight": "700",
        "letterSpacing": "0.18em",
        "textTransform": "uppercase",
        "color": color or NEO["blue"],
        "borderBottom": f"2px solid {NEO['border']}",
        "paddingBottom": "8px",
        "marginBottom": "16px",
        "marginTop": "0",
    })


def param_input(label, id_, value, min_, max_, step, unit=""):
    return html.Div([
        html.Label(
            f"{label}" + (f" [{unit}]" if unit else ""),
            style={
                "fontSize": "10px", "fontWeight": "700",
                "letterSpacing": "0.1em", "textTransform": "uppercase",
                "color": NEO["muted"], "marginBottom": "4px",
                "display": "block",
            }),
        dbc.Input(
            id=id_, type="number", value=value,
            min=min_, max=max_, step=step,
            debounce=True,
            style={
                "border": f"3px solid {NEO['border']}",
                "borderRadius": "0",
                "fontFamily": "DM Mono, monospace",
                "fontWeight": "600",
                "fontSize": "13px",
                "background": "white",
                "padding": "6px 10px",
                "width": "100%",
                "boxShadow": "none",
            },
        ),
    ], style={"marginBottom": "12px"})


# ──────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────
def create_header():
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("SFCM", style={
                            "fontFamily": "'Syne', 'DM Mono', monospace",
                            "fontSize": "32px",
                            "fontWeight": "900",
                            "color": NEO["text"],
                            "letterSpacing": "-0.02em",
                            "lineHeight": "1",
                        }),
                        html.Span(" DASHBOARD", style={
                            "fontFamily": "DM Mono, monospace",
                            "fontSize": "32px",
                            "fontWeight": "900",
                            "color": NEO["red"],
                            "letterSpacing": "-0.02em",
                            "lineHeight": "1",
                        }),
                    ]),
                    html.P(
                        "Pemetaan Pusat Sebaran Kemiskinan — 514 Kabupaten/Kota Indonesia",
                        style={
                            "fontFamily": "DM Mono, monospace",
                            "fontSize": "11px",
                            "color": NEO["muted"],
                            "margin": "4px 0 0 0",
                            "letterSpacing": "0.04em",
                        }
                    ),
                ], width=8),
                dbc.Col([
                    html.Div([
                        html.Div("SC + FCM", style={
                            "fontFamily": "DM Mono, monospace",
                            "fontSize": "11px", "fontWeight": "700",
                            "letterSpacing": "0.12em",
                            "color": NEO["text"],
                            "background": NEO["yellow"],
                            "border": f"3px solid {NEO['border']}",
                            "padding": "4px 12px",
                            "display": "inline-block",
                        }),
                        html.Div("Subtractive + Fuzzy C-Means", style={
                            "fontSize": "10px", "color": NEO["muted"],
                            "marginTop": "4px",
                            "fontFamily": "DM Mono, monospace",
                        }),
                    ], style={"textAlign": "right"}),
                ], width=4, className="d-flex align-items-center justify-content-end"),
            ], align="center"),
        ], fluid=True),
    ], style={
        "background": NEO["yellow"],
        "borderBottom": f"4px solid {NEO['border']}",
        "padding": "18px 0",
        "marginBottom": "0",
    })


# ──────────────────────────────────────────────────────────────
# CONTROL PANEL
# ──────────────────────────────────────────────────────────────
def create_controls():
    upload_zone = dcc.Upload(
        id="upload-data",
        children=html.Div([
            html.Div("⬆", style={
                "fontSize": "36px", "lineHeight": "1",
                "marginBottom": "8px",
            }),
            html.Div("Drop CSV atau klik untuk upload",
                     style={"fontWeight": "700", "fontSize": "13px"}),
            html.Div("Format: titik-koma (;), desimal koma",
                     style={"fontSize": "10px", "color": NEO["muted"],
                            "marginTop": "4px", "fontFamily": "DM Mono, monospace"}),
        ], style={"textAlign": "center", "padding": "30px 10px"}),
        style={
            "border": f"3px dashed {NEO['border']}",
            "background": "#FAFAF5",
            "cursor": "pointer",
            "transition": "background 0.15s",
            "marginBottom": "10px",
        },
        multiple=False,
    )

    file_badge = html.Div(id="file-badge", style={"minHeight": "28px"})

    sc_params = dbc.Row([
        dbc.Col(param_input("Radius (ra)", "input-ra", 0.45, 0.10, 1.0, 0.05), width=3),
        dbc.Col(param_input("Squash (rb)", "input-rb", 1.5,  1.1,  2.5, 0.1),  width=3),
        dbc.Col(param_input("Accept ratio", "input-accept", 0.50, 0.2, 0.8, 0.05), width=3),
        dbc.Col(param_input("Reject ratio", "input-reject", 0.15, 0.05, 0.4, 0.05), width=3),
    ], className="g-2")

    fcm_params = dbc.Row([
        dbc.Col(param_input("Fuzziness (m)", "input-m", 2.0, 1.2, 4.0, 0.1), width=3),
        dbc.Col(param_input("Max iterasi",  "input-maxiter", 100, 50, 500, 10), width=3),
        dbc.Col(param_input("Toleransi ε",  "input-eps", 1e-5, 1e-7, 1e-3, 1e-7), width=3),
        dbc.Col([
            html.Div(style={"height": "28px"}),
            html.Button(
                "▶▶  JALANKAN  SFCM",
                id="btn-run",
                style={
                    "background": NEO["red"],
                    "color": "white",
                    "border": f"3px solid {NEO['border']}",
                    "boxShadow": NEO["shadow"],
                    "fontFamily": "DM Mono, monospace",
                    "fontWeight": "900",
                    "fontSize": "13px",
                    "letterSpacing": "0.1em",
                    "padding": "10px 0",
                    "width": "100%",
                    "cursor": "pointer",
                    "transition": "transform .08s, box-shadow .08s",
                },
                n_clicks=0,
                className="neo-run-btn",
            ),
        ], width=3),
    ], className="g-2")

    return dbc.Container([
        neo_card([
            dbc.Row([
                dbc.Col([
                    section_title("📂 Data Input"),
                    upload_zone,
                    file_badge,
                ], width=4),
                dbc.Col([
                    section_title("⚙ Subtractive Clustering"),
                    sc_params,
                    html.Div(style={"height": "12px"}),
                    section_title("⚙ Fuzzy C-Means"),
                    fcm_params,
                ], width=8),
            ], className="g-3"),
        ]),
        html.Div(id="alert-box"),
    ], fluid=True)


# ──────────────────────────────────────────────────────────────
# METRICS ROW
# ──────────────────────────────────────────────────────────────
def metric_card(value, label, accent=None):
    return html.Div([
        html.Div(str(value), style={
            "fontFamily": "DM Mono, monospace",
            "fontSize": "28px",
            "fontWeight": "900",
            "color": accent or NEO["blue"],
            "lineHeight": "1",
        }),
        html.Div(label, style={
            "fontFamily": "DM Mono, monospace",
            "fontSize": "9px",
            "fontWeight": "700",
            "letterSpacing": "0.14em",
            "textTransform": "uppercase",
            "color": NEO["muted"],
            "marginTop": "5px",
        }),
    ], style={
        "background": "white",
        "border": f"3px solid {NEO['border']}",
        "boxShadow": NEO["shadow_sm"],
        "padding": "14px 18px",
        "textAlign": "center",
    })


# ──────────────────────────────────────────────────────────────
# RESULTS SECTION  (hidden until algorithm runs)
# ──────────────────────────────────────────────────────────────
def create_results_section():
    return html.Div([
        dbc.Container([

            # ── Metrics ──────────────────────────────────
            html.Div(id="metrics-row", style={"marginBottom": "24px"}),

            # ── Cluster Summary Cards ─────────────────────
            html.Div(id="cluster-summary", style={"marginBottom": "24px"}),

            # ── Charts: Convergence + PCA ─────────────────
            neo_card([
                section_title("📈 Konvergensi & Sebaran Cluster"),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="chart-convergence", config={"displayModeBar": False}), width=6),
                    dbc.Col(dcc.Graph(id="chart-pca",         config={"displayModeBar": False}), width=6),
                ], className="g-3"),
            ]),

            # ── Charts: Pie + Bar ─────────────────────────
            neo_card([
                section_title("📊 Distribusi & Profil Indikator"),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="chart-pie",  config={"displayModeBar": False}), width=5),
                    dbc.Col(dcc.Graph(id="chart-bar",  config={"displayModeBar": False}), width=7),
                ], className="g-3"),
            ]),

            # ── Heatmap ───────────────────────────────────
            neo_card([
                section_title("🌡 Profil Pusat Cluster — Normalized Heatmap"),
                dcc.Graph(id="chart-heatmap", config={"displayModeBar": False}),
            ]),

        ], fluid=True),
    ], id="results-section", style={"display": "none"})


# ──────────────────────────────────────────────────────────────
# GEOSPATIAL MAP SECTION
# ──────────────────────────────────────────────────────────────
def create_map_section():
    layer_opts = [
        {"label": "● Scatter Titik",       "value": "scatter"},
        {"label": "🔥 Density Heatmap P0",  "value": "density"},
    ]
    style_opts = [
        {"label": "🗺 OpenStreetMap",  "value": "open-street-map"},
        {"label": "🌑 Carto Dark",     "value": "carto-darkmatter"},
        {"label": "🌫 Carto Light",    "value": "carto-positron"},
    ]

    def ctrl_label(text):
        return html.Label(text, style={
            "fontSize": "9px", "fontWeight": "700",
            "letterSpacing": "0.14em", "textTransform": "uppercase",
            "color": NEO["muted"], "display": "block", "marginBottom": "4px",
            "fontFamily": "DM Mono, monospace",
        })

    dropdown_style = {
        "border": f"3px solid {NEO['border']}",
        "borderRadius": "0",
        "fontFamily": "DM Mono, monospace",
        "fontSize": "12px",
    }

    return html.Div([
        dbc.Container([
            neo_card([
                section_title("🗺 PETA SEBARAN CLUSTER KEMISKINAN INDONESIA", NEO["red"]),

                # Map controls row
                dbc.Row([
                    dbc.Col([
                        ctrl_label("Layer Type"),
                        dcc.Dropdown(
                            id="map-layer", options=layer_opts,
                            value="scatter", clearable=False,
                            style=dropdown_style,
                        ),
                    ], width=3),
                    dbc.Col([
                        ctrl_label("Basemap Style"),
                        dcc.Dropdown(
                            id="map-style", options=style_opts,
                            value="open-street-map", clearable=False,
                            style=dropdown_style,
                        ),
                    ], width=3),
                    dbc.Col([
                        ctrl_label("Filter Cluster"),
                        dcc.Dropdown(
                            id="map-cluster-filter",
                            options=[], value=[], multi=True,
                            placeholder="Semua cluster...",
                            style=dropdown_style,
                        ),
                    ], width=6),
                ], className="g-3", style={"marginBottom": "16px"}),

                # Map container with thick border
                html.Div(
                    dcc.Graph(
                        id="chart-map",
                        config={"scrollZoom": True, "displayModeBar": True,
                                "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
                        style={"height": "520px"},
                    ),
                    style={
                        "border": f"3px solid {NEO['border']}",
                        "boxShadow": NEO["shadow"],
                        "overflow": "hidden",
                    },
                ),

                # Map stats bar
                html.Div(id="map-stats-bar", style={"marginTop": "12px"}),
            ]),

            # Province breakdown chart
            html.Div(id="province-chart-container"),

        ], fluid=True),
    ], id="map-section", style={"display": "none"})


# ──────────────────────────────────────────────────────────────
# DATA TABLE SECTION
# ──────────────────────────────────────────────────────────────
def create_table_section():
    return html.Div([
        dbc.Container([
            neo_card([
                section_title("📋 Tabel Hasil Lengkap"),
                dbc.Row([
                    dbc.Col([
                        dcc.Dropdown(
                            id="table-cluster-filter",
                            options=[], value=None,
                            placeholder="Filter: semua cluster...",
                            clearable=True,
                            style={
                                "border": f"3px solid {NEO['border']}",
                                "borderRadius": "0",
                                "fontFamily": "DM Mono, monospace",
                                "fontSize": "12px",
                            },
                        ),
                    ], width=4),
                    dbc.Col([
                        html.Button(
                            "⬇  Download Excel",
                            id="btn-download",
                            style={
                                "background": NEO["green"],
                                "color": "white",
                                "border": f"3px solid {NEO['border']}",
                                "boxShadow": NEO["shadow_sm"],
                                "fontFamily": "DM Mono, monospace",
                                "fontWeight": "700",
                                "fontSize": "12px",
                                "letterSpacing": "0.08em",
                                "padding": "8px 20px",
                                "cursor": "pointer",
                            },
                            n_clicks=0,
                        ),
                        dcc.Download(id="download-excel"),
                    ], width=4),
                ], className="g-2", style={"marginBottom": "14px"}),

                dash_table.DataTable(
                    id="table-results",
                    columns=[],
                    data=[],
                    page_size=15,
                    sort_action="native",
                    filter_action="native",
                    style_table={
                        "overflowX": "auto",
                        "border": f"3px solid {NEO['border']}",
                    },
                    style_header={
                        "backgroundColor": NEO["text"],
                        "color": "white",
                        "fontWeight": "700",
                        "fontFamily": "DM Mono, monospace",
                        "fontSize": "11px",
                        "letterSpacing": "0.06em",
                        "border": f"1px solid {NEO['border']}",
                        "padding": "10px 12px",
                    },
                    style_cell={
                        "fontFamily": "DM Mono, monospace",
                        "fontSize": "11px",
                        "padding": "8px 12px",
                        "border": f"1px solid {NEO['grid']}",
                        "backgroundColor": "white",
                        "color": NEO["text"],
                        "minWidth": "80px",
                    },
                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "#F5F0E8",
                        },
                        {
                            "if": {"filter_query": '{_Cluster} = 1'},
                            "borderLeft": f"4px solid {CLUSTER_COLORS[0]}",
                        },
                        {
                            "if": {"filter_query": '{_Cluster} = 2'},
                            "borderLeft": f"4px solid {CLUSTER_COLORS[1]}",
                        },
                        {
                            "if": {"filter_query": '{_Cluster} = 3'},
                            "borderLeft": f"4px solid {CLUSTER_COLORS[2]}",
                        },
                    ],
                    page_action="native",
                ),
            ]),
        ], fluid=True),
    ], id="table-section", style={"display": "none"})


# ──────────────────────────────────────────────────────────────
# SPINNER / LOADING OVERLAY
# ──────────────────────────────────────────────────────────────
def create_loading_overlay():
    return html.Div([
        html.Div([
            html.Div("⟳", style={
                "fontSize": "48px", "animation": "spin 1s linear infinite",
                "display": "block", "textAlign": "center",
            }),
            html.Div("MENJALANKAN SFCM...", style={
                "fontFamily": "DM Mono, monospace",
                "fontWeight": "900", "letterSpacing": "0.15em",
                "fontSize": "14px", "marginTop": "12px",
            }),
        ], style={
            "background": NEO["yellow"],
            "border": f"4px solid {NEO['border']}",
            "boxShadow": NEO["shadow_lg"],
            "padding": "32px 48px",
            "textAlign": "center",
        }),
    ], id="loading-overlay", style={"display": "none"})


# ──────────────────────────────────────────────────────────────
# STORES & FOOTER
# ──────────────────────────────────────────────────────────────
def create_stores():
    return html.Div([
        dcc.Store(id="store-results"),
        dcc.Store(id="store-df"),
    ])


def create_footer():
    return html.Div([
        html.Div(
            "SFCM Dashboard · Pemetaan Kemiskinan Indonesia · Plotly Dash",
            style={
                "fontFamily": "DM Mono, monospace",
                "fontSize": "10px",
                "color": NEO["muted"],
                "textAlign": "center",
                "padding": "24px",
                "borderTop": f"3px solid {NEO['border']}",
                "marginTop": "40px",
                "background": NEO["yellow"],
                "letterSpacing": "0.1em",
            }
        ),
    ])


# ──────────────────────────────────────────────────────────────
# MAIN LAYOUT
# ──────────────────────────────────────────────────────────────
def create_layout():
    return html.Div([
        # Google Fonts
        html.Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;900&display=swap",
        ),

        create_stores(),
        create_header(),

        html.Div(style={"height": "24px"}),
        create_controls(),

        create_results_section(),
        create_map_section(),
        create_table_section(),
        create_footer(),
    ], style={
        "background": NEO["bg"],
        "minHeight": "100vh",
        "fontFamily": "DM Mono, monospace",
    })
