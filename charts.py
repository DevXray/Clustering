"""
charts.py — Plotly figure builders, all styled with neobrutalism tokens
"""
import copy

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.decomposition import PCA

from constants import CLUSTER_COLORS, FEAT_SHORT, CHART_BASE, NEO


# ── Utility ────────────────────────────────────────────────────
def _base_layout(title: str, extra: dict = None) -> dict:
    layout = copy.deepcopy(CHART_BASE)
    layout["title"] = dict(
        text=f"<b>{title}</b>",
        font=dict(size=13, color=NEO["text"]),
        x=0.02, xanchor="left",
    )
    if extra:
        layout.update(extra)
    return layout


# ── Convergence ────────────────────────────────────────────────
def make_convergence_fig(obj_history: list) -> go.Figure:
    x = list(range(1, len(obj_history) + 1))
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, y=obj_history,
        mode="lines+markers",
        line=dict(color=NEO["blue"], width=3),
        marker=dict(size=7, color=NEO["blue"],
                    line=dict(color=NEO["border"], width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(0,68,255,0.07)",
        hovertemplate="Iter %{x} — J = %{y:.4f}<extra></extra>",
    ))

    fig.add_annotation(
        x=len(obj_history), y=obj_history[-1],
        text=f"<b>Konvergen iter {len(obj_history)}<br>J = {obj_history[-1]:.2f}</b>",
        showarrow=True, arrowhead=2, arrowwidth=2,
        arrowcolor=NEO["green"],
        font=dict(color=NEO["green"], size=10),
        bgcolor="white", bordercolor=NEO["green"], borderwidth=2,
        ax=-80, ay=-44,
    )

    fig.update_layout(**_base_layout("Konvergensi Objective Function", {
        "xaxis_title": "Iterasi",
        "yaxis_title": "J (Objective)",
        "showlegend": False,
    }))
    return fig


# ── PCA Scatter ────────────────────────────────────────────────
def make_pca_fig(X: np.ndarray, labels: np.ndarray, centers: list, label_map: dict) -> go.Figure:
    n_cl = len(centers)
    pca  = PCA(n_components=2)
    Xp   = pca.fit_transform(X)
    Cp   = pca.transform(np.array(centers))
    pvar = pca.explained_variance_ratio_

    fig = go.Figure()
    for i in range(n_cl):
        mask = labels == i
        cat  = label_map.get(str(i), f"C{i+1}")
        col  = CLUSTER_COLORS[i]

        fig.add_trace(go.Scatter(
            x=Xp[mask, 0], y=Xp[mask, 1],
            mode="markers",
            marker=dict(color=col, size=7, opacity=0.65,
                        line=dict(color="rgba(0,0,0,0.25)", width=0.5)),
            name=f"C{i+1} — {cat}",
            hovertemplate=f"C{i+1}<br>PC1=%{{x:.3f}}, PC2=%{{y:.3f}}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[Cp[i, 0]], y=[Cp[i, 1]],
            mode="markers",
            marker=dict(symbol="star", color=col, size=22,
                        line=dict(color=NEO["border"], width=2)),
            name=f"Centroid C{i+1}",
            showlegend=False,
            hovertemplate=f"Centroid C{i+1}<extra></extra>",
        ))

    fig.update_layout(**_base_layout("Visualisasi Cluster — PCA 2D", {
        "xaxis_title": f"PC1 ({pvar[0]*100:.1f}%)",
        "yaxis_title": f"PC2 ({pvar[1]*100:.1f}%)",
    }))
    return fig


# ── Donut/Pie ──────────────────────────────────────────────────
def make_pie_fig(labels: np.ndarray, label_map: dict, n_cl: int) -> go.Figure:
    sizes = [(labels == i).sum() for i in range(n_cl)]
    lbls  = [f"C{i+1} — {label_map.get(str(i), '')}<br>({sizes[i]})" for i in range(n_cl)]

    fig = go.Figure(go.Pie(
        labels=lbls, values=sizes,
        hole=0.38,
        marker=dict(colors=CLUSTER_COLORS[:n_cl],
                    line=dict(color=NEO["border"], width=3)),
        textinfo="percent",
        textfont=dict(size=12, color=NEO["text"]),
        hovertemplate="%{label}<br>%{percent}<extra></extra>",
        pull=[0.04] * n_cl,
    ))

    fig.update_layout(**_base_layout("Distribusi Cluster", {
        "showlegend": True,
        "margin": dict(l=20, r=20, t=52, b=20),
    }))
    return fig


# ── Grouped Bar ────────────────────────────────────────────────
def make_bar_fig(final_centers: list, label_map: dict) -> go.Figure:
    centers  = np.array(final_centers)
    key_idx  = [0, 3, 5, 6, 7]
    key_lbls = ["P0%", "IPM", "Sanitasi%", "AirMinum%", "Pengangguran%"]
    n_cl     = len(final_centers)

    fig = go.Figure()
    for i in range(n_cl):
        vals = [float(centers[i, j]) for j in key_idx]
        fig.add_trace(go.Bar(
            name=f"C{i+1} — {label_map.get(str(i), '')}",
            x=key_lbls, y=vals,
            marker_color=CLUSTER_COLORS[i],
            marker_line=dict(color=NEO["border"], width=2),
            hovertemplate="%{x}: %{y:.3f}<extra></extra>",
        ))

    fig.update_layout(**_base_layout("Perbandingan Indikator Kunci", {
        "barmode": "group",
        "yaxis_title": "Nilai (0–1)",
        "yaxis_range": [0, 1.08],
        "bargap": 0.18,
        "bargroupgap": 0.06,
    }))
    return fig


# ── Heatmap ────────────────────────────────────────────────────
def make_heatmap_fig(final_centers: list, avail_cols: list, label_map: dict) -> go.Figure:
    centers    = np.array(final_centers)
    n_cl       = len(final_centers)
    feat_short = FEAT_SHORT[: len(avail_cols)]
    row_labels = [f"C{i+1}  ({label_map.get(str(i), '')[:14]})" for i in range(n_cl)]

    colorscale = [
        [0.00, "#FFFDE7"], [0.25, "#FFE500"],
        [0.55, "#FF8000"], [0.80, "#FF3500"],
        [1.00, "#6D0000"],
    ]

    fig = go.Figure(go.Heatmap(
        z=centers[:, : len(avail_cols)],
        x=feat_short,
        y=row_labels,
        colorscale=colorscale,
        zmin=0, zmax=1,
        text=np.round(centers[:, : len(avail_cols)], 2),
        texttemplate="<b>%{text}</b>",
        textfont=dict(size=11),
        colorbar=dict(
            title=dict(text="Nilai (0–1)", side="right"),
            outlinecolor=NEO["border"], outlinewidth=2,
            tickcolor=NEO["border"],
        ),
        hovertemplate="%{y}<br>%{x}: %{z:.3f}<extra></extra>",
    ))

    fig.update_layout(**_base_layout("Profil Pusat Cluster — Normalized", {
        "height": max(260, n_cl * 80 + 140),
        "margin": dict(l=180, r=80, t=60, b=90),
        "xaxis": dict(
            tickangle=-35, showgrid=False,
            showline=True, linecolor=NEO["border"], linewidth=2,
        ),
        "yaxis": dict(
            showgrid=False,
            showline=True, linecolor=NEO["border"], linewidth=2,
            tickfont=dict(size=11),
        ),
    }))
    return fig


# ── Geospatial Map ─────────────────────────────────────────────
def make_map_fig(
    df_geo: pd.DataFrame,
    label_map: dict,
    n_cl: int,
    kab_col: str = "",
    cluster_filter: list | None = None,
    layer_type: str = "scatter",
    map_style: str = "open-street-map",
) -> go.Figure:
    """
    OpenStreetMap-based geospatial map — no Mapbox token required.

    layer_type: 'scatter' | 'density'
    """
    df = df_geo.dropna(subset=["_lat", "_lon"]).copy()
    if cluster_filter:
        df = df[df["_Cluster"].isin(cluster_filter)]

    empty_map_layout = dict(
        mapbox=dict(style=map_style, center=dict(lat=-2.5, lon=118.0), zoom=4),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
    )

    if df.empty:
        return go.Figure(layout=empty_map_layout)

    p0_col = "Persentase Penduduk Miskin (P0) Menurut Kabupaten/Kota (Persen)"
    prov_col = next((c for c in df.columns if "prov" in c.lower()), None)

    if layer_type == "density":
        z = df[p0_col].fillna(0) if p0_col in df.columns else pd.Series(np.ones(len(df)))
        fig = go.Figure(go.Densitymapbox(
            lat=df["_lat"], lon=df["_lon"],
            z=z, radius=28,
            colorscale=[
                [0.0, "rgba(0,214,143,0)"],
                [0.3, "#FFE500"],
                [0.6, "#FF8000"],
                [1.0, "#FF3500"],
            ],
            showscale=True,
            colorbar=dict(
                title="P0 (%)",
                outlinecolor=NEO["border"], outlinewidth=2,
                bgcolor="white",
            ),
            hoverinfo="skip",
        ))
        fig.update_layout(**empty_map_layout)
        return fig

    # Scatter layer — one trace per cluster
    fig = go.Figure()
    for i in range(n_cl):
        sub = df[df["_Cluster"] == i + 1]
        if sub.empty:
            continue

        cat       = label_map.get(str(i), f"Cluster {i+1}")
        col       = CLUSTER_COLORS[i]
        p0_vals   = sub[p0_col] if p0_col in sub.columns else pd.Series(np.ones(len(sub)))
        kab_vals  = sub[kab_col] if kab_col and kab_col in sub.columns else sub.index.astype(str)
        prov_vals = sub[prov_col] if prov_col else pd.Series([""] * len(sub))

        # Size proportional to P0 for visual weight
        sizes = (p0_vals.fillna(5).clip(2, 50) / p0_vals.max() * 14 + 6).values

        custom = np.column_stack([
            kab_vals.values,
            prov_vals.values,
            sub["_Kategori"].values,
            p0_vals.round(2).values,
            sub["_Memb%"].values,
        ])

        fig.add_trace(go.Scattermapbox(
            lat=sub["_lat"], lon=sub["_lon"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=sizes,
                color=col,
                opacity=0.85,
                allowoverlap=True,
            ),
            name=f"C{i+1} — {cat}",
            customdata=custom,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Provinsi: %{customdata[1]}<br>"
                "Kategori: <b>%{customdata[2]}</b><br>"
                "P0: %{customdata[3]}%<br>"
                "Membership: %{customdata[4]}%"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        mapbox=dict(style=map_style, center=dict(lat=-2.5, lon=118.0), zoom=4),
        legend=dict(
            bgcolor="white", bordercolor=NEO["border"], borderwidth=3,
            font_size=11, orientation="v",
            x=0.01, y=0.99, xanchor="left", yanchor="top",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
        uirevision="map",
    )
    return fig


# ── Province Bar ────────────────────────────────────────────────
def make_province_bar(df_res: pd.DataFrame, n_cl: int, label_map: dict) -> go.Figure:
    """Stacked bar of cluster counts per province."""
    prov_col = next((c for c in df_res.columns if "prov" in c.lower()), None)
    if not prov_col:
        return go.Figure()

    summary = (
        df_res.groupby([prov_col, "_Cluster"])
        .size()
        .reset_index(name="Count")
    )
    provinces = (
        df_res.groupby(prov_col)["Persentase Penduduk Miskin (P0) Menurut Kabupaten/Kota (Persen)"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig = go.Figure()
    for i in range(n_cl):
        sub = summary[summary["_Cluster"] == i + 1].set_index(prov_col).reindex(provinces).fillna(0)
        fig.add_trace(go.Bar(
            x=provinces, y=sub["Count"],
            name=f"C{i+1} — {label_map.get(str(i), '')}",
            marker_color=CLUSTER_COLORS[i],
            marker_line=dict(color=NEO["border"], width=1.5),
        ))

    fig.update_layout(**_base_layout("Distribusi Cluster per Provinsi (diurutkan P0 tertinggi)", {
        "barmode": "stack",
        "xaxis_tickangle": -40,
        "yaxis_title": "Jumlah Kab/Kota",
        "height": 380,
        "margin": dict(l=52, r=16, t=60, b=120),
    }))
    return fig
