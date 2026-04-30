import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score, silhouette_score
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SFCM Dashboard — Pemetaan Kemiskinan Indonesia",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

.stApp {
    background: #0A0E1A;
    color: #E8EAF0;
}

section[data-testid="stSidebar"] {
    background: #0D1220;
    border-right: 1px solid #1E2A40;
}

.sidebar-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #4A90D9;
    letter-spacing: .12em;
    text-transform: uppercase;
    margin: 0 0 6px 0;
    padding: 12px 0 6px 0;
    border-bottom: 1px solid #1E2A40;
}

.metric-card {
    background: #111827;
    border: 1px solid #1E2A40;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: center;
}
.metric-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 26px;
    font-weight: 500;
    color: #4FC3F7;
    line-height: 1;
}
.metric-lbl {
    font-size: 11px;
    color: #6B7280;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: .08em;
}

.cluster-chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    margin: 3px 0;
}

.section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: #4A90D9;
    margin: 0 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #1E2A40;
}

div[data-testid="stHorizontalBlock"] > div {
    background: #111827;
    border: 1px solid #1E2A40;
    border-radius: 10px;
    padding: 14px;
}

.stSlider > div > div > div > div {
    background: #4A90D9 !important;
}

h1 { font-family: 'IBM Plex Mono', monospace !important; font-size: 20px !important; color: #E8EAF0 !important; }
h2 { font-family: 'IBM Plex Sans', sans-serif !important; font-size: 16px !important; color: #9CA3AF !important; font-weight: 400 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
FEATURE_COLS = [
    'Persentase Penduduk Miskin (P0) Menurut Kabupaten/Kota (Persen)',
    'Rata-rata Lama Sekolah Penduduk 15+ (Tahun)',
    'Pengeluaran per Kapita Disesuaikan (Ribu Rupiah/Orang/Tahun)',
    'Indeks Pembangunan Manusia',
    'Umur Harapan Hidup (Tahun)',
    'Persentase rumah tangga yang memiliki akses terhadap sanitasi layak',
    'Persentase rumah tangga yang memiliki akses terhadap air minum layak',
    'Tingkat Pengangguran Terbuka',
    'Tingkat Partisipasi Angkatan Kerja',
    'PDRB atas Dasar Harga Konstan menurut Pengeluaran (x1jt)'
]
FEAT_SHORT = ['P0%','LamaSekolah','Pengeluaran','IPM','HarapanHidup',
              'Sanitasi%','AirMinum%','Pengangguran%','Partisipasi%','PDRB']

DARK_BG   = '#0A0E1A'
CARD_BG   = '#111827'
BORDER    = '#1E2A40'
ACCENT    = '#4A90D9'
TEXT_MAIN = '#E8EAF0'
TEXT_MUT  = '#6B7280'
CLUSTER_COLORS = ['#EF4444','#3B82F6','#10B981','#F59E0B','#8B5CF6','#EC4899','#06B6D4']

plt.rcParams.update({
    'figure.facecolor': DARK_BG,
    'axes.facecolor':   CARD_BG,
    'axes.edgecolor':   BORDER,
    'axes.labelcolor':  TEXT_MUT,
    'xtick.color':      TEXT_MUT,
    'ytick.color':      TEXT_MUT,
    'text.color':       TEXT_MAIN,
    'grid.color':       BORDER,
    'grid.alpha':       1.0,
    'font.family':      'monospace',
    'font.size':        9,
})

# ─────────────────────────────────────────────
# ALGORITHMS
# ─────────────────────────────────────────────
def parse_pengeluaran(val):
    if pd.isna(val): return np.nan
    val = str(val).strip().replace('Rp','').replace(' ','')
    val = val.replace('.','').replace(',','.')
    try: return float(val)
    except: return np.nan

@st.cache_data
def load_and_preprocess(file_bytes):
    import io

    df = pd.read_csv(
        io.BytesIO(file_bytes),
        sep=';',
        skipinitialspace=True,
        decimal=','
    )
    df.columns = [c.strip() for c in df.columns]

    # Pengeluaran masih format string Rp8.776,00 — bersihkan khusus
    pen_col = 'Pengeluaran per Kapita Disesuaikan (Ribu Rupiah/Orang/Tahun)'
    if pen_col in df.columns and not pd.api.types.is_numeric_dtype(df[pen_col]):
        def _parse_rp(val):
            if pd.isna(val): return np.nan
            s = str(val).strip().replace('Rp','').replace(' ','')
            has_dot, has_comma = '.' in s, ',' in s
            if has_dot and has_comma:
                s = s.replace('.','').replace(',','.')
            elif has_comma and not has_dot:
                s = s.replace(',','.')
            try: return float(s)
            except: return np.nan
        df[pen_col] = df[pen_col].apply(_parse_rp)

    # Kolom lain pastikan numerik
    for col in FEATURE_COLS:
        if col in df.columns and col != pen_col:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    available = [c for c in FEATURE_COLS if c in df.columns]
    if not available:
        raise ValueError(
            "Tidak ada kolom fitur yang cocok. "
            "Pastikan nama kolom di file CSV sama persis dengan yang diharapkan."
        )

    df_clean = df.dropna(subset=available).copy()
    scaler = MinMaxScaler()
    X = scaler.fit_transform(df_clean[available].values)
    return df_clean, X, scaler, available


def subtractive_clustering(X, ra=0.5, rb_ratio=1.5, accept_ratio=0.5, reject_ratio=0.15):
    rb = ra * rb_ratio
    n  = X.shape[0]
    potentials = np.array([
        np.sum(np.exp(-np.sum((X - X[i])**2, axis=1) / (ra/2)**2))
        for i in range(n)
    ])
    centers, pots = [], []
    first_max = potentials.max()
    while True:
        idx = potentials.argmax()
        pot = potentials[idx]
        if not centers:
            centers.append(X[idx].copy()); pots.append(pot)
        else:
            ratio = pot / first_max
            if ratio >= accept_ratio:
                centers.append(X[idx].copy()); pots.append(pot)
            elif ratio <= reject_ratio:
                break
            else:
                d_min = min(np.linalg.norm(X[idx]-c) for c in centers)
                if (d_min/ra)+ratio >= 1:
                    centers.append(X[idx].copy()); pots.append(pot)
                else:
                    potentials[idx] = 0; continue
        if len(centers) >= 15: break
        diff_sq    = np.sum((X - centers[-1])**2, axis=1)
        potentials -= pot * np.exp(-diff_sq / (rb/2)**2)
        potentials  = np.maximum(potentials, 0)
        if potentials.max() < reject_ratio * first_max: break
    return np.array(centers), pots

def fuzzy_cmeans(X, init_centers, m=2.0, max_iter=100, eps=1e-6):
    n, d = X.shape
    c    = len(init_centers)
    centers = init_centers.copy()
    obj_history = []
    for it in range(max_iter):
        U = np.zeros((c, n))
        for i in range(c):
            for k in range(n):
                d_ik = np.linalg.norm(X[k] - centers[i])
                if d_ik == 0: U[i,k]=1.0; continue
                total = sum(
                    (d_ik/max(np.linalg.norm(X[k]-centers[j]),1e-10))**(2/(m-1))
                    for j in range(c))
                U[i,k] = 1.0/total
        centers_new = np.array([
            np.sum((U[i]**m)[:,None]*X,axis=0)/np.sum(U[i]**m) for i in range(c)])
        obj = sum((U[i,k]**m)*np.linalg.norm(X[k]-centers_new[i])**2
                  for i in range(c) for k in range(n))
        obj_history.append(obj)
        if np.max(np.abs(centers_new-centers)) < eps: break
        centers = centers_new.copy()
    return centers, U, obj_history

# ─────────────────────────────────────────────
# PLOT HELPERS (dark theme)
# ─────────────────────────────────────────────
def plot_convergence(obj_history):
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.plot(range(1,len(obj_history)+1), obj_history,
            color=ACCENT, lw=2, marker='o', ms=3.5, zorder=3)
    ax.fill_between(range(1,len(obj_history)+1), obj_history,
                    alpha=0.12, color=ACCENT)
    ax.set_xlabel('Iterasi')
    ax.set_ylabel('J (Objective)')
    ax.set_title('Konvergensi Objective Function', color=TEXT_MAIN, pad=8, fontsize=10)
    ax.grid(True, ls='--', lw=0.5)
    ax.annotate(f'iter {len(obj_history)}\nJ={obj_history[-1]:.2f}',
                xy=(len(obj_history), obj_history[-1]),
                xytext=(len(obj_history)*0.55, (obj_history[0]+obj_history[-1])/2),
                color='#10B981', fontsize=8,
                arrowprops=dict(arrowstyle='->', color='#10B981', lw=1))
    fig.tight_layout()
    return fig

def plot_scatter(X, cluster_labels, final_centers, label_map):
    pca     = PCA(n_components=2)
    X_pca   = pca.fit_transform(X)
    ctr_pca = pca.transform(final_centers)
    n_cl    = len(final_centers)
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    for i in range(n_cl):
        mask = cluster_labels == i
        ax.scatter(X_pca[mask,0], X_pca[mask,1],
                   c=CLUSTER_COLORS[i], s=14, alpha=0.55, label=f'C{i+1}')
        ax.scatter(ctr_pca[i,0], ctr_pca[i,1],
                   c=CLUSTER_COLORS[i], s=220, marker='*',
                   edgecolors='white', lw=0.7, zorder=5)
    pvar = pca.explained_variance_ratio_
    ax.set_xlabel(f'PC1 ({pvar[0]*100:.1f}%)')
    ax.set_ylabel(f'PC2 ({pvar[1]*100:.1f}%)')
    ax.set_title('Visualisasi Cluster (PCA 2D)', color=TEXT_MAIN, pad=8, fontsize=10)
    ax.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN)
    ax.grid(True, ls='--', lw=0.5)
    fig.tight_layout()
    return fig

def plot_pie(cluster_labels, label_map, n_cl):
    sizes = [(cluster_labels==i).sum() for i in range(n_cl)]
    lbls  = [f'C{i+1}\n{label_map[i][:14]}\n({sizes[i]})' for i in range(n_cl)]
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=lbls, colors=CLUSTER_COLORS[:n_cl],
        autopct='%1.1f%%', startangle=90,
        textprops={'color': TEXT_MUT, 'fontsize': 8})
    for at in autotexts:
        at.set_color(DARK_BG); at.set_fontweight('bold'); at.set_fontsize(8)
    ax.set_title('Distribusi Cluster', color=TEXT_MAIN, pad=8, fontsize=10)
    fig.tight_layout()
    return fig

def plot_heatmap(final_centers, feat_labels, label_map):
    n_cl = len(final_centers)
    feat_show = feat_labels[:10]
    ctr_df = pd.DataFrame(
        final_centers[:,:len(feat_show)],
        columns=[f[:10] for f in feat_show],
        index=[f'C{i+1} ({label_map[i][:10]})' for i in range(n_cl)]
    )
    fig, ax = plt.subplots(figsize=(5.5, max(2.5, n_cl*1.1)))
    sns.heatmap(ctr_df, annot=True, fmt='.2f', cmap='YlOrRd',
                ax=ax, linewidths=0.4, linecolor=BORDER,
                cbar_kws={'label':'Nilai (0-1)', 'shrink':0.8})
    ax.set_title('Profil Pusat Cluster (Normalized)', color=TEXT_MAIN, pad=8, fontsize=10)
    plt.setp(ax.get_xticklabels(), rotation=40, ha='right', fontsize=8)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=8)
    fig.tight_layout()
    return fig

def plot_bar_profile(final_centers, feat_labels, label_map):
    n_cl = len(final_centers)
    key_idx  = [0,3,5,6,7]
    key_lbls = ['P0%','IPM','Sanitasi%','AirMinum%','Pengangguran%']
    x = np.arange(len(key_idx))
    w = 0.8 / n_cl
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    for i in range(n_cl):
        vals = [float(final_centers[i,j]) for j in key_idx]
        offset = (i - n_cl/2 + 0.5) * w
        ax.bar(x + offset, vals, w*0.9,
               color=CLUSTER_COLORS[i], alpha=0.85, label=f'C{i+1}')
    ax.set_xticks(x); ax.set_xticklabels(key_lbls, fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('Nilai (0-1)')
    ax.set_title('Perbandingan Indikator Kunci', color=TEXT_MAIN, pad=8, fontsize=10)
    ax.legend(fontsize=8, framealpha=0, labelcolor=TEXT_MAIN)
    ax.grid(True, axis='y', ls='--', lw=0.5)
    fig.tight_layout()
    return fig

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-header">📂 Data</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload file CSV",
        type=['csv'],
        help="File Klasifikasi_Tingkat_Kemiskinan_di_Indonesia.csv"
    )

    st.markdown('<div class="sidebar-header">⚙️ Parameter Subtractive Clustering</div>', unsafe_allow_html=True)
    ra = st.slider('Radius (ra)', 0.20, 0.80, 0.50, 0.05,
                   help='Jarak pandang SC. Kecil = lebih banyak cluster')
    rb_ratio = st.slider('Squash factor', 1.1, 2.5, 1.5, 0.1,
                         help='rb = ra × squash factor')
    accept_r = st.slider('Accept ratio', 0.20, 0.80, 0.50, 0.05,
                         help='Ambang batas terima cluster baru')
    reject_r = st.slider('Reject ratio', 0.05, 0.40, 0.15, 0.05,
                         help='Ambang batas tolak cluster baru')

    st.markdown('<div class="sidebar-header">⚙️ Parameter Fuzzy C-Means</div>', unsafe_allow_html=True)
    m_fuzz    = st.slider('Fuzziness (m)', 1.2, 4.0, 2.0, 0.1,
                          help='Koefisien fuzziness. Standar = 2.0')
    max_iter  = st.slider('Max iterasi', 50, 500, 100, 50)
    eps       = st.select_slider('Toleransi (ε)',
                                  options=[1e-3,1e-4,1e-5,1e-6],
                                  value=1e-5,
                                  format_func=lambda x: f'{x:.0e}')

    run_btn = st.button('▶  Jalankan SFCM', use_container_width=True, type='primary')

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("# SFCM Dashboard")
st.markdown("## Pemetaan Pusat Sebaran Kemiskinan — 514 Kabupaten/Kota Indonesia")
st.divider()

# ─────────────────────────────────────────────
# MAIN LOGIC
# ─────────────────────────────────────────────
if uploaded is None:
    st.info("⬅️ Upload file CSV di sidebar untuk memulai.", icon="📂")
    st.stop()

file_bytes = uploaded.read()
try:
    df_clean, X, scaler, avail_cols = load_and_preprocess(file_bytes)
except Exception as e:
    st.error(f"Gagal membaca file: {e}")
    st.stop()

st.caption(f"✅ Data dimuat: **{len(df_clean)} baris** × **{len(avail_cols)} fitur**")

if not run_btn:
    st.info("Atur parameter di sidebar lalu tekan **▶ Jalankan SFCM**.", icon="⚙️")
    st.stop()

# ─────────────────────────────────────────────
# RUN ALGORITHM
# ─────────────────────────────────────────────
with st.spinner('Menjalankan Subtractive Clustering...'):
    sc_centers, sc_pots = subtractive_clustering(X, ra, rb_ratio, accept_r, reject_r)

n_cl = len(sc_centers)
if n_cl < 2:
    st.error(f"Subtractive Clustering hanya menemukan **{n_cl} cluster**. "
             "Coba kecilkan nilai **ra** (misalnya 0.30–0.50).")
    st.stop()

with st.spinner(f'Menjalankan Fuzzy C-Means ({n_cl} cluster)...'):
    final_centers, U_matrix, obj_history = fuzzy_cmeans(
        X, sc_centers, m_fuzz, max_iter, eps)

cluster_labels = np.argmax(U_matrix, axis=0)
df_clean = df_clean.copy()
df_clean['Cluster'] = cluster_labels + 1

centers_orig = scaler.inverse_transform(final_centers)
p0_vals    = centers_orig[:,0]
sorted_idx = np.argsort(p0_vals)
if n_cl == 2:
    cat_names = ['Kemiskinan Rendah','Kemiskinan Tinggi']
elif n_cl == 3:
    cat_names = ['Kemiskinan Rendah','Kemiskinan Sedang','Kemiskinan Tinggi']
else:
    cat_names = [f'Kelompok {i+1}' for i in range(n_cl)]
LABEL_MAP = {int(ci): cat_names[rank] for rank, ci in enumerate(sorted_idx)}
df_clean['Kategori'] = [LABEL_MAP[cl] for cl in cluster_labels]
df_clean['Memb_Max_%'] = (np.max(U_matrix, axis=0)*100).round(2)
for i in range(n_cl):
    df_clean[f'Memb_C{i+1}_%'] = (U_matrix[i]*100).round(2)

# Evaluasi
dbi = davies_bouldin_score(X, cluster_labels)
sil = silhouette_score(X, cluster_labels)

# ─────────────────────────────────────────────
# METRICS ROW
# ─────────────────────────────────────────────
m1, m2, m3, m4, m5, m6 = st.columns(6)
metrics = [
    (m1, n_cl,             "Cluster"),
    (m2, len(obj_history), "Iterasi"),
    (m3, f"{dbi:.4f}",     "DBI"),
    (m4, f"{sil:.4f}",     "Silhouette"),
    (m5, len(df_clean),    "Total Daerah"),
    (m6, f"{ra}",          "ra terpilih"),
]
for col, val, lbl in metrics:
    col.markdown(f"""<div class="metric-card">
        <div class="metric-val">{val}</div>
        <div class="metric-lbl">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CLUSTER SUMMARY
# ─────────────────────────────────────────────
st.markdown('<p class="section-title">Ringkasan Cluster</p>', unsafe_allow_html=True)
chip_cols = st.columns(n_cl)
for i in range(n_cl):
    n_i = (cluster_labels==i).sum()
    pct = n_i/len(cluster_labels)*100
    p0c = centers_orig[i][0]
    chip_cols[i].markdown(f"""
    <div style="background:{CLUSTER_COLORS[i]}22;border:1px solid {CLUSTER_COLORS[i]}55;
                border-radius:10px;padding:14px;text-align:center">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;
                    color:{CLUSTER_COLORS[i]};font-weight:500">Cluster {i+1}</div>
        <div style="font-size:12px;color:{TEXT_MAIN};margin:4px 0">{LABEL_MAP[i]}</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;
                    color:{CLUSTER_COLORS[i]};font-weight:600">{n_i}</div>
        <div style="font-size:11px;color:{TEXT_MUT}">daerah ({pct:.1f}%)</div>
        <div style="font-size:11px;color:{TEXT_MUT};margin-top:4px">P0 avg = {p0c:.2f}%</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CHARTS — ROW 1
# ─────────────────────────────────────────────
st.markdown('<p class="section-title">Visualisasi Hasil</p>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.pyplot(plot_convergence(obj_history), use_container_width=True)
with c2:
    st.pyplot(plot_scatter(X, cluster_labels, final_centers, LABEL_MAP),
              use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.pyplot(plot_pie(cluster_labels, LABEL_MAP, n_cl), use_container_width=True)
with c4:
    st.pyplot(plot_bar_profile(final_centers, avail_cols, LABEL_MAP),
              use_container_width=True)

# Heatmap full width
st.pyplot(plot_heatmap(final_centers, FEAT_SHORT, LABEL_MAP), use_container_width=True)

# ─────────────────────────────────────────────
# PUSAT CLUSTER TABLE
# ─────────────────────────────────────────────
st.markdown('<p class="section-title">Pusat Cluster (Nilai Asli)</p>', unsafe_allow_html=True)
ctr_tbl = pd.DataFrame(centers_orig,
    columns=FEAT_SHORT[:len(avail_cols)],
    index=[f'Cluster {i+1} — {LABEL_MAP[i]}' for i in range(n_cl)])
st.dataframe(ctr_tbl.round(4), use_container_width=True)

# ─────────────────────────────────────────────
# DATA TABLE
# ─────────────────────────────────────────────
st.markdown('<p class="section-title">Tabel Hasil Lengkap</p>', unsafe_allow_html=True)

kab_col = next((c for c in df_clean.columns if 'kab' in c.lower()), None)
prov_col = next((c for c in df_clean.columns if 'prov' in c.lower()), None)
show_cols = [c for c in [prov_col, kab_col, 'Cluster', 'Kategori', 'Memb_Max_%'] if c]
for i in range(n_cl):
    show_cols.append(f'Memb_C{i+1}_%')

filter_cl = st.selectbox("Filter cluster:", ['Semua'] + [f'Cluster {i+1}' for i in range(n_cl)])
df_show = df_clean[show_cols].copy()
if filter_cl != 'Semua':
    cl_num = int(filter_cl.split()[-1])
    df_show = df_show[df_show['Cluster'] == cl_num]

st.dataframe(df_show.reset_index(drop=True), use_container_width=True, height=340)

# Download
@st.cache_data
def to_excel(df):
    from io import BytesIO
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, sheet_name='Hasil SFCM', index=False)
    return buf.getvalue()

excel_data = to_excel(df_clean)
st.download_button(
    label="⬇️  Download Hasil (Excel)",
    data=excel_data,
    file_name="Hasil_SFCM_Kemiskinan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

st.caption("SFCM Dashboard · Pemetaan Kemiskinan Indonesia · Dibuat dengan Streamlit")