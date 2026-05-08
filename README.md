# SFCM Dashboard — Pemetaan Kemiskinan Indonesia
> **Plotly Dash** · Neobrutalism Theme · Geospatial Map · Multi-file

---

## Struktur File

```
sfcm_dash/
├── app.py           ← Entry point (jalankan ini)
├── layout.py        ← Semua komponen UI / layout
├── callbacks.py     ← Semua Dash callbacks (logika interaktif)
├── algorithms.py    ← Algoritma SC + FCM + pipeline
├── charts.py        ← Plotly figure builders
├── constants.py     ← Warna, fitur, tema neobrutalism
├── geo_data.py      ← Koordinat 514 Kab/Kota Indonesia
├── assets/
│   └── style.css    ← Neobrutalism CSS (auto-loaded Dash)
└── requirements.txt
```

---

## Cara Setup & Jalankan

### 1. Buat virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Jalankan aplikasi
```bash
python app.py
```

Buka browser: **http://localhost:8050**

---

## Cara Pakai

1. **Upload CSV** — klik atau drop file `Klasifikasi_Tingkat_Kemiskinan_di_Indonesia.csv`
   - Format: delimiter titik-koma (`;`), desimal koma (`,`)
2. **Atur Parameter** di panel kontrol:
   - `ra` — radius Subtractive Clustering (kecilkan → lebih banyak cluster)
   - `m` — fuzziness Fuzzy C-Means (standar = 2.0)
   - dst.
3. **Klik "JALANKAN SFCM"**
4. Hasil muncul:
   - Metrik (DBI, Silhouette, jumlah cluster, iterasi)
   - Grafik konvergensi, PCA scatter, pie distribusi, bar indikator, heatmap
   - **Peta geospatial** interaktif (Scatter / Density, 3 basemap pilihan)
   - Tabel data lengkap + **Download Excel**

---

## Fitur Geospatial Map

| Mode | Keterangan |
|------|------------|
| **Scatter Titik** | Setiap kab/kota = titik berwarna per cluster, ukuran ∝ P0% |
| **Density Heatmap** | Hotspot kemiskinan berdasarkan intensitas P0% |

Basemap tersedia:
- 🗺 **OpenStreetMap** (default, no API key)
- 🌑 **Carto Dark**
- 🌫 **Carto Positron**

---

## Catatan Teknis

- Tidak perlu Mapbox token — menggunakan OpenStreetMap tiles bawaan Plotly
- Algoritma SC + FCM ditulis murni NumPy (vectorised, tanpa library FCM eksternal)
- Semua callbacks menggunakan `from dash import callback` (Dash 2.x pattern) — bebas circular import
- Data disimpan sementara di `dcc.Store` (client-side JSON), tidak ada database

---

## Requirements

```
dash>=2.14.0
dash-bootstrap-components>=1.6.0
plotly>=5.18.0
pandas>=1.5.0
numpy>=1.23.0
scikit-learn>=1.2.0
openpyxl>=3.0.0
```
