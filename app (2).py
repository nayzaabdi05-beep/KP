import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Prediksi Material Request - PT EJP",
    page_icon="📦",
    layout="wide"
)

# --- JUDUL UTAMA ---
st.title("📦 Dashboard Monitoring & Klasifikasi Waktu Pemenuhan Material Request")
st.markdown("**PT Epsindo Jaya Pratama (EJP) Workshop Duri** | Studi Kasus Algoritma *Random Forest*")
st.markdown("---")

# --- CACHE DATA & MODEL ---
@st.cache_resource
def load_and_train_model():
    file_name = "DES 2025- JULI 2026_EJP.xlsx"
    try:
        df_temp = pd.read_excel(file_name, header=None)
        baris_header = 0
        for i in range(min(15, len(df_temp))):
            baris_isi = df_temp.iloc[i].astype(str).tolist()
            if any('MR Date' in val for val in baris_isi):
                baris_header = i
                break
        df = pd.read_excel(file_name, skiprows=baris_header)
    except Exception as e:
        st.error(f"Gagal memuat file utama ({e}). Pastikan file '{file_name}' sudah di-upload ke direktori Colab.")
        return None, None, None, None, None

    # Cleaning & Preprocessing
    df.columns = df.columns.astype(str).str.strip()
    df_clean = df[df['MR Date'] != 'MR Date'].copy()
    df_clean = df_clean.dropna(subset=['MR Date'])
    
    kolom_ffill = ['Part ID', 'Description', 'Qty', 'Unit', 'WO Date', 'WO No.']
    for kol in kolom_ffill:
        if kol in df_clean.columns:
            df_clean[kol] = df_clean[kol].replace('', np.nan).ffill()
            
    df_clean = df_clean.dropna(subset=['Tgl Penyerahan'])
    df_clean['MR Date'] = pd.to_datetime(df_clean['MR Date'], errors='coerce')
    df_clean['Tgl Penyerahan'] = pd.to_datetime(df_clean['Tgl Penyerahan'], errors='coerce')
    df_clean['WO Date'] = pd.to_datetime(df_clean['WO Date'], errors='coerce')
    df_clean = df_clean.dropna(subset=['MR Date', 'Tgl Penyerahan']).reset_index(drop=True)

    df_clean['Durasi_Hari'] = (df_clean['Tgl Penyerahan'] - df_clean['MR Date']).dt.days
    df_clean = df_clean[(df_clean['Durasi_Hari'] >= 0) & (df_clean['Durasi_Hari'] <= 30)].copy()

    def tentukan_kategori(hari):
        if hari <= 1: return 'Cepat'
        elif hari <= 3: return 'Standar'
        else: return 'Lambat'

    df_clean['Kategori'] = df_clean['Durasi_Hari'].apply(tentukan_kategori)

    def ekstrak_material(desc):
        desc = str(desc).upper()
        if 'PUMP' in desc: return 'PUMP'
        if 'MOTOR' in desc: return 'MOTOR'
        if 'CABLE' in desc: return 'CABLE'
        if 'PROTECTOR' in desc: return 'PROTECTOR'
        if 'INTAKE' in desc or 'INI' in desc: return 'INTAKE'
        if 'AGH' in desc: return 'AGH'
        if 'FCE' in desc: return 'FCE'
        return 'OTHER'

    df_clean['Jenis_Material'] = df_clean['Description'].apply(ekstrak_material)
    df_clean['Qty'] = pd.to_numeric(df_clean['Qty'], errors='coerce').fillna(1)
    df_clean['Unit'] = df_clean['Unit'].astype(str).str.strip().str.upper()
    df_clean['Gap_WO_MR'] = (df_clean['MR Date'] - df_clean['WO Date']).dt.days.fillna(0).clip(lower=0)
    df_clean['MR_DayOfWeek'] = df_clean['MR Date'].dt.dayofweek
    df_clean['MR_Month'] = df_clean['MR Date'].dt.month

    # Modeling
    fitur_input = ['Jenis_Material', 'Unit', 'Qty', 'Gap_WO_MR', 'MR_DayOfWeek', 'MR_Month']
    X = df_clean[fitur_input]
    y = df_clean['Kategori']
    
    X_encoded = pd.get_dummies(X, columns=['Jenis_Material', 'Unit'], drop_first=True)
    X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, max_depth=6, min_samples_leaf=2, class_weight='balanced', random_state=42)
    model.fit(X_train, y_train)

    return df_clean, model, X_encoded.columns, X_test, y_test

df_data, model_rf, model_columns, X_test, y_test = load_and_train_model()

if df_data is not None:
    # --- SIDEBAR NAVIGASI ---
    menu = st.sidebar.selectbox("Pilih Menu Dasbor", ["📊 Ringkasan Data & EDA", "🤖 Simulasi Prediksi Model", "📈 Evaluasi Kinerja Model"])

    # =========================================================================
    # MENU 1: RINGKASAN DATA & EDA
    # =========================================================================
    if menu == "📊 Ringkasan Data & EDA":
        st.subheader("📊 Statistik Ringkasan Operasional Logistik")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Transaksi Valid", f"{len(df_data):,} Baris")
        col2.metric("Kategori Cepat (<=1 Hari)", f"{(df_data['Kategori']=='Cepat').sum():,} Transaksi")
        col3.metric("Kategori Standar (1-3 Hari)", f"{(df_data['Kategori']=='Standar').sum():,} Transaksi")
        col4.metric("Kategori Lambat (>3 Hari)", f"{(df_data['Kategori']=='Lambat').sum():,} Transaksi")
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Distribusi Frekuensi Kelas Target")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.countplot(data=df_data, x='Kategori', order=['Cepat', 'Standar', 'Lambat'], palette='Blues_r', ax=ax)
            ax.set_ylabel("Jumlah Transaksi")
            ax.set_xlabel("Kategori Pemenuhan")
            st.pyplot(fig)
            
        with c2:
            st.markdown("#### Sebaran Durasi per Kelompok Material")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.countplot(data=df_data, x='Jenis_Material', hue='Kategori', palette='Set2', ax=ax)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
            ax.set_ylabel("Jumlah Transaksi")
            ax.set_xlabel("Kelompok Material")
            st.pyplot(fig)

    # =========================================================================
    # MENU 2: SIMULASI PREDIKSI MODEL
    # =========================================================================
    elif menu == "🤖 Simulasi Prediksi Model":
        st.subheader("🤖 Form Estimasi Kategori Waktu Pemenuhan Material")
        st.markdown("Masukkan parameter pengajuan dokumen *Material Request* (MR) di bawah ini untuk menguji prediksi kecepatan penyerahan barang:")

        with st.form("form_prediksi"):
            col1, col2 = st.columns(2)
            
            with col1:
                jns_material = st.selectbox("Kelompok Jenis Material", ['PUMP', 'MOTOR', 'CABLE', 'PROTECTOR', 'INTAKE', 'AGH', 'FCE', 'OTHER'])
                satuan = st.selectbox("Satuan Unit (Unit)", ['UNIT', 'REEL', 'EA', 'SET'])
                kuantitas = st.number_input("Kuantitas Permintaan (Qty)", min_value=1, max_value=100, value=1)
                
            with col2:
                gap_wo = st.slider("Tenggat Persiapan Dokumen (Gap WO-MR dalam Hari)", min_value=0, max_value=30, value=1)
                hari_mr = st.selectbox("Hari Pengajuan MR", ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'])
                bulan_mr = st.slider("Bulan Transaksi (MR Month)", min_value=1, max_value=12, value=6)

            submit_btn = st.form_submit_button("🔍 Prediksi Kategori Waktu Pemenuhan")

        if submit_btn:
            mapping_hari = {'Senin':0, 'Selasa':1, 'Rabu':2, 'Kamis':3, 'Jumat':4, 'Sabtu':5, 'Minggu':6}
            
            input_data = pd.DataFrame({
                'Jenis_Material': [jns_material],
                'Unit': [satuan],
                'Qty': [kuantitas],
                'Gap_WO_MR': [gap_wo],
                'MR_DayOfWeek': [mapping_hari[hari_mr]],
                'MR_Month': [bulan_mr]
            })
            
            input_encoded = pd.get_dummies(input_data, columns=['Jenis_Material', 'Unit'], drop_first=True)
            input_encoded = input_encoded.reindex(columns=model_columns, fill_value=0)
            
            prediksi = model_rf.predict(input_encoded)[0]
            probabilitas = model_rf.predict_proba(input_encoded)[0]
            
            st.markdown("---")
            st.markdown("### Hasil Analisis Sistem Penunjang Keputusan:")
            
            if prediksi == 'Cepat':
                st.success(f"🟢 **Prediksi Kategori: CEPAT (<= 1 Hari)**")
            elif prediksi == 'Standar':
                st.warning(f"🟡 **Prediksi Kategori: STANDAR (1 - 3 Hari)**")
            else:
                st.error(f"🔴 **Prediksi Kategori: LAMBAT (> 3 Hari)**")
                
            st.markdown(f"**Tingkat Keyakinan Model (Probabilitas):**")
            st.write(f"- Cepat: `{probabilitas[0]*100:.2f}%`")
            st.write(f"- Standar: `{probabilitas[1]*100:.2f}%`")
            st.write(f"- Lambat: `{probabilitas[2]*100:.2f}%`")

    # =========================================================================
    # MENU 3: EVALUASI KINERJA MODEL
    # =========================================================================
    elif menu == "📈 Evaluasi Kinerja Model":
        st.subheader("📈 Metrik Evaluasi Kinerja Random Forest")
        
        y_pred = model_rf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        
        col1, col2 = st.columns(2)
        col1.metric("Akurasi Pengujian (Testing Accuracy)", f"{acc * 100:.2f}%")
        col2.metric("Jumlah Sampel Data Uji", f"{len(y_test)} Transaksi")
        
        st.markdown("---")
        st.markdown("#### Confusion Matrix Pengujian Model")
        
        label_urutan = ['Cepat', 'Standar', 'Lambat']
        cm = confusion_matrix(y_test, y_pred, labels=label_urutan)
        
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=label_urutan, yticklabels=label_urutan, ax=ax)
        ax.set_xlabel('Prediksi Model')
        ax.set_ylabel('Aktual Sebenarnya')
        st.pyplot(fig)
        
        st.markdown("#### Classification Report Detail")
        report_dict = classification_report(y_test, y_pred, output_dict=True)
        df_report = pd.DataFrame(report_dict).transpose()
        st.dataframe(df_report.style.format(subset=['precision', 'recall', 'f1-score', 'support'], formatter="{:.2f}"))
