"""
callbacks.py — All Dash callbacks (uses `from dash import callback` — no circular import)
"""
import json
import io

import numpy as np
import pandas as pd
from dash import callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash import dash_table

from algorithms import parse_upload, preprocess, run_pipeline
from charts import (
    make_convergence_fig, make_pca_fig, make_pie_fig,
    make_bar_fig, make_heatmap_fig, make_map_fig, make_province_bar,
)
from constants import NEO, CLUSTER_COLORS, FEAT_SHORT


# ─────────────────────────────────────────────────────────────
# HELPER: cluster summary cards
# ─────────────────────────────────────────────────────────────
def _cluster_cards(results: dict):
    n_cl      = results["n_cl"]
    label_map = results["label_map"]
    sizes     = results["cluster_sizes"]
    c_orig    = results["centers_orig"]
    n_total   = results["n_total"]

    cols = []
    for i in range(n_cl):
        n_i  = sizes[str(i)]
        pct  = n_i / n_total * 100
        p0c  = c_orig[i][0]
        col  = CLUSTER_COLORS[i]
        cat  = label_map[str(i)]

        cols.append(dbc.Col(
            html.Div([
                html.Div(f"CLUSTER {i+1}", style={
                    "fontFamily": "DM Mono, monospace",
                    "fontSize": "9px", "fontWeight": "700",
                    "letterSpacing": "0.2em", "color": "white",
                    "background": col,
                    "padding": "4px 10px",
                    "borderBottom": f"2px solid {NEO['border']}",
                }),
                html.Div([
                    html.Div(cat, style={
                        "fontSize": "12px", "fontWeight": "700",
                        "color": NEO["text"], "margin": "10px 0 4px",
                        "fontFamily": "DM Mono, monospace",
                        "lineHeight": "1.2",
                    }),
                    html.Div(f"{n_i}", style={
                        "fontFamily": "DM Mono, monospace",
                        "fontSize": "36px", "fontWeight": "900",
                        "color": col, "lineHeight": "1",
                    }),
                    html.Div("daerah", style={
                        "fontSize": "10px", "color": NEO["muted"],
                        "fontFamily": "DM Mono, monospace",
                    }),
                    html.Div(f"{pct:.1f}%  ·  P0 avg {p0c:.2f}%", style={
                        "fontFamily": "DM Mono, monospace",
                        "fontSize": "10px", "color": NEO["muted"],
                        "marginTop": "6px",
                        "borderTop": f"1px solid {NEO['grid']}",
                        "paddingTop": "6px",
                    }),
                ], style={"padding": "0 14px 14px"}),
            ], style={
                "border": f"3px solid {NEO['border']}",
                "boxShadow": NEO["shadow_sm"],
                "background": "white",
                "overflow": "hidden",
            }),
            width=12 // n_cl if n_cl <= 4 else 4,
        ))

    return dbc.Row(cols, className="g-3", style={"marginBottom": "24px"})


# ─────────────────────────────────────────────────────────────
# HELPER: metrics row
# ─────────────────────────────────────────────────────────────
def _metrics_row(results: dict):
    items = [
        (results["n_cl"],    "Cluster",      NEO["red"]),
        (results["n_iter"],  "Iterasi",      NEO["blue"]),
        (results["dbi"],     "DBI ↓",        NEO["orange"]),
        (results["sil"],     "Silhouette ↑", NEO["green"]),
        (results["n_total"], "Total Daerah", NEO["purple"]),
        (results["ra"],      "ra terpilih",  NEO["text"]),
    ]
    cols = []
    for val, lbl, accent in items:
        cols.append(dbc.Col(
            html.Div([
                html.Div(str(val), style={
                    "fontFamily": "DM Mono, monospace",
                    "fontSize": "28px", "fontWeight": "900",
                    "color": accent, "lineHeight": "1",
                }),
                html.Div(lbl, style={
                    "fontFamily": "DM Mono, monospace",
                    "fontSize": "9px", "fontWeight": "700",
                    "letterSpacing": "0.14em", "textTransform": "uppercase",
                    "color": NEO["muted"], "marginTop": "5px",
                }),
            ], style={
                "background": "white",
                "border": f"3px solid {NEO['border']}",
                "boxShadow": "3px 3px 0 #0D0D0D",
                "padding": "14px 18px",
                "textAlign": "center",
            }),
        ))
    return dbc.Row(cols, className="g-3", style={"marginBottom": "24px"})


# ─────────────────────────────────────────────────────────────
# CALLBACK 1 — File badge update on upload
# ─────────────────────────────────────────────────────────────
@callback(
    Output("file-badge", "children"),
    Input("upload-data", "filename"),
    prevent_initial_call=True,
)
def update_file_badge(filename):
    if not filename:
        return ""
    return html.Div(
        f"✅  {filename}",
        style={
            "fontFamily": "DM Mono, monospace",
            "fontSize": "11px",
            "background": NEO["green"],
            "color": "white",
            "border": f"2px solid {NEO['border']}",
            "padding": "4px 10px",
            "fontWeight": "600",
            "display": "inline-block",
        },
    )


# ─────────────────────────────────────────────────────────────
# CALLBACK 2 — Run SFCM algorithm
# ─────────────────────────────────────────────────────────────
@callback(
    Output("store-results",  "data"),
    Output("store-df",       "data"),
    Output("alert-box",      "children"),
    Input("btn-run", "n_clicks"),
    State("upload-data", "contents"),
    State("upload-data", "filename"),
    State("input-ra",      "value"),
    State("input-rb",      "value"),
    State("input-accept",  "value"),
    State("input-reject",  "value"),
    State("input-m",       "value"),
    State("input-maxiter", "value"),
    State("input-eps",     "value"),
    prevent_initial_call=True,
)
def run_sfcm(n_clicks, contents, filename,
             ra, rb, accept_r, reject_r, m, max_iter, eps):
    if not contents:
        alert = html.Div("⚠ Belum ada file CSV yang diupload.",
                         style={"fontFamily": "DM Mono, monospace",
                                "background": NEO["yellow"],
                                "border": f"3px solid {NEO['border']}",
                                "padding": "10px 16px", "fontWeight": "700",
                                "marginBottom": "12px"})
        return no_update, no_update, alert

    try:
        # Guard against None inputs
        ra       = float(ra       or 0.45)
        rb       = float(rb       or 1.50)
        accept_r = float(accept_r or 0.50)
        reject_r = float(reject_r or 0.15)
        m        = float(m        or 2.00)
        max_iter = int(  max_iter or 100)
        eps      = float(eps      or 1e-5)

        df            = parse_upload(contents, filename)
        df_clean, X, scaler, avail_cols = preprocess(df)

        results = run_pipeline(
            df_clean, X, scaler, avail_cols,
            ra=ra, rb_ratio=rb, accept_r=accept_r, reject_r=reject_r,
            m=m, max_iter=max_iter, eps=eps,
        )

        # Separate the df_json for the store-df
        df_json = results.pop("df_json")
        return results, df_json, ""

    except Exception as exc:
        alert = html.Div([
            html.Strong("❌ ERROR: "),
            str(exc),
        ], style={
            "fontFamily": "DM Mono, monospace",
            "background": NEO["red"],
            "color": "white",
            "border": f"3px solid {NEO['border']}",
            "boxShadow": NEO["shadow_sm"],
            "padding": "10px 16px",
            "fontWeight": "600",
            "marginBottom": "12px",
        })
        return no_update, no_update, alert


# ─────────────────────────────────────────────────────────────
# CALLBACK 3 — Show/hide result sections + populate dropdown opts
# ─────────────────────────────────────────────────────────────
@callback(
    Output("results-section",        "style"),
    Output("map-section",            "style"),
    Output("table-section",          "style"),
    Output("metrics-row",            "children"),
    Output("cluster-summary",        "children"),
    Output("map-cluster-filter",     "options"),
    Output("map-cluster-filter",     "value"),
    Output("table-cluster-filter",   "options"),
    Input("store-results", "data"),
)
def show_sections(results):
    if not results:
        hidden = {"display": "none"}
        return hidden, hidden, hidden, [], [], [], [], []

    show = {"display": "block"}
    n_cl      = results["n_cl"]
    label_map = results["label_map"]

    metrics       = _metrics_row(results)
    cluster_cards = _cluster_cards(results)

    cl_opts = [
        {"label": f"C{i+1} — {label_map[str(i)]}", "value": i + 1}
        for i in range(n_cl)
    ]
    cl_all = list(range(1, n_cl + 1))

    return show, show, show, metrics, cluster_cards, cl_opts, cl_all, cl_opts


# ─────────────────────────────────────────────────────────────
# CALLBACK 4 — Update all analysis charts
# ─────────────────────────────────────────────────────────────
@callback(
    Output("chart-convergence", "figure"),
    Output("chart-pca",         "figure"),
    Output("chart-pie",         "figure"),
    Output("chart-bar",         "figure"),
    Output("chart-heatmap",     "figure"),
    Input("store-results", "data"),
    State("store-df",     "data"),
)
def update_charts(results, df_json):
    if not results or not df_json:
        empty = {"data": [], "layout": {"paper_bgcolor": "white",
                                        "plot_bgcolor": "#FAFAF5"}}
        return empty, empty, empty, empty, empty

    n_cl       = results["n_cl"]
    label_map  = results["label_map"]
    obj        = results["obj_history"]
    centers    = results["final_centers"]
    avail_cols = results["avail_cols"]

    df      = pd.DataFrame(json.loads(df_json))
    labels  = (df["_Cluster"] - 1).values
    X_cols  = [c for c in avail_cols if c in df.columns]
    X       = df[X_cols].values.astype(float) if X_cols else np.zeros((len(df), 1))

    fig_conv  = make_convergence_fig(obj)
    fig_pca   = make_pca_fig(X, labels, centers, label_map)
    fig_pie   = make_pie_fig(labels, label_map, n_cl)
    fig_bar   = make_bar_fig(centers, label_map)
    fig_heat  = make_heatmap_fig(centers, avail_cols, label_map)

    return fig_conv, fig_pca, fig_pie, fig_bar, fig_heat


# ─────────────────────────────────────────────────────────────
# CALLBACK 5 — Update geospatial map
# ─────────────────────────────────────────────────────────────
@callback(
    Output("chart-map",       "figure"),
    Output("map-stats-bar",   "children"),
    Output("province-chart-container", "children"),
    Input("store-results",      "data"),
    Input("map-layer",          "value"),
    Input("map-style",          "value"),
    Input("map-cluster-filter", "value"),
    State("store-df",           "data"),
)
def update_map(results, layer_type, map_style, cluster_filter, df_json):
    empty_fig = {
        "data": [],
        "layout": {
            "mapbox": {"style": "open-street-map",
                       "center": {"lat": -2.5, "lon": 118}, "zoom": 4},
            "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
            "paper_bgcolor": "white",
            "annotations": [{
                "text": "Jalankan SFCM terlebih dahulu",
                "x": 0.5, "y": 0.5, "xref": "paper", "yref": "paper",
                "font": {"size": 16, "color": "#888"},
                "showarrow": False,
            }],
        },
    }

    if not results or not df_json:
        return empty_fig, "", ""

    n_cl      = results["n_cl"]
    label_map = results["label_map"]
    kab_col   = results.get("kab_col", "")

    df = pd.DataFrame(json.loads(df_json))

    fig = make_map_fig(
        df, label_map, n_cl,
        kab_col=kab_col,
        cluster_filter=cluster_filter or None,
        layer_type=layer_type or "scatter",
        map_style=map_style or "open-street-map",
    )

    # Stats bar
    df_valid  = df.dropna(subset=["_lat", "_lon"])
    n_mapped  = len(df_valid)
    n_total   = len(df)
    stats_bar = html.Div(
        f"✅ {n_mapped} / {n_total} daerah berhasil dipetakan",
        style={
            "fontFamily": "DM Mono, monospace",
            "fontSize": "10px",
            "color": NEO["muted"],
            "fontWeight": "600",
            "letterSpacing": "0.06em",
        },
    )

    # Province chart
    prov_fig = make_province_bar(df, n_cl, label_map)
    prov_card = html.Div([
        html.Div([
            html.P("📊 DISTRIBUSI CLUSTER PER PROVINSI", style={
                "fontFamily": "DM Mono, monospace",
                "fontSize": "10px", "fontWeight": "700",
                "letterSpacing": "0.18em", "color": NEO["blue"],
                "borderBottom": f"2px solid {NEO['border']}",
                "paddingBottom": "8px", "marginBottom": "0",
            }),
            dcc.Graph(figure=prov_fig,
                      config={"displayModeBar": False},
                      style={"height": "380px"}),
        ], style={
            "background": "white",
            "border": f"3px solid {NEO['border']}",
            "boxShadow": NEO["shadow"],
            "padding": "20px 22px",
            "marginTop": "24px",
        }),
    ])

    return fig, stats_bar, prov_card


# ─────────────────────────────────────────────────────────────
# CALLBACK 6 — Update data table
# ─────────────────────────────────────────────────────────────
@callback(
    Output("table-results", "data"),
    Output("table-results", "columns"),
    Input("store-results",        "data"),
    Input("table-cluster-filter", "value"),
    State("store-df",             "data"),
)
def update_table(results, cluster_filter, df_json):
    if not results or not df_json:
        return [], []

    n_cl    = results["n_cl"]
    kab_col = results.get("kab_col", "")
    df      = pd.DataFrame(json.loads(df_json))

    # Select display columns
    prov_col = next((c for c in df.columns if "prov" in c.lower()), None)
    base_cols = [c for c in [prov_col, kab_col] if c]
    extra_cols = ["_Cluster", "_Kategori", "_Memb%"]
    mem_cols   = [f"_C{i+1}%" for i in range(n_cl) if f"_C{i+1}%" in df.columns]
    show_cols  = base_cols + extra_cols + mem_cols

    df_show = df[[c for c in show_cols if c in df.columns]].copy()

    if cluster_filter is not None:
        df_show = df_show[df_show["_Cluster"] == cluster_filter]

    df_show = df_show.reset_index(drop=True)

    columns = [
        {"name": c.replace("_", " ").strip(), "id": c}
        for c in df_show.columns
    ]
    return df_show.to_dict("records"), columns


# ─────────────────────────────────────────────────────────────
# CALLBACK 7 — Download Excel
# ─────────────────────────────────────────────────────────────
@callback(
    Output("download-excel", "data"),
    Input("btn-download", "n_clicks"),
    State("store-df", "data"),
    prevent_initial_call=True,
)
def download_excel(n_clicks, df_json):
    if not df_json:
        return no_update

    df  = pd.DataFrame(json.loads(df_json))
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Hasil SFCM", index=False)
    buf.seek(0)

    return dcc.send_bytes(buf.read(), "Hasil_SFCM_Kemiskinan.xlsx")
