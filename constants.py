"""
constants.py — Feature definitions, neobrutalism theme tokens, chart base layout
"""

# ──────────────────────────────────────────────────────────────
# FEATURE COLUMNS — must match CSV headers exactly
# ──────────────────────────────────────────────────────────────
FEATURE_COLS = [
    "Persentase Penduduk Miskin (P0) Menurut Kabupaten/Kota (Persen)",
    "Rata-rata Lama Sekolah Penduduk 15+ (Tahun)",
    "Pengeluaran per Kapita Disesuaikan (Ribu Rupiah/Orang/Tahun)",
    "Indeks Pembangunan Manusia",
    "Umur Harapan Hidup (Tahun)",
    "Persentase rumah tangga yang memiliki akses terhadap sanitasi layak",
    "Persentase rumah tangga yang memiliki akses terhadap air minum layak",
    "Tingkat Pengangguran Terbuka",
    "Tingkat Partisipasi Angkatan Kerja",
    "PDRB atas Dasar Harga Konstan menurut Pengeluaran (x1jt)",
]

FEAT_SHORT = [
    "P0%", "LamaSekolah", "Pengeluaran", "IPM", "HarapanHidup",
    "Sanitasi%", "AirMinum%", "Pengangguran%", "Partisipasi%", "PDRB",
]

# ──────────────────────────────────────────────────────────────
# NEOBRUTALISM PALETTE
# ──────────────────────────────────────────────────────────────
NEO = {
    "bg":       "#F5F0E8",   # warm parchment background
    "card":     "#FFFFFF",
    "border":   "#0D0D0D",
    "yellow":   "#FFE500",
    "red":      "#FF3500",
    "blue":     "#0044FF",
    "green":    "#00D68F",
    "purple":   "#A200FF",
    "orange":   "#FF8000",
    "pink":     "#FF4D9E",
    "teal":     "#00C5CC",
    "text":     "#0D0D0D",
    "muted":    "#5C5C5C",
    "grid":     "#E2DDD4",
    "shadow":   "6px 6px 0px #0D0D0D",
    "shadow_sm":"3px 3px 0px #0D0D0D",
    "shadow_lg":"8px 8px 0px #0D0D0D",
}

# ──────────────────────────────────────────────────────────────
# CLUSTER COLORS  (bold, flat — no gradients)
# ──────────────────────────────────────────────────────────────
CLUSTER_COLORS   = ["#FF3500", "#0044FF", "#00D68F", "#FFE500", "#A200FF", "#FF4D9E", "#FF8000"]
CLUSTER_COLORS_RGBA = [
    [255, 53,   0],
    [0,   68,  255],
    [0,  214, 143],
    [255, 229,  0],
    [162,  0,  255],
    [255,  77, 158],
    [255, 128,  0],
]

# ──────────────────────────────────────────────────────────────
# PLOTLY BASE LAYOUT (applied to all charts)
# ──────────────────────────────────────────────────────────────
CHART_BASE = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FAFAF5",
    font=dict(family="DM Mono, JetBrains Mono, monospace", color="#0D0D0D", size=11),
    margin=dict(l=52, r=16, t=52, b=48),
    xaxis=dict(
        showgrid=True, gridcolor="#E2DDD4", gridwidth=1,
        showline=True, linecolor="#0D0D0D", linewidth=2.5,
        zeroline=False, tickfont_size=10,
    ),
    yaxis=dict(
        showgrid=True, gridcolor="#E2DDD4", gridwidth=1,
        showline=True, linecolor="#0D0D0D", linewidth=2.5,
        zeroline=False, tickfont_size=10,
    ),
    legend=dict(
        bgcolor="white",
        bordercolor="#0D0D0D",
        borderwidth=2,
        font_size=10,
    ),
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#0D0D0D",
        font=dict(color="#0D0D0D", size=11),
    ),
)
