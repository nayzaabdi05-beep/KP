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
st.title("📦 Dashboard Analisis Waktu Pemenuhan Material Request (MR)")
st.markdown("**PT Epsindo Jaya Pratama Workshop Duri** | *Monitoring & Evaluasi Lead Time*")
st.markdown("---")

# 2. Load dan Bersihkan Data
@st.cache_data
def load_data():
    file_path = 'DES 2025- JUNI 2026_EJP.xlsx'
    df = pd.read_excel(file_path)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    
    df_clean = df[['Part ID', 'Description', 'Qty', 'Unit', 'MR Date', 'Tgl Penyerahan']].dropna()
    
    df_clean['MR Date'] = pd.to_datetime(df_clean['MR Date'], errors='coerce')
    df_clean['Tgl Penyerahan'] = pd.to_datetime(df_clean['Tgl Penyerahan'], errors='coerce')
    df_clean = df_clean.dropna(subset=['MR Date', 'Tgl Penyerahan'])
    
    df_clean['Rentang_Hari'] = (df_clean['Tgl Penyerahan'] - df_clean['MR Date']).dt.days
    
    def categorize_lead_time(days):
        if days <= 1:
            return 'Cepat'
        elif days <= 3:
            return 'Standar'
        else:
            return 'Lambat'
            
    df_clean['Kategori'] = df_clean['Rentang_Hari'].apply(categorize_lead_time)
    return df_clean

df_clean = load_data()

# 3. Sidebar Filter Kategori Waktu
st.sidebar.header("⚙️ Kontrol & Filter")
st.sidebar.markdown("Pilih kategori waktu pemenuhan:")

selected_kategori = st.sidebar.multiselect(
    "Pilih Kategori:", 
    options=['Cepat', 'Standar', 'Lambat'], 
    default=['Cepat', 'Standar', 'Lambat']
)

# Proses Filter Data
filtered_df = df_clean[df_clean['Kategori'].isin(selected_kategori)]

# 4. Kotak Metrik Utama (KPIs)
st.markdown("### 📈 Ringkasan Performa")
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

# 5. Visualisasi Grafik & Insight
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### 📊 Proporsi Kategori Waktu")
    kategori_counts = filtered_df['Kategori'].value_counts().reindex(['Cepat', 'Standar', 'Lambat']).fillna(0)
    st.bar_chart(kategori_counts, color="#2E8B57")

with col_right:
    st.markdown("### 💡 Insight Singkat")
    if len(filtered_df) > 0:
        total = len(filtered_df)
        cepat_count = len(filtered_df[filtered_df['Kategori'] == 'Cepat'])
        persen_cepat = (cepat_count / total) * 100 if total > 0 else 0
        
        st.info(f"""
        * **Dominasi Layanan**: Sekitar **{persen_cepat:.1f}%** dari total transaksi terpilih berhasil diselesaikan dalam kategori **Cepat** ($\le$ 1 hari).
        * **Evaluasi**: Perhatikan transaksi yang masuk kategori **Lambat** (> 3 hari) untuk dianalisis kendala operasionalnya di lapangan.
        """)
    else:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter yang dipilih.")

st.markdown("---")

# 6. Tabel Detail Data
st.markdown("### 📋 Tabel Detail Transaksi Material Request")
st.dataframe(
    filtered_df[['Part ID', 'Description', 'Qty', 'Unit', 'MR Date', 'Tgl Penyerahan', 'Rentang_Hari', 'Kategori']], 
    use_container_width=True,
    height=400
)
