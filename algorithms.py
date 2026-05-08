"""
algorithms.py — Subtractive Clustering + Fuzzy C-Means pipeline
"""
import io
import base64

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import davies_bouldin_score, silhouette_score

from constants import FEATURE_COLS


# ──────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────

def parse_upload(contents: str, filename: str) -> pd.DataFrame:
    """Decode Dash Upload component's base64 content → DataFrame."""
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)

    if filename.lower().endswith(".csv"):
        df = pd.read_csv(
            io.BytesIO(decoded),
            sep=";",
            skipinitialspace=True,
            decimal=",",
        )
    else:
        raise ValueError(f"Format tidak didukung: {filename}. Gunakan CSV.")

    df.columns = [c.strip() for c in df.columns]
    return df


def preprocess(df: pd.DataFrame):
    """
    Clean numeric columns, normalize to [0,1].
    Returns (df_clean, X_scaled, scaler, available_cols).
    """
    pen_col = FEATURE_COLS[2]

    # Fix Pengeluaran if stored as "Rp8.776,00" string
    if pen_col in df.columns and not pd.api.types.is_numeric_dtype(df[pen_col]):
        def _parse_rp(val):
            if pd.isna(val):
                return np.nan
            s = str(val).strip().replace("Rp", "").replace(" ", "")
            if "." in s and "," in s:
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            try:
                return float(s)
            except ValueError:
                return np.nan

        df = df.copy()
        df[pen_col] = df[pen_col].apply(_parse_rp)

    available = []
    for col in FEATURE_COLS:
        if col in df.columns:
            if col != pen_col:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            available.append(col)

    if not available:
        raise ValueError(
            "Tidak ada kolom fitur yang cocok. "
            "Pastikan nama kolom CSV sama persis dengan yang diharapkan."
        )

    df_clean = df.dropna(subset=available).copy()
    scaler = MinMaxScaler()
    X = scaler.fit_transform(df_clean[available].values).astype(np.float64)
    return df_clean, X, scaler, available


# ──────────────────────────────────────────────
# SUBTRACTIVE CLUSTERING
# ──────────────────────────────────────────────

def subtractive_clustering(
    X: np.ndarray,
    ra: float = 0.5,
    rb_ratio: float = 1.5,
    accept_ratio: float = 0.5,
    reject_ratio: float = 0.15,
) -> tuple:
    """
    Determine cluster centers automatically from data density.

    Returns
    -------
    centers : ndarray  (n_clusters, n_features)
    pots    : list[float]
    """
    rb = ra * rb_ratio
    n = X.shape[0]
    half_ra2 = (ra / 2.0) ** 2
    half_rb2 = (rb / 2.0) ** 2

    # Vectorised potential calculation
    potentials = np.zeros(n)
    for i in range(n):
        diff_sq = np.sum((X - X[i]) ** 2, axis=1)
        potentials[i] = np.sum(np.exp(-diff_sq / half_ra2))

    centers, pots = [], []
    first_max = float(potentials.max())

    while True:
        idx = int(potentials.argmax())
        pot = float(potentials[idx])

        if not centers:
            centers.append(X[idx].copy())
            pots.append(pot)
        else:
            ratio = pot / first_max
            if ratio >= accept_ratio:
                centers.append(X[idx].copy())
                pots.append(pot)
            elif ratio <= reject_ratio:
                break
            else:
                d_min = min(np.linalg.norm(X[idx] - c) for c in centers)
                if (d_min / ra) + ratio >= 1.0:
                    centers.append(X[idx].copy())
                    pots.append(pot)
                else:
                    potentials[idx] = 0.0
                    continue

        if len(centers) >= 15:
            break

        # Suppress neighbourhood of the new center
        diff_sq = np.sum((X - centers[-1]) ** 2, axis=1)
        potentials -= pot * np.exp(-diff_sq / half_rb2)
        potentials = np.maximum(potentials, 0.0)

        if potentials.max() < reject_ratio * first_max:
            break

    return np.array(centers), pots


# ──────────────────────────────────────────────
# FUZZY C-MEANS
# ──────────────────────────────────────────────

def fuzzy_cmeans(
    X: np.ndarray,
    init_centers: np.ndarray,
    m: float = 2.0,
    max_iter: int = 100,
    eps: float = 1e-6,
) -> tuple:
    """
    Fuzzy C-Means initialised from SC centers (vectorised).

    Returns
    -------
    centers     : ndarray (c, d)
    U           : ndarray (c, n) — membership matrix
    obj_history : list[float]
    """
    n, _ = X.shape
    c = len(init_centers)
    centers = init_centers.astype(np.float64).copy()
    obj_history: list[float] = []
    exp = 2.0 / (m - 1.0)

    for _ in range(max_iter):
        # Distances  (c, n)
        dists = np.stack(
            [np.linalg.norm(X - centers[i], axis=1) for i in range(c)]
        )                                               # (c, n)
        dists_safe = np.maximum(dists, 1e-10)

        # Membership  U[i,k] = 1 / Σ_j (d_ik / d_jk)^exp
        ratios = (dists_safe[:, np.newaxis, :] / dists_safe[np.newaxis, :, :]) ** exp
        U = 1.0 / ratios.sum(axis=1)                  # (c, n)

        # Handle exact-zero distances
        zero_mask = dists == 0.0
        if zero_mask.any():
            U = np.where(zero_mask, 1.0, U)
            # Normalize columns that have any exact hit
            hit_cols = zero_mask.any(axis=0)
            U[:, hit_cols] = zero_mask[:, hit_cols].astype(float)
            row_sums = U[:, hit_cols].sum(axis=0)
            U[:, hit_cols] /= np.maximum(row_sums, 1e-10)

        # Update centers
        um = U ** m                                     # (c, n)
        centers_new = (um @ X) / um.sum(axis=1, keepdims=True)  # (c, d)

        # Objective function
        diff2 = np.sum((X[np.newaxis] - centers_new[:, np.newaxis]) ** 2, axis=2)
        obj = float(np.sum(um * diff2))
        obj_history.append(obj)

        if np.max(np.abs(centers_new - centers)) < eps:
            centers = centers_new
            break
        centers = centers_new

    return centers, U, obj_history


# ──────────────────────────────────────────────
# FULL PIPELINE
# ──────────────────────────────────────────────

def run_pipeline(df: pd.DataFrame, X: np.ndarray, scaler, avail_cols: list, **params) -> dict:
    """
    Execute full SC → FCM pipeline and return JSON-serialisable results dict.
    """
    from geo_data import COORDS

    ra         = float(params.get("ra",         0.50))
    rb_ratio   = float(params.get("rb_ratio",   1.50))
    accept_r   = float(params.get("accept_r",   0.50))
    reject_r   = float(params.get("reject_r",   0.15))
    m          = float(params.get("m",          2.00))
    max_iter   = int(  params.get("max_iter",   100))
    eps        = float(params.get("eps",        1e-6))

    # --- Stage 1: Subtractive Clustering ---
    sc_centers, _ = subtractive_clustering(X, ra, rb_ratio, accept_r, reject_r)
    n_cl = len(sc_centers)
    if n_cl < 2:
        raise ValueError(
            f"SC hanya menemukan {n_cl} cluster. Kecilkan nilai ra."
        )

    # --- Stage 2: Fuzzy C-Means ---
    final_centers, U, obj_history = fuzzy_cmeans(X, sc_centers, m, max_iter, eps)
    labels = np.argmax(U, axis=0)

    # --- Label mapping (sort by P0 ascending) ---
    centers_orig = scaler.inverse_transform(final_centers)
    sorted_idx   = np.argsort(centers_orig[:, 0])
    if n_cl == 2:
        cat_names = ["Kemiskinan Rendah", "Kemiskinan Tinggi"]
    elif n_cl == 3:
        cat_names = ["Kemiskinan Rendah", "Kemiskinan Sedang", "Kemiskinan Tinggi"]
    else:
        cat_names = [f"Kelompok {i + 1}" for i in range(n_cl)]
    label_map = {int(ci): cat_names[rank] for rank, ci in enumerate(sorted_idx)}

    # --- Enrich dataframe ---
    df_res = df.copy()
    df_res["_Cluster"]  = labels + 1
    df_res["_Kategori"] = [label_map[cl] for cl in labels]
    df_res["_Memb%"]    = (np.max(U, axis=0) * 100).round(2)
    for i in range(n_cl):
        df_res[f"_C{i+1}%"] = (U[i] * 100).round(2)

    # --- Coordinates ---
    kab_col = next((c for c in df.columns if "kab" in c.lower()), df.columns[1])
    df_res["_lat"] = df_res[kab_col].map(lambda x: COORDS.get(str(x).strip(), (None, None))[0])
    df_res["_lon"] = df_res[kab_col].map(lambda x: COORDS.get(str(x).strip(), (None, None))[1])

    # --- Evaluation ---
    dbi = float(davies_bouldin_score(X, labels))
    sil = float(silhouette_score(X, labels))

    return {
        "n_cl":         n_cl,
        "n_iter":       len(obj_history),
        "dbi":          round(dbi, 4),
        "sil":          round(sil, 4),
        "n_total":      len(df_res),
        "ra":           ra,
        "label_map":    {str(k): v for k, v in label_map.items()},
        "obj_history":  obj_history,
        "final_centers": final_centers.tolist(),
        "centers_orig":  centers_orig.tolist(),
        "cluster_sizes": {str(i): int((labels == i).sum()) for i in range(n_cl)},
        "avail_cols":   avail_cols,
        "kab_col":      kab_col,
        "df_json":      df_res.to_json(orient="records", date_format="iso"),
    }
