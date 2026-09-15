import streamlit as st
import pandas as pd
import datetime

# Konfigurasi Halaman
st.set_page_config(
    page_title="Dashboard MR - EJP Duri",
    page_icon="📦",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 1. Judul Dashboard
st.title("Dashboard Analisis Waktu Pemenuhan Material Request (MR)")
st.markdown("**PT Epsindo Jaya Pratama Workshop Duri** | *Monitoring & Evaluasi Lead Time*")
st.markdown("---")

# 2. Load dan Bersihkan Data (Disamakan persis dengan Notebook Kerja Praktek)
@st.cache_data
def load_data():
    file_path = 'DES 2025- JUNI 2026_EJP.xlsx'
    df = pd.read_excel(file_path)
    
    # Menjadikan baris pertama sebagai header
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    
    # Memilih kolom utama
    df_clean = df[['Part ID', 'Description', 'Qty', 'Unit', 'MR Date', 'Tgl Penyerahan']].copy()
    
    # Menghapus baris kosong pada kolom krusial
    df_clean = df_clean.dropna(subset=['Part ID', 'MR Date', 'Tgl Penyerahan'])
    df_clean = df_clean.reset_index(drop=True)
    
    # Konversi format tanggal dengan aman
    df_clean['MR Date'] = pd.to_datetime(df_clean['MR Date'], errors='coerce')
    df_clean['Tgl Penyerahan'] = pd.to_datetime(df_clean['Tgl Penyerahan'], errors='coerce')
    df_clean = df_clean.dropna(subset=['MR Date', 'Tgl Penyerahan'])
    df_clean = df_clean.reset_index(drop=True)
    
    # Perhitungan Rentang Hari & Kategori
    df_clean['Rentang_Hari'] = (df_clean['Tgl Penyerahan'] - df_clean['MR Date']).dt.days
    
    def categorize_lead_time(days):
        if days <= 1:
            return 'Cepat'
        elif days <= 3:
            return 'Standar'
        else:
            return 'Lambat'
            
    df_clean['Kategori'] = df_clean['Rentang_Hari'].apply(categorize_lead_time)
    
    # Kolom Bulan untuk keperluan filter
    df_clean['Bulan'] = df_clean['MR Date'].dt.to_period('M').astype(str)
    
    return df_clean

df_clean = load_data()

# 3. Sidebar Filter & Pencarian
st.sidebar.header("Navigasi & Filter")
st.sidebar.markdown("Sesuaikan filter data analisis:")

# A. Filter Bulan
daftar_bulan = sorted(df_clean['Bulan'].unique())
opsi_bulan = ['Semua Bulan'] + daftar_bulan
selected_bulan = st.sidebar.selectbox("Pilih Bulan (Berdasarkan MR Date):", options=opsi_bulan)

st.sidebar.markdown("---")

# B. Fitur Pencarian Part ID / Deskripsi
st.sidebar.subheader("Pencarian Barang")
search_query = st.sidebar.text_input("Cari Part ID / Deskripsi:", "").strip().lower()

st.sidebar.markdown("---")

# C. Filter Kategori Waktu (Cepat, Standar, Lambat)
selected_kategori = st.sidebar.multiselect(
    "Pilih Kategori Waktu:", 
    options=['Cepat', 'Standar', 'Lambat'], 
    default=['Cepat', 'Standar', 'Lambat']
)

# 4. Proses Filter Data Bertingkat
filtered_df = df_clean.copy()

# Filter Bulan
if selected_bulan != 'Semua Bulan':
    filtered_df = filtered_df[filtered_df['Bulan'] == selected_bulan]

# Filter Kategori Waktu
filtered_df = filtered_df[filtered_df['Kategori'].isin(selected_kategori)]

# Filter Pencarian (Part ID atau Deskripsi)
if search_query:
    filtered_df = filtered_df[
        filtered_df['Part ID'].astype(str).str.lower().str.contains(search_query) | 
        filtered_df['Description'].astype(str).str.lower().str.contains(search_query)
    ]

# 5. Kotak Metrik Utama (KPIs)
info_label = f"Bulan: {selected_bulan}" + (f" | Pencarian: '{search_query}'" if search_query else "")
st.markdown(f"### Ringkasan Performa (*{info_label}*)")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total Transaksi", value=f"{len(filtered_df):,} Data")
with col2:
    avg_hari = filtered_df['Rentang_Hari'].mean() if len(filtered_df) > 0 else 0
    st.metric(label="Rata-rata Waktu Proses", value=f"{avg_hari:.2f} Hari")
with col3:
    max_hari = filtered_df['Rentang_Hari'].max() if len(filtered_df) > 0 else 0
    st.metric(label="Waktu Terlama", value=f"{max_hari} Hari")

st.markdown("---")

# 6. Visualisasi Grafik & Insight
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### Proporsi Kategori Waktu")
    kategori_counts = filtered_df['Kategori'].value_counts().reindex(['Cepat', 'Standar', 'Lambat']).fillna(0)
    st.bar_chart(kategori_counts, color="#2E8B57")

with col_right:
    st.markdown("### Insight & Informasi")
    if search_query:
        st.success(f"Menampilkan hasil pencarian untuk kata kunci: **'{search_query}'**")
        
    if len(filtered_df) > 0:
        total = len(filtered_df)
        cepat_count = len(filtered_df[filtered_df['Kategori'] == 'Cepat'])
        persen_cepat = (cepat_count / total) * 100 if total > 0 else 0
        
        st.info(f"""
        * **Dominasi Layanan**: Sekitar **{persen_cepat:.1f}%** dari data terpilih diselesaikan dalam kategori **Cepat** ($\le$ 1 hari).
        * **Catatan**: Gunakan kotak pencarian di sidebar untuk melacak item atau nomor part spesifik secara instan.
        """)
    else:
        st.warning("Tidak ada data yang cocok dengan pencarian atau filter yang dipilih.")

st.markdown("---")

# 7. Tabel Detail Data
st.markdown("### Tabel Detail Transaksi Material Request")
st.dataframe(
    filtered_df[['Part ID', 'Description', 'Qty', 'Unit', 'MR Date', 'Tgl Penyerahan', 'Rentang_Hari', 'Kategori']], 
    use_container_width=True,
    height=400
)
