import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Konfigurasi Halaman Dashboard (Layout Luas)
st.set_page_config(page_title="Dashboard Lead Time EJP", layout="wide")

# Konfigurasi Styling Grafik agar menyatu dengan tema gelap
plt.style.use('dark_background')

# Inject CSS Custom untuk Tema Gelap (Dark Mode) & Kerapian Tampilan
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stMetric {
        background-color: #1a1c23;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2f3241;
    }
    </style>
""", unsafe_allow_html=True)

st.title(" Dashboard Analisis & Klasifikasi Lead Time PT Epsindo Jaya Pratama")
st.markdown("Dashboard interaktif berbasis *Dark Mode* untuk memantau performa pengiriman material, tren bulanan, dan status kategori operasional.")

# 2. Load Data dengan Caching
@st.cache_data
def load_data():
    file_path = 'DES 2025- JULI 2026_EJP.xlsx'
    df = pd.read_excel(file_path, sheet_name=0)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    
    # --- BAGIAN YANG DIPERBAIKI: Mengubah nilai None/NaN agar rapi ---
    df['Part ID'] = df['Part ID'].fillna('Tidak Ada Part ID')
    df['Description'] = df['Description'].fillna('Tanpa Keterangan')
    # -----------------------------------------------------------------
    
    # Cleaning & Processing
    df_clean = df.dropna(subset=['MR Date', 'Tgl Penyerahan']).copy()
    df_clean['MR Date'] = pd.to_datetime(df_clean['MR Date'], errors='coerce')
    df_clean['Tgl Penyerahan'] = pd.to_datetime(df_clean['Tgl Penyerahan'], errors='coerce')
    df_clean['WO Date'] = pd.to_datetime(df_clean['WO Date'], errors='coerce')
    df_clean = df_clean.dropna(subset=['MR Date', 'Tgl Penyerahan']).reset_index(drop=True)
    
    # Hitung Rentang Hari & Kategori
    df_clean['Rentang_Hari'] = (df_clean['Tgl Penyerahan'] - df_clean['MR Date']).dt.days
    df_clean['WO_Month'] = df_clean['WO Date'].dt.month
    df_clean['WO_DayOfWeek'] = df_clean['WO Date'].dt.dayofweek
    
    # Mapping Nama Bulan agar lebih mudah dibaca
    month_names = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus', 
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    df_clean['Nama_Bulan'] = df_clean['WO_Month'].map(month_names)
    
    def kategorisasi_lead_time(hari):
        if hari <= 1:
            return 'Cepat'
        elif 2 <= hari <= 3:
            return 'Standar'
        else:
            return 'Lambat'
            
    df_clean['Kategori_LeadTime'] = df_clean['Rentang_Hari'].apply(kategorisasi_lead_time)
    return df_clean

try:
    df_data = load_data()
except Exception as e:
    st.error(f"Gagal memuat data Excel. Pastikan file 'DES 2025- JULI 2026_EJP.xlsx' ada di folder yang sama. Detail: {e}")
    st.stop()

# --- SIDEBAR: NAVIGASI MENU ---
st.sidebar.header("🔍 Panel Navigasi")
menu = st.sidebar.selectbox("Pilih Menu Analisis", [
    "Ringkasan Utama", 
    "Analisis Berdasarkan Bulan", 
    "Cari Berdasarkan Part ID"
])

# --- MENU 1: RINGKASAN UTAMA ---
if menu == "Ringkasan Utama":
    st.subheader("Ringkasan Keseluruhan Kategori Lead Time")
    
    col1, col2, col3, col4 = st.columns(4)
    total_data = len(df_data)
    cepat_count = (df_data['Kategori_LeadTime'] == 'Cepat').sum()
    standar_count = (df_data['Kategori_LeadTime'] == 'Standar').sum()
    lambat_count = (df_data['Kategori_LeadTime'] == 'Lambat').sum()
    
    col1.metric("Total Transaksi", f"{total_data} Data")
    col2.metric("Kategori Cepat", f"{cepat_count} Data")
    col3.metric("Kategori Standar", f"{standar_count} Data")
    col4.metric("Kategori Lambat", f"{lambat_count} Data")
    
    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Diagram Batang Distribusi")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=df_data, x='Kategori_LeadTime', order=['Cepat', 'Standar', 'Lambat'], palette='Blues_r', ax=ax)
        ax.set_title("Jumlah Transaksi per Kategori", color='white')
        st.pyplot(fig)
        
    with col_b:
        st.markdown("#### Diagram Persentase (Pie Chart)")
        fig, ax = plt.subplots(figsize=(6, 4))
        counts = df_data['Kategori_LeadTime'].value_counts()
        ax.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=['#1f77b4', '#aec7e8', '#ff7f0e'], startangle=140, textprops={'color': 'white'})
        ax.set_title("Persentase Kategori Lead Time", color='white')
        st.pyplot(fig)

# --- MENU 2: ANALISIS BERDASARKAN BULAN (SPESIFIK) ---
elif menu == "Analisis Berdasarkan Bulan":
    st.subheader(" Analisis Detail Kategori per Bulan")
    
    list_bulan = ['Desember', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli']
    selected_month = st.selectbox("Pilih Bulan Work Order:", list_bulan)
    
    df_month_filtered = df_data[df_data['Nama_Bulan'] == selected_month]
    
    st.markdown(f"### Rekapitulasi Bulan: **{selected_month}**")
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_total = len(df_month_filtered)
    m_cepat = (df_month_filtered['Kategori_LeadTime'] == 'Cepat').sum()
    m_standar = (df_month_filtered['Kategori_LeadTime'] == 'Standar').sum()
    m_lambat = (df_month_filtered['Kategori_LeadTime'] == 'Lambat').sum()
    
    m_col1.metric("Total Bulan Ini", f"{m_total} Data")
    m_col2.metric("Cepat (<= 1 Hari)", f"{m_cepat} Data")
    m_col3.metric("Standar (2-3 Hari)", f"{m_standar} Data")
    m_col4.metric("Lambat (> 3 Hari)", f"{m_lambat} Data")
    
    st.markdown("---")
    st.markdown(f"#### Tabel Transaksi Detail Bulan {selected_month}")
    st.dataframe(
        df_month_filtered[['Part ID', 'Description', 'MR Date', 'Tgl Penyerahan', 'Rentang_Hari', 'Kategori_LeadTime']], 
        use_container_width=True
    )

# --- MENU 3: PENCARIAN BERDASARKAN PART ID ---
elif menu == "Cari Berdasarkan Part ID":
    st.subheader(" Pencarian Status Kategori Berdasarkan Part ID")
    
    unique_parts = df_data['Part ID'].dropna().astype(str).unique()
    selected_part = st.selectbox("Pilih atau Ketik Part ID:", sorted(unique_parts))
    
    filtered_df = df_data[df_data['Part ID'].astype(str) == selected_part]
    
    st.markdown(f"Ditemukan **{len(filtered_df)}** riwayat transaksi untuk Part ID: **{selected_part}**")
    
    st.dataframe(
        filtered_df[['Part ID', 'Description', 'MR Date', 'Tgl Penyerahan', 'Rentang_Hari', 'Kategori_LeadTime']], 
        use_container_width=True
    )