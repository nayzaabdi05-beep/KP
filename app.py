import streamlit as st
import pandas as pd
import datetime

# 1. Judul Dashboard
st.title("📦 Dashboard Analisis Waktu Pemenuhan MR")
st.subheader("PT Epsindo Jaya Pratama Workshop Duri")
st.markdown("---")

# 2. Load dan Bersihkan Data
@st.cache_data
def load_data():
    file_path = 'DES 2025- JUNI 2026_EJP.xlsx'
    df = pd.read_excel(file_path)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    
    # Ambil kolom yang diperlukan
    df_clean = df[['Part ID', 'Description', 'Qty', 'Unit', 'MR Date', 'Tgl Penyerahan']].dropna()
    
    # Konversi format tanggal
    df_clean['MR Date'] = pd.to_datetime(df_clean['MR Date'], errors='coerce')
    df_clean['Tgl Penyerahan'] = pd.to_datetime(df_clean['Tgl Penyerahan'], errors='coerce')
    df_clean = df_clean.dropna(subset=['MR Date', 'Tgl Penyerahan'])
    
    # Hitung selisih hari (Lead Time)
    df_clean['Rentang_Hari'] = (df_clean['Tgl Penyerahan'] - df_clean['MR Date']).dt.days
    
    # Tentukan Kategori
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

# 3. Sidebar Filter (Interaktif)
st.sidebar.header("🔍 Filter Data")
selected_kategori = st.sidebar.multiselect(
    "Pilih Kategori Waktu:", 
    options=['Cepat', 'Standar', 'Lambat'], 
    default=['Cepat', 'Standar', 'Lambat']
)

# Filter data berdasarkan sidebar
filtered_df = df_clean[df_clean['Kategori'].isin(selected_kategori)]

# 4. Ringkasan Angka (Metrics)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Transaksi", len(filtered_df))
with col2:
    avg_hari = filtered_df['Rentang_Hari'].mean() if len(filtered_df) > 0 else 0
    st.metric("Rata-rata Rentang Hari", f"{avg_hari:.2f} Hari")
with col3:
    max_hari = filtered_df['Rentang_Hari'].max() if len(filtered_df) > 0 else 0
    st.metric("Rentang Hari Terlama", f"{max_hari} Hari")

st.markdown("---")

# 5. Grafik Sederhana (Bagan Batang Jumlah Kategori)
st.markdown("### 📊 Grafik Jumlah Transaksi per Kategori")
kategori_counts = filtered_df['Kategori'].value_counts().reindex(['Cepat', 'Standar', 'Lambat']).fillna(0)
st.bar_chart(kategori_counts)

# 6. Tabel Data Detail
st.markdown("### 📋 Tabel Detail Transaksi")
st.dataframe(
    filtered_df[['Part ID', 'Description', 'Qty', 'Unit', 'MR Date', 'Tgl Penyerahan', 'Rentang_Hari', 'Kategori']], 
    use_container_width=True
)
