import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score, silhouette_score
import pydeck as pdk
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

# ─────────────────────────────────────────────
# KOORDINAT 514 KABUPATEN/KOTA INDONESIA
# ─────────────────────────────────────────────
COORDS = {
    "Aceh Barat": (-4.0757, 96.2497), "Aceh Barat Daya": (-3.7099, 96.8200),
    "Aceh Besar": (5.5483, 95.6036), "Aceh Jaya": (4.6126, 95.6192),
    "Aceh Selatan": (3.0145, 97.3676), "Aceh Singkil": (2.4793, 97.7989),
    "Aceh Tamiang": (4.1718, 97.8650), "Aceh Tengah": (4.5721, 96.8107),
    "Aceh Tenggara": (3.8315, 97.3435), "Aceh Timur": (4.5142, 97.8701),
    "Aceh Utara": (5.1810, 97.1638), "Bener Meriah": (4.6456, 96.6785),
    "Bireuen": (5.2072, 96.6955), "Gayo Lues": (3.8278, 97.1337),
    "Nagan Raya": (4.0500, 96.3667), "Pidie": (5.3772, 96.1314),
    "Pidie Jaya": (5.2312, 96.2573), "Simeulue": (2.6890, 96.1021),
    "Subulussalam": (2.6539, 98.0034), "Kota Banda Aceh": (5.5477, 95.3237),
    "Kota Langsa": (4.4683, 97.9706), "Kota Lhokseumawe": (5.1801, 97.1407),
    "Kota Sabang": (5.8930, 95.3215), "Kota Subulussalam": (2.6539, 98.0034),
    "Asahan": (2.9905, 99.7640), "Batubara": (3.0985, 99.5236),
    "Batu Bara": (3.0985, 99.5236), "Dairi": (2.5820, 98.3196),
    "Deli Serdang": (3.5596, 98.7918), "Humbang Hasundutan": (2.2734, 98.5064),
    "Karo": (3.1298, 98.4902), "Labuhanbatu": (2.0716, 99.5264),
    "Labuhan Batu": (2.0716, 99.5264), "Labuhanbatu Selatan": (1.8388, 100.0889),
    "Labuhan Batu Selatan": (1.8388, 100.0889), "Labuhanbatu Utara": (2.3618, 99.9013),
    "Labuhan Batu Utara": (2.3618, 99.9013), "Langkat": (4.0047, 98.2461),
    "Mandailing Natal": (0.8453, 99.2701), "Nias": (1.0764, 97.5228),
    "Nias Barat": (1.2798, 97.2056), "Nias Selatan": (0.4872, 97.8325),
    "Nias Utara": (1.3428, 97.5639), "Padang Lawas": (1.3791, 99.7642),
    "Padang Lawas Utara": (1.6986, 99.4628), "Pakpak Bharat": (2.7543, 98.2008),
    "Samosir": (2.5764, 98.8001), "Serdang Bedagai": (3.3691, 99.0158),
    "Simalungun": (2.9607, 99.0571), "Tapanuli Selatan": (1.5777, 99.3147),
    "Tapanuli Tengah": (1.9040, 98.6827), "Tapanuli Utara": (2.2553, 98.9756),
    "Toba Samosir": (2.3641, 99.1521), "Kota Binjai": (3.5999, 98.4851),
    "Kota Gunungsitoli": (1.2894, 97.6174), "Kota Medan": (3.5952, 98.6722),
    "Kota Padangsidimpuan": (1.3788, 99.2722),
    "Kota Pematangsiantar": (2.9595, 99.0687), "Kota Pematang Siantar": (2.9595, 99.0687),
    "Kota Sibolga": (1.7407, 98.7836), "Kota Tanjungbalai": (2.9667, 99.8000),
    "Kota Tanjung Balai": (2.9667, 99.8000), "Kota Tebing Tinggi": (3.3320, 99.1625),
    "Agam": (-0.2200, 100.2000), "Dharmasraya": (-1.0200, 101.4500),
    "Kepulauan Mentawai": (-2.4100, 99.6700), "Lima Puluh Kota": (-0.3600, 100.6500),
    "Padang Pariaman": (-0.5000, 100.1200), "Pasaman": (0.4500, 99.8700),
    "Pasaman Barat": (0.0800, 99.6500), "Pesisir Selatan": (-2.2000, 101.0000),
    "Sijunjung": (-0.7000, 101.0000), "Solok": (-0.9200, 100.6500),
    "Solok Selatan": (-1.3500, 101.3500), "Tanah Datar": (-0.4700, 100.5800),
    "Kota Bukittinggi": (-0.3050, 100.3690), "Kota Padang": (-0.9492, 100.3543),
    "Kota Padang Panjang": (-0.4633, 100.4133), "Kota Pariaman": (-0.6199, 100.1167),
    "Kota Payakumbuh": (-0.2167, 100.6333), "Kota Sawah Lunto": (-0.6783, 100.7833),
    "Kota Solok": (-0.7979, 100.6556),
    "Bengkalis": (1.4680, 102.1059), "Indragiri Hilir": (-0.3498, 103.0924),
    "Indragiri Hulu": (-0.3339, 102.5309), "Kampar": (0.3645, 101.0338),
    "Kepulauan Meranti": (1.0481, 102.7524), "Kuantan Singingi": (-0.5218, 101.4665),
    "Pelalawan": (0.0049, 102.1123), "Rokan Hilir": (2.1527, 100.8922),
    "Rokan Hulu": (0.9136, 100.4019), "Siak": (1.1267, 102.0006),
    "Kota Dumai": (1.6843, 101.4476), "Kota Pekanbaru": (0.5071, 101.4478),
    "Bintan": (1.0760, 104.5296), "Karimun": (1.0218, 103.4009),
    "Kepulauan Anambas": (3.1942, 106.1441), "Lingga": (0.2039, 104.6122),
    "Natuna": (3.9915, 108.3212), "Kota Batam": (1.1301, 104.0529),
    "Kota Tanjungpinang": (0.9185, 104.4603), "Kota Tanjung Pinang": (0.9185, 104.4603),
    "Batanghari": (-1.5882, 102.9503), "Batang Hari": (-1.5882, 102.9503),
    "Bungo": (-1.3958, 101.9963), "Kerinci": (-2.0852, 101.4728),
    "Merangin": (-2.3283, 102.3493), "Muaro Jambi": (-1.5882, 103.5879),
    "Sarolangun": (-2.2930, 102.7101), "Tanjung Jabung Barat": (-1.3946, 103.5024),
    "Tanjung Jabung Timur": (-0.9773, 104.2534), "Tebo": (-1.4723, 102.3882),
    "Kota Jambi": (-1.6101, 103.6131), "Kota Sungaipenuh": (-2.0841, 101.3970),
    "Kota Sungai Penuh": (-2.0841, 101.3970),
    "Banyuasin": (-2.8005, 104.7454), "Banyu Asin": (-2.8005, 104.7454),
    "Empat Lawang": (-3.9860, 102.8618), "Lahat": (-3.7893, 103.5277),
    "Muara Enim": (-3.6668, 103.7575), "Musi Banyuasin": (-2.9547, 103.7568),
    "Musi Rawas": (-3.1104, 102.9104), "Musi Rawas Utara": (-2.8104, 102.9104),
    "Ogan Ilir": (-3.3551, 104.5756), "Ogan Komering Ilir": (-3.7975, 104.8958),
    "Ogan Komering Ulu": (-4.3168, 104.2292),
    "Ogan Komering Ulu Selatan": (-4.7168, 104.0292),
    "Ogan Komering Ulu Timur": (-4.1168, 104.6292),
    "Penukal Abab Lematang Ilir": (-3.6668, 104.1575),
    "Kota Lubuklinggau": (-3.2968, 102.8618), "Kota Pagar Alam": (-4.0285, 103.2491),
    "Kota Palembang": (-2.9761, 104.7754), "Kota Prabumulih": (-3.4258, 104.2352),
    "Bangka": (-2.1729, 106.1065), "Bangka Barat": (-1.8200, 105.7200),
    "Bangka Selatan": (-2.9200, 106.3800), "Bangka Tengah": (-2.3200, 106.2200),
    "Belitung": (-2.7500, 107.6500), "Belitung Timur": (-2.7500, 108.2000),
    "Kota Pangkalpinang": (-2.1292, 106.1174), "Kota Pangkal Pinang": (-2.1292, 106.1174),
    "Bengkulu Selatan": (-4.5200, 103.1100), "Bengkulu Tengah": (-3.7200, 102.2700),
    "Bengkulu Utara": (-3.3600, 102.1400), "Kaur": (-4.9500, 103.4900),
    "Kepahiang": (-3.6400, 102.5800), "Lebong": (-3.0700, 102.3400),
    "Muko Muko": (-2.5400, 101.1100), "Mukomuko": (-2.5400, 101.1100),
    "Rejang Lebong": (-3.4600, 102.5500), "Seluma": (-4.1400, 102.5600),
    "Kota Bengkulu": (-3.7928, 102.2608),
    "Lampung Barat": (-5.0700, 104.1300), "Lampung Selatan": (-5.5900, 105.3900),
    "Lampung Tengah": (-4.8200, 105.3200), "Lampung Timur": (-5.0800, 105.8900),
    "Lampung Utara": (-4.8300, 104.9100), "Mesuji": (-4.0600, 105.3500),
    "Pesawaran": (-5.3100, 105.1100), "Pesisir Barat": (-5.1300, 103.9200),
    "Pringsewu": (-5.3600, 104.9700), "Tanggamus": (-5.4700, 104.6500),
    "Tulang Bawang": (-4.3700, 105.6700), "Tulangbawang": (-4.3700, 105.6700),
    "Tulang Bawang Barat": (-4.4700, 105.3700), "Way Kanan": (-4.3200, 104.4500),
    "Kota Bandar Lampung": (-5.3971, 105.2668), "Kota Metro": (-5.1130, 105.3067),
    "Lebak": (-6.5600, 106.2400), "Pandeglang": (-6.3100, 106.1100),
    "Serang": (-6.1200, 106.1500), "Tangerang": (-6.1800, 106.6300),
    "Kota Cilegon": (-6.0000, 106.0500), "Kota Serang": (-6.1100, 106.1600),
    "Kota Tangerang": (-6.1783, 106.6319), "Kota Tangerang Selatan": (-6.2882, 106.7159),
    "Bandung": (-7.0551, 107.6002), "Bandung Barat": (-6.9100, 107.4900),
    "Bekasi": (-6.3500, 107.0300), "Bogor": (-6.5971, 106.8060),
    "Ciamis": (-7.3300, 108.3500), "Cianjur": (-6.8200, 107.1400),
    "Cirebon": (-6.7320, 108.5523), "Garut": (-7.2217, 107.9014),
    "Indramayu": (-6.3277, 108.3254), "Karawang": (-6.3219, 107.3381),
    "Kuningan": (-6.9764, 108.4810), "Majalengka": (-6.8400, 108.2300),
    "Pangandaran": (-7.6900, 108.6600), "Purwakarta": (-6.5566, 107.4369),
    "Subang": (-6.5700, 107.7600), "Sukabumi": (-6.9200, 106.9300),
    "Sumedang": (-6.8537, 107.9225), "Tasikmalaya": (-7.3500, 108.2200),
    "Kota Bandung": (-6.9175, 107.6191), "Kota Banjar": (-7.3700, 108.5400),
    "Kota Bekasi": (-6.2349, 106.9896), "Kota Bogor": (-6.5971, 106.8060),
    "Kota Cimahi": (-6.8722, 107.5420), "Kota Cirebon": (-6.7320, 108.5523),
    "Kota Depok": (-6.4025, 106.7942), "Kota Sukabumi": (-6.9189, 106.9280),
    "Kota Tasikmalaya": (-7.3274, 108.2207),
    "Kepulauan Seribu": (-5.6100, 106.5700),
    "Kota Jakarta Barat": (-6.1681, 106.7591), "Kota Jakarta Pusat": (-6.1862, 106.8340),
    "Kota Jakarta Selatan": (-6.2615, 106.8106), "Kota Jakarta Timur": (-6.2250, 106.9004),
    "Kota Jakarta Utara": (-6.1248, 106.9004),
    "Banjarnegara": (-7.3833, 109.6888), "Banyumas": (-7.5200, 109.2900),
    "Batang": (-6.9152, 109.7303), "Blora": (-6.9622, 111.4135),
    "Boyolali": (-7.5200, 110.5900), "Brebes": (-6.8718, 109.0392),
    "Cilacap": (-7.7300, 109.0100), "Demak": (-6.8943, 110.6386),
    "Grobogan": (-7.0323, 110.8952), "Jepara": (-6.5894, 110.6677),
    "Karanganyar": (-7.5923, 110.9530), "Kebumen": (-7.6700, 109.6500),
    "Kendal": (-6.9228, 110.2012), "Klaten": (-7.7059, 110.5999),
    "Kudus": (-6.8048, 110.8390), "Magelang": (-7.4696, 110.2179),
    "Pati": (-6.7463, 111.0385), "Pekalongan": (-6.8887, 109.6753),
    "Pemalang": (-6.8900, 109.3800), "Purbalingga": (-7.3900, 109.3600),
    "Purworejo": (-7.7139, 110.0178), "Rembang": (-6.7053, 111.3440),
    "Semarang": (-7.0051, 110.4381), "Sragen": (-7.4255, 111.0270),
    "Sukoharjo": (-7.6800, 110.8400), "Tegal": (-6.8797, 109.1256),
    "Temanggung": (-7.3164, 110.1742), "Wonogiri": (-7.8200, 110.9200),
    "Wonosobo": (-7.3617, 109.9036), "Kota Magelang": (-7.4722, 110.2175),
    "Kota Pekalongan": (-6.8886, 109.6753), "Kota Salatiga": (-7.3305, 110.5084),
    "Kota Semarang": (-6.9667, 110.4167), "Kota Surakarta": (-7.5755, 110.8243),
    "Kota Tegal": (-6.8797, 109.1256),
    "Bantul": (-7.8885, 110.3286), "Gunungkidul": (-7.9700, 110.5900),
    "Gunung Kidul": (-7.9700, 110.5900), "Kulon Progo": (-7.8500, 110.1600),
    "Sleman": (-7.7172, 110.3552), "Kota Yogyakarta": (-7.7956, 110.3695),
    "Bangkalan": (-6.9067, 112.7317), "Banyuwangi": (-8.2192, 114.3691),
    "Blitar": (-8.0956, 112.1686), "Bojonegoro": (-7.1511, 111.8815),
    "Bondowoso": (-7.9117, 113.8220), "Gresik": (-7.1566, 112.6517),
    "Jember": (-8.1845, 113.7049), "Jombang": (-7.5556, 112.2384),
    "Kediri": (-7.8166, 112.0114), "Lamongan": (-7.1185, 112.4117),
    "Lumajang": (-8.1301, 113.2238), "Madiun": (-7.6298, 111.5229),
    "Magetan": (-7.6533, 111.3285), "Malang": (-7.9666, 112.6326),
    "Mojokerto": (-7.4716, 112.4337), "Nganjuk": (-7.6047, 111.9050),
    "Ngawi": (-7.4068, 111.4477), "Pacitan": (-8.1939, 111.0999),
    "Pamekasan": (-7.1579, 113.4736), "Pasuruan": (-7.6456, 112.9080),
    "Ponorogo": (-7.8706, 111.4641), "Probolinggo": (-7.7544, 113.2156),
    "Sampang": (-7.1886, 113.2475), "Sidoarjo": (-7.4458, 112.7182),
    "Situbondo": (-7.7060, 114.0069), "Sumenep": (-6.9900, 113.8600),
    "Trenggalek": (-8.0572, 111.7092), "Tuban": (-6.8980, 112.0508),
    "Tulungagung": (-8.0656, 111.9032), "Kota Blitar": (-8.0956, 112.1686),
    "Kota Kediri": (-7.8166, 112.0114), "Kota Madiun": (-7.6298, 111.5229),
    "Kota Malang": (-7.9666, 112.6326), "Kota Mojokerto": (-7.4716, 112.4337),
    "Kota Pasuruan": (-7.6456, 112.9080), "Kota Probolinggo": (-7.7544, 113.2156),
    "Kota Surabaya": (-7.2575, 112.7521), "Kota Batu": (-7.8681, 112.5270),
    "Badung": (-8.5781, 115.1875), "Bangli": (-8.4558, 115.3558),
    "Buleleng": (-8.1124, 115.0892), "Gianyar": (-8.5365, 115.3308),
    "Jembrana": (-8.3644, 114.6199), "Karangasem": (-8.4529, 115.6097),
    "Karang Asem": (-8.4529, 115.6097), "Klungkung": (-8.5407, 115.4024),
    "Tabanan": (-8.5380, 115.1275), "Kota Denpasar": (-8.6705, 115.2126),
    "Bima": (-8.4600, 118.7200), "Dompu": (-8.5300, 118.4600),
    "Lombok Barat": (-8.6500, 116.1000), "Lombok Tengah": (-8.7200, 116.2700),
    "Lombok Timur": (-8.6000, 116.5500), "Lombok Utara": (-8.3600, 116.1200),
    "Sumbawa": (-8.4800, 117.4200), "Sumbawa Barat": (-8.7900, 116.8900),
    "Kota Bima": (-8.4637, 118.7249), "Kota Mataram": (-8.5833, 116.1167),
    "Alor": (-8.2500, 124.5000), "Belu": (-9.1000, 124.8800),
    "Ende": (-8.8400, 121.6600), "Flores Timur": (-8.5200, 122.9800),
    "Kupang": (-10.1700, 123.6100), "Lembata": (-8.3300, 123.5000),
    "Malaka": (-9.3000, 124.9000), "Manggarai": (-8.6300, 120.4700),
    "Manggarai Barat": (-8.6200, 119.9000), "Manggarai Timur": (-8.6300, 120.9000),
    "Nagekeo": (-8.9000, 121.3000), "Ngada": (-8.6700, 121.0500),
    "Rote Ndao": (-10.7500, 123.0000), "Sabu Raijua": (-10.5000, 121.8000),
    "Sikka": (-8.6200, 122.2000), "Sumba Barat": (-9.6600, 119.4300),
    "Sumba Barat Daya": (-9.6600, 119.1000), "Sumba Tengah": (-9.5000, 119.6000),
    "Sumba Timur": (-9.6600, 120.2600), "Timor Tengah Selatan": (-9.7500, 124.2900),
    "Timor Tengah Utara": (-9.4500, 124.4500), "Kota Kupang": (-10.1615, 123.5764),
    "Bengkayang": (0.8100, 109.6800), "Kapuas Hulu": (0.9700, 114.0400),
    "Kayong Utara": (-1.1800, 109.9700), "Ketapang": (-1.8500, 110.0000),
    "Kubu Raya": (-0.1500, 109.3500), "Landak": (0.3700, 109.9600),
    "Melawi": (-0.0600, 111.7800), "Mempawah": (0.4000, 109.1500),
    "Sambas": (1.3600, 109.3000), "Sanggau": (0.1300, 110.5700),
    "Sekadau": (0.0200, 110.9500), "Sintang": (0.0700, 111.4800),
    "Kota Pontianak": (-0.0263, 109.3425), "Pontianak": (-0.0263, 109.3425),
    "Kota Singkawang": (0.9000, 108.9800),
    "Barito Selatan": (-1.9100, 114.8300), "Barito Timur": (-1.8400, 115.4600),
    "Barito Utara": (-0.9600, 114.8200), "Gunung Mas": (-1.3700, 113.9900),
    "Kapuas": (-2.0000, 114.3800), "Katingan": (-1.7000, 112.9700),
    "Kotawaringin Barat": (-2.5600, 111.7500), "Kotawaringin Timur": (-1.8300, 112.6000),
    "Lamandau": (-2.1300, 111.4800), "Murung Raya": (-0.8400, 114.5500),
    "Pulang Pisau": (-2.1200, 114.1500), "Seruyan": (-2.2500, 112.5700),
    "Sukamara": (-2.7200, 111.1200), "Kota Palangka Raya": (-2.2096, 113.9108),
    "Balangan": (-2.3100, 115.2000), "Banjar": (-3.6300, 114.8600),
    "Barito Kuala": (-3.1100, 114.5600), "Hulu Sungai Selatan": (-2.7200, 115.3500),
    "Hulu Sungai Tengah": (-2.5200, 115.5000), "Hulu Sungai Utara": (-2.0700, 115.2300),
    "Kotabaru": (-3.2800, 116.1800), "Kota Baru": (-3.2800, 116.1800),
    "Tabalong": (-2.0200, 115.4700), "Tanah Bumbu": (-3.5700, 115.8800),
    "Tanah Laut": (-3.7200, 115.1800), "Tapin": (-3.0400, 114.8700),
    "Kota Banjarbaru": (-3.4426, 114.8322), "Kota Banjar Baru": (-3.4426, 114.8322),
    "Kota Banjarmasin": (-3.3194, 114.5908),
    "Berau": (2.1600, 117.5000), "Kutai Barat": (-0.4200, 115.5800),
    "Kutai Kartanegara": (-0.4400, 117.1400), "Kutai Timur": (0.5500, 117.9500),
    "Mahakam Ulu": (0.0600, 115.5000), "Mahakam Hulu": (0.0600, 115.5000),
    "Paser": (-1.5800, 116.0000), "Penajam Paser Utara": (-1.2700, 116.6300),
    "Kota Balikpapan": (-1.2379, 116.8529), "Kota Bontang": (0.1335, 117.5007),
    "Kota Samarinda": (-0.5022, 117.1536),
    "Bulungan": (2.8600, 117.0800), "Malinau": (3.5900, 116.6200),
    "Nunukan": (4.1400, 117.6600), "Tana Tidung": (3.5100, 117.1600),
    "Kota Tarakan": (3.2972, 117.5937),
    "Bolaang Mongondow": (0.5500, 124.0200),
    "Bolaang Mongondow Selatan": (-0.4500, 124.0000),
    "Bolaang Mongondow Timur": (0.4500, 124.5500),
    "Bolaang Mongondow Utara": (0.8400, 124.2800),
    "Kepulauan Sangihe": (3.5700, 125.5700),
    "Kepulauan Siau Tagulandang Biaro": (2.7700, 125.4100),
    "Siau Tagulandang Biaro": (2.7700, 125.4100),
    "Kepulauan Talaud": (4.2800, 126.7800), "Minahasa": (1.3100, 124.8400),
    "Minahasa Selatan": (1.0200, 124.5500), "Minahasa Tenggara": (0.9300, 124.8200),
    "Minahasa Utara": (1.6300, 125.1100), "Kota Bitung": (1.4415, 125.1918),
    "Kota Kotamobagu": (0.7267, 124.3167), "Kota Manado": (1.4748, 124.8421),
    "Kota Tomohon": (1.3228, 124.8290),
    "Boalemo": (0.4400, 122.3700), "Bone Bolango": (0.5600, 123.1600),
    "Gorontalo": (0.5583, 123.0622), "Gorontalo Utara": (0.7700, 122.5000),
    "Pohuwato": (0.4700, 121.9300), "Kota Gorontalo": (0.5412, 123.0595),
    "Banggai": (-1.5700, 122.8300), "Banggai Kepulauan": (-1.7600, 123.5000),
    "Banggai Laut": (-1.9000, 123.2000), "Buol": (1.2000, 121.4500),
    "Donggala": (-0.6900, 119.9100), "Morowali": (-2.3200, 121.5000),
    "Morowali Utara": (-1.5600, 121.4500), "Parigi Moutong": (-0.4500, 120.2000),
    "Poso": (-1.4000, 120.7500), "Sigi": (-1.1500, 119.9100),
    "Tojo Una-Una": (-0.6200, 121.9900), "Toli-Toli": (1.0400, 120.8000),
    "Kota Palu": (-0.8917, 119.8707),
    "Bantaeng": (-5.5200, 119.9600), "Barru": (-4.4700, 119.6600),
    "Bone": (-4.5400, 120.3400), "Bulukumba": (-5.5400, 120.1900),
    "Enrekang": (-3.5700, 119.7800), "Gowa": (-5.2900, 119.7300),
    "Jeneponto": (-5.6800, 119.7200), "Kepulauan Selayar": (-6.1200, 120.4800),
    "Luwu": (-2.5100, 120.1900), "Luwu Timur": (-2.5400, 121.1600),
    "Luwu Utara": (-2.4500, 120.0800), "Maros": (-5.0100, 119.6700),
    "Pangkajene dan Kepulauan": (-4.7700, 119.5300),
    "Pangkajene Dan Kepulauan": (-4.7700, 119.5300),
    "Pinrang": (-3.7900, 119.6500), "Sidenreng Rappang": (-3.9900, 119.8400),
    "Sinjai": (-5.1200, 120.2500), "Soppeng": (-4.3400, 119.8700),
    "Takalar": (-5.4300, 119.4400), "Tana Toraja": (-2.9700, 119.8200),
    "Toraja Utara": (-2.8100, 119.7900), "Wajo": (-4.1500, 120.0300),
    "Kota Makassar": (-5.1477, 119.4327), "Kota Palopo": (-3.0000, 120.1967),
    "Kota Parepare": (-4.0135, 119.6297),
    "Majene": (-3.5400, 118.9700), "Mamasa": (-2.9300, 119.3300),
    "Mamuju": (-2.6800, 118.9000), "Mamuju Tengah": (-2.5000, 119.1500),
    "Pasangkayu": (-1.3200, 119.2500), "Mamuju Utara": (-1.3200, 119.2500),
    "Polewali Mandar": (-3.4100, 119.3700),
    "Bombana": (-4.5600, 121.7400), "Buton": (-4.9800, 122.7400),
    "Buton Selatan": (-5.2000, 122.7000), "Buton Tengah": (-4.9700, 122.4000),
    "Buton Utara": (-4.5700, 122.5500), "Kolaka": (-4.0600, 121.6200),
    "Kolaka Timur": (-4.1000, 121.9000), "Kolaka Utara": (-3.6300, 121.3600),
    "Konawe": (-4.0300, 122.5900), "Konawe Kepulauan": (-4.1300, 123.2500),
    "Konawe Selatan": (-4.5700, 122.4400), "Konawe Utara": (-3.3500, 122.0600),
    "Muna": (-4.7800, 122.6200), "Muna Barat": (-4.7800, 122.3000),
    "Wakatobi": (-5.4400, 123.5800), "Kota Baubau": (-5.4686, 122.6278),
    "Kota Kendari": (-3.9985, 122.5130),
    "Buru": (-3.4000, 126.7000), "Buru Selatan": (-3.8000, 126.5000),
    "Kepulauan Aru": (-6.2000, 134.4000), "Maluku Barat Daya": (-7.5000, 128.0000),
    "Maluku Tengah": (-3.3500, 129.1000), "Maluku Tenggara": (-5.6500, 132.7500),
    "Maluku Tenggara Barat": (-7.9500, 131.3000),
    "Seram Bagian Barat": (-3.1000, 128.3000),
    "Seram Bagian Timur": (-3.2000, 130.5000),
    "Kota Ambon": (-3.6954, 128.1814), "Kota Tual": (-5.6553, 132.7520),
    "Halmahera Barat": (1.2400, 127.5000), "Halmahera Selatan": (-0.7500, 127.8000),
    "Halmahera Tengah": (0.5000, 128.2000), "Halmahera Timur": (0.6900, 128.5000),
    "Halmahera Utara": (1.8000, 127.8000), "Kepulauan Sula": (-1.8500, 125.4500),
    "Pulau Morotai": (2.2500, 128.3000), "Pulau Taliabu": (-1.7500, 124.7500),
    "Kota Ternate": (0.7892, 127.3797), "Kota Tidore Kepulauan": (0.6800, 127.4000),
    "Fakfak": (-2.9200, 132.3000), "Kaimana": (-3.6500, 133.7500),
    "Manokwari": (-0.8660, 134.0820), "Manokwari Selatan": (-1.2000, 134.0000),
    "Maybrat": (-1.4500, 132.3500), "Pegunungan Arfak": (-1.5000, 133.8000),
    "Raja Ampat": (-0.4300, 130.5000), "Sorong": (-0.8700, 131.2600),
    "Sorong Selatan": (-1.8000, 131.4000), "Tambrauw": (-0.6500, 132.1000),
    "Teluk Bintuni": (-2.1200, 133.5000), "Teluk Wondama": (-2.5600, 134.4000),
    "Kota Sorong": (-0.8760, 131.2553),
    "Asmat": (-5.6500, 138.4000), "Biak Numfor": (-1.1800, 136.1000),
    "Boven Digoel": (-5.8700, 140.1300), "Deiyai": (-3.8000, 136.0000),
    "Dogiyai": (-3.9600, 136.1500), "Intan Jaya": (-3.8700, 136.7500),
    "Jayapura": (-2.5800, 140.5100), "Jayawijaya": (-3.9400, 138.9200),
    "Keerom": (-3.3000, 140.8000), "Kepulauan Yapen": (-1.6000, 136.2000),
    "Lanny Jaya": (-3.7800, 138.3000), "Mamberamo Raya": (-2.7000, 138.2000),
    "Mamberamo Tengah": (-3.5000, 138.5000), "Mappi": (-6.4000, 139.3000),
    "Merauke": (-8.4667, 140.3333), "Mimika": (-4.5400, 136.5300),
    "Nabire": (-3.3700, 135.5000), "Nduga": (-4.4000, 138.0000),
    "Nduga *": (-4.4000, 138.0000), "Paniai": (-3.9800, 136.4000),
    "Pegunungan Bintang": (-4.7000, 140.4000), "Puncak": (-3.8000, 137.2000),
    "Puncak Jaya": (-3.5500, 137.6000), "Sarmi": (-1.8700, 138.7500),
    "Supiori": (-0.7000, 135.5000), "Tolikara": (-3.6000, 138.4500),
    "Waropen": (-2.5000, 136.5000), "Yahukimo": (-4.5000, 139.4000),
    "Yalimo": (-4.0000, 138.7000), "Kota Jayapura": (-2.5337, 140.7181),
}

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
    ra = st.slider('Radius (ra)', 0.20, 1.00, 0.50, 0.05,
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


# ─────────────────────────────────────────────
# GEOSPATIAL MAP
# ─────────────────────────────────────────────
st.divider()
st.markdown('''<p class="section-title">🗺️ Peta Sebaran Cluster Kemiskinan Indonesia</p>''',
            unsafe_allow_html=True)

# Tambahkan lat/lon ke dataframe
kab_col_geo = next((c for c in df_clean.columns if 'kab' in c.lower()), next((c for c in df_clean.columns if 'kota' in c.lower()), df_clean.columns[1]))

df_geo = df_clean.copy()
df_geo['lat'] = df_geo[kab_col_geo].map(lambda x: COORDS.get(str(x).strip(), (None, None))[0])
df_geo['lon'] = df_geo[kab_col_geo].map(lambda x: COORDS.get(str(x).strip(), (None, None))[1])
df_geo_valid = df_geo.dropna(subset=['lat', 'lon'])
n_mapped = len(df_geo_valid)
n_total  = len(df_geo)

if n_mapped < n_total:
    st.caption(f"⚠️ {n_mapped}/{n_total} daerah berhasil dipetakan (koordinat tersedia).")
else:
    st.caption(f"✅ Semua {n_mapped} daerah berhasil dipetakan.")

# Warna RGB per cluster
CLUSTER_RGB_MAP = {
    1: [239, 68,  68],
    2: [59,  130, 246],
    3: [16,  185, 129],
    4: [245, 158, 11],
    5: [168, 85,  247],
}
df_geo_valid = df_geo_valid.copy()
df_geo_valid['color'] = df_geo_valid['Cluster'].apply(
    lambda c: CLUSTER_RGB_MAP.get(c, [156, 163, 175])
)

p0_col_name = FEATURE_COLS[0]  # P0 — selalu kolom pertama di FEATURE_COLS

# ── Kontrol peta ──
map_col1, map_col2, map_col3 = st.columns([1, 1, 2])
with map_col1:
    map_style_opt = st.selectbox("Basemap", [
        "mapbox://styles/mapbox/dark-v10",
        "mapbox://styles/mapbox/light-v10",
        "mapbox://styles/mapbox/satellite-v9",
        "mapbox://styles/mapbox/streets-v11",
    ], format_func=lambda x: {
        "mapbox://styles/mapbox/dark-v10":      "🌑 Dark",
        "mapbox://styles/mapbox/light-v10":     "☀️ Light",
        "mapbox://styles/mapbox/satellite-v9":  "🛰️ Satellite",
        "mapbox://styles/mapbox/streets-v11":   "🗺️ Streets",
    }.get(x, x))

with map_col2:
    map_type = st.selectbox("Tipe Layer", [
        "Scatter (titik)",
        "Heatmap Kemiskinan",
        "Column 3D",
    ])

with map_col3:
    cluster_opts = {i+1: f"Cluster {i+1} — {LABEL_MAP[i]}" for i in range(n_cl)}
    filter_map = st.multiselect(
        "Filter cluster",
        options=list(cluster_opts.keys()),
        default=list(cluster_opts.keys()),
        format_func=lambda x: cluster_opts[x]
    )

df_map = df_geo_valid[df_geo_valid['Cluster'].isin(filter_map)].copy() if filter_map else df_geo_valid.copy()

# ── Build tooltip ──
tooltip_content = (
    "<div style='background:#111827;padding:10px;border-radius:8px;"
    "border:1px solid #1E2A40;font-family:monospace;font-size:12px;color:#E8EAF0'>"
    "<b style='color:#4FC3F7'>{" + kab_col_geo + "}</b><br>"
    "Provinsi: {Provinsi}<br>"
    "Cluster: {Cluster} — {Kategori}<br>"
    "P0: {" + p0_col_name + "}%<br>"
    "Membership: {Memb_Max_%}%"
    "</div>"
)

# ── Build layer ──
if map_type == "Scatter (titik)":
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=16000,
        pickable=True,
        opacity=0.85,
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
        auto_highlight=True,
    )
    pitch = 0

elif map_type == "Heatmap Kemiskinan":
    layer = pdk.Layer(
        "HeatmapLayer",
        data=df_map,
        get_position=["lon", "lat"],
        get_weight=p0_col_name,
        aggregation="MEAN",
        radiusPixels=45,
        opacity=0.8,
        color_range=[
            [34,  197, 94,  180],
            [250, 204, 21,  200],
            [249, 115, 22,  220],
            [239, 68,  68,  230],
            [120, 0,   0,   255],
        ],
    )
    pitch = 0

else:  # Column 3D
    p0_max = float(df_map[p0_col_name].max()) if not df_map.empty else 1.0
    df_map['elevation'] = (df_map[p0_col_name] / p0_max * 300000).astype(float)
    layer = pdk.Layer(
        "ColumnLayer",
        data=df_map,
        get_position=["lon", "lat"],
        get_elevation="elevation",
        elevation_scale=1,
        radius=14000,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
        opacity=0.9,
        coverage=0.9,
    )
    pitch = 45

view_state = pdk.ViewState(
    latitude=-2.5,
    longitude=118.0,
    zoom=4,
    pitch=pitch,
    bearing=0,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style=map_style_opt,
    tooltip={"html": tooltip_content} if map_type != "Heatmap Kemiskinan" else True,
)
st.pydeck_chart(deck, use_container_width=True)

# ── Legenda peta ──
st.markdown("**Legenda:**")
leg_cols = st.columns(n_cl)
for i in range(n_cl):
    r, g, b = CLUSTER_RGB_MAP.get(i+1, [150, 150, 150])
    n_shown = int((df_map['Cluster'] == i+1).sum())
    leg_cols[i].markdown(
        f"<div style='display:flex;align-items:center;gap:8px;padding:4px 0'>"
        f"<div style='width:13px;height:13px;border-radius:50%;"
        f"background:rgb({r},{g},{b});flex-shrink:0'></div>"
        f"<span style='font-size:12px;color:var(--color-text-primary)'>"
        f"C{i+1} — {LABEL_MAP[i]} ({n_shown})</span></div>",
        unsafe_allow_html=True
    )

# ── Statistik per Provinsi ──
st.divider()
st.markdown('''<p class="section-title">📊 Statistik Kemiskinan Per Provinsi</p>''',
            unsafe_allow_html=True)

prov_col_name = next((c for c in df_clean.columns if 'prov' in c.lower()), 'Provinsi')
# Hitung statistik per provinsi
prov_base = df_clean.groupby(prov_col_name).agg(
    Total_Daerah=('Cluster', 'count'),
    Rata_P0=(p0_col_name, 'mean'),
    Rata_IPM=('Indeks Pembangunan Manusia', 'mean'),
).reset_index()
# Hitung jumlah per cluster secara terpisah
for ci in range(1, n_cl + 1):
    prov_base[f'Cluster {ci}'] = df_clean.groupby(prov_col_name)['Cluster'].apply(
        lambda x: int((x == ci).sum())
    ).reindex(prov_base[prov_col_name]).values
prov_stat = prov_base.sort_values('Rata_P0', ascending=False).round(2)

def color_p0_cell(val):
    try:
        v = float(val)
        if   v > 25: return 'background-color:#7f1d1d;color:white'
        elif v > 18: return 'background-color:#b91c1c;color:white'
        elif v > 12: return 'background-color:#b45309;color:white'
        elif v > 7:  return 'background-color:#365314;color:white'
        else:        return 'background-color:#14532d;color:white'
    except: return ''

st.dataframe(
    prov_stat.style.map(color_p0_cell, subset=['Rata_P0']),
    use_container_width=True,
    height=420,
)


st.caption("SFCM Dashboard · Pemetaan Kemiskinan Indonesia · Dibuat dengan Streamlit")