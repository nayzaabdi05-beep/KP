import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Dashboard Lead Time EJP", layout="wide")

st.title("📊 Dashboard Analisis & Klasifikasi Lead Time PT Epsindo Jaya Pratama")
st.markdown("Dashboard interaktif untuk memvisualisasikan hasil eksplorasi data (*EDA*) dan analisis operasional gudang.")

# 1. Load Data dengan Caching agar performanya cepat di Cloud
@st.cache_data
def load_data():
    file_path = 'DES 2025- JULI 2026_EJP.xlsx'
    df = pd.read_excel(file_path, sheet_name=0)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    
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
    
    def kategorisasi_lead_time(hari):
        if hari <= 1:
            return 'Cepat'
        elif 2 <= hari <= 3:
            return 'Standar'
        else:
            return 'Lambat'
            
    df_clean['Kategori_LeadTime'] = df_clean['Rentang_Hari'].apply(kategorisasi_lead_time)
    return df_clean

# Panggil fungsi load data
try:
    df_data = load_data()
except Exception as e:
    st.error(f"Gagal memuat data Excel. Pastikan nama file 'DES 2025- JULI 2026_EJP.xlsx' sudah benar dan berada di folder yang sama. Detail error: {e}")
    st.stop()

# --- SIDEBAR: NAVIGASI MENU ---
st.sidebar.header("🔍 Panel Navigasi")
menu = st.sidebar.selectbox("Pilih Menu Analisis", ["Ringkasan Utama", "Analisis Tren Bulanan", "Cari Berdasarkan Part ID"])

# --- MENU 1: RINGKASAN UTAMA ---
if menu == "Ringkasan Utama":
    st.subheader("📌 Ringkasan Distribusi Kategori Lead Time")
    
    # Metric Cards
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
    
    # Visualisasi Diagram Batang & Pie Chart
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### Diagram Batang Distribusi")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=df_data, x='Kategori_LeadTime', order=['Cepat', 'Standar', 'Lambat'], palette='Blues_d', ax=ax)
        ax.set_title("Jumlah Transaksi per Kategori")
        st.pyplot(fig)
        
    with col_b:
        st.markdown("#### Diagram Persentase (Pie Chart)")
        fig, ax = plt.subplots(figsize=(6, 4))
        counts = df_data['Kategori_LeadTime'].value_counts()
        ax.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=['#4682B4', '#87CEEB', '#B0E0E6'], startangle=140)
        ax.set_title("Persentase Kategori Lead Time")
        st.pyplot(fig)

# --- MENU 2: ANALISIS TREN BULANAN ---
elif menu == "Analisis Tren Bulanan":
    st.subheader("📈 Analisis Kategori Lead Time Berdasarkan Bulan Work Order")
    
    monthly_cat = pd.crosstab(df_data['WO_Month'], df_data['Kategori_LeadTime'])
    
    st.markdown("Tabel Distribusi Kategori per Bulan:")
    st.dataframe(monthly_cat, use_container_width=True)
    
    st.markdown("#### Grafik Perbandingan Kategori per Bulan")
    fig, ax = plt.subplots(figsize=(10, 5))
    monthly_cat.plot(kind='bar', stacked=False, ax=ax, colormap='viridis')
    ax.set_title("Jumlah Kategori Lead Time per Bulan Work Order")
    ax.set_xlabel("Bulan (1-12)")
    ax.set_ylabel("Jumlah Transaksi")
    plt.xticks(rotation=0)
    st.pyplot(fig)

# --- MENU 3: PENCARIAN BERDASARKAN PART ID ---
elif menu == "Cari Berdasarkan Part ID":
    st.subheader("🔍 Pencarian Status Kategori Berdasarkan Part ID")
    
    unique_parts = df_data['Part ID'].dropna().astype(str).unique()
    selected_part = st.selectbox("Pilih atau Ketik Part ID:", sorted(unique_parts))
    
    filtered_df = df_data[df_data['Part ID'].astype(str) == selected_part]
    
    st.markdown(f"Ditemukan **{len(filtered_df)}** transaksi untuk Part ID: **{selected_part}**")
    st.dataframe(filtered_df[['Part ID', 'Description', 'MR Date', 'Tgl Penyerahan', 'Rentang_Hari', 'Kategori_LeadTime']], use_container_width=True)