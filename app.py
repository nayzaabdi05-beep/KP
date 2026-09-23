import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix
)

from imblearn.over_sampling import SMOTENC

# ==========================================
# 1. KONFIGURASI HALAMAN & TAMPILAN DARK THEME
# ==========================================
st.set_page_config(
    page_title="Dashboard Prediksi Lead Time EJP",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS untuk mempercantik Dark Mode & komponen Streamlit
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stMetric {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stMetric label {
        color: #9ca3af !important;
    }
    .stMetric .st-emotion-cache-1wivap2 {
        color: #f3f4f6 !important;
    }
    h1, h2, h3 {
        color: #f9fafb;
    }
    .sidebar .st-emotion-cache-1cypcdb {
        background-color: #111827;
    }
    </style>
""", unsafe_allow_html=True)

# Set Seaborn theme untuk mendukung tampilan gelap
plt.style.use("dark_background")

# ==========================================
# 2. CACHED DATA LOADING & PREPROCESSING
# ==========================================
@st.cache_data
def load_and_process_data(file_path):
    df = pd.read_excel(file_path, sheet_name=0, header=1)

    # Konversi tanggal
    df["WO Date"] = pd.to_datetime(df["WO Date"], errors="coerce")
    df["MR Date"] = pd.to_datetime(df["MR Date"], errors="coerce")
    df["Tgl Penyerahan"] = pd.to_datetime(df["Tgl Penyerahan"], errors="coerce")

    # Ambil periode Desember 2025 - Juni 2026
    df = df[
        (df["MR Date"] >= "2025-12-01") &
        (df["MR Date"] < "2026-07-01")
    ].copy()

    # Hapus data yang tidak memiliki informasi utama
    df = df.dropna(subset=["Part ID", "MR Date", "Tgl Penyerahan"])
    df = df.drop_duplicates()

    # Konversi Qty
    df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce")
    df = df.dropna(subset=["Qty"])

    # Hitung lead time
    df["Rentang_Hari"] = (df["Tgl Penyerahan"] - df["MR Date"]).dt.days
    df = df[df["Rentang_Hari"] >= 0].reset_index(drop=True)

    # Fitur Waktu Tambahan
    df["WO_MR_Days"] = (df["MR Date"] - df["WO Date"]).dt.days
    df["MR_Month"] = df["MR Date"].dt.month
    df["MR_DayOfWeek"] = df["MR Date"].dt.dayofweek
    df["Bulan_MR"] = df["MR Date"].dt.to_period("M").astype(str)

    # Pelabelan Lead Time
    def kategori_lead_time(hari):
        if hari <= 1:
            return "Cepat"
        elif hari <= 3:
            return "Standar"
        else:
            return "Lambat"

    df["Kategori_LeadTime"] = df["Rentang_Hari"].apply(kategori_lead_time)
    return df

# ==========================================
# 3. SIDEBAR & NAVIGASI
# ==========================================
st.sidebar.title("🎛️ Panel Kontrol")
st.sidebar.markdown("---")

file_path = "DES 2025- JULI 2026_EJP.xlsx"

try:
    df = load_and_process_data(file_path)
except Exception as e:
    st.error(f"Gagal memuat file dataset `{file_path}`. Pastikan file berada di folder yang sama. Error: {e}")
    st.stop()

menu = st.sidebar.selectbox(
    "Pilih Menu Dashboard:",
    (
        "1. Overview & Data Cleaning",
        "2. Exploratory Data Analysis (EDA)",
        "3. Pelabelan Lead Time",
        "4. Model Training & SMOTENC",
        "5. Evaluasi & Overfitting Check",
        "6. Prediksi Real-Time Mandiri"
    )
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Algoritma Utama:** RandomForestClassifier dengan penyeimbangan data SMOTENC.")

# ==========================================
# 4. KONTEN HALAMAN UTAMA BERDASARKAN MENU
# ==========================================

if menu == "1. Overview & Data Cleaning":
    st.title("📂 1. Import, Input & Data Cleaning")
    st.markdown("Bagian ini menampilkan ringkasan data setelah melewati tahap pembersihan (handling missing value, konversi tanggal, filter periode Des 2025 - Jun 2026, dan validasi Qty).")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Data Bersih", len(df))
    col2.metric("Jumlah Fitur Utama", len(df.columns))
    col3.metric("Rentang Periode", "Des 2025 - Jun 2026")

    st.subheader("👀 Sampel Data Setelah Cleaning")
    st.dataframe(df.head(10), use_container_width=True)

    with st.expander("🔍 Cek Outlier pada Kolom Rentang Hari (Lead Time)"):
        Q1 = df["Rentang_Hari"].quantile(0.25)
        Q3 = df["Rentang_Hari"].quantile(0.75)
        IQR = Q3 - Q1
        batas_bawah = Q1 - (1.5 * IQR)
        batas_atas = Q3 + (1.5 * IQR)
        outlier = df[(df["Rentang_Hari"] < batas_bawah) | (df["Rentang_Hari"] > batas_atas)]

        st.write(f"- **Q1 (25%)**: {Q1}")
        st.write(f"- **Q3 (75%)**: {Q3}")
        st.write(f"- **Batas Bawah**: {batas_bawah}")
        st.write(f"- **Batas Atas**: {batas_atas}")
        st.write(f"- **Jumlah Outlier terdeteksi**: {len(outlier)} baris")
        st.caption("Catatan: Outlier tidak dihapus secara otomatis karena nilai lead time yang panjang merepresentasikan kategori 'Lambat' yang ingin diklasifikasikan.")

elif menu == "2. Exploratory Data Analysis (EDA)":
    st.title("📈 2. Exploratory Data Analysis (EDA)")
    st.markdown("Analisis distribusi lama waktu pemenuhan material serta tren transaksi per bulan.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribusi Lead Time Pemenuhan Material")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(df["Rentang_Hari"], bins=30, kde=True, ax=ax, color="#3b82f6")
        ax.set_title("Distribusi Lead Time", color="white")
        ax.set_xlabel("Rentang Hari", color="white")
        ax.set_ylabel("Frekuensi", color="white")
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1f2937')
        st.pyplot(fig)

    with col2:
        st.subheader("Jumlah Transaksi Berdasarkan Bulan MR")
        bulanan = df.groupby("Bulan_MR").size().reset_index(name="Jumlah")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=bulanan, x="Bulan_MR", y="Jumlah", ax=ax, palette="mako")
        ax.set_title("Transaksi per Bulan", color="white")
        ax.set_xlabel("Bulan MR", color="white")
        ax.set_ylabel("Jumlah Transaksi", color="white")
        plt.xticks(rotation=45)
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1f2937')
        st.pyplot(fig)

elif menu == "3. Pelabelan Lead Time":
    st.title("🏷️ 3. Pelabelan Kategori Lead Time")
    st.markdown("""
    Aturan Pelabelan target berdasarkan `Rentang_Hari`:
    - **Cepat**: $\\le 1$ Hari
    - **Standar**: $2 - 3$ Hari
    - **Lambat**: $> 3$ Hari
    """)

    urutan = ["Cepat", "Standar", "Lambat"]
    kategori = df["Kategori_LeadTime"].value_counts().reindex(urutan)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Jumlah per Kategori")
        st.dataframe(kategori, use_container_width=True)

    with col2:
        st.subheader("Visualisasi Distribusi Kategori")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x=kategori.index, y=kategori.values, ax=ax, palette=["#10b981", "#f59e0b", "#ef4444"])
        ax.set_title("Distribusi Kategori Lead Time", color="white")
        ax.set_xlabel("Kategori", color="white")
        ax.set_ylabel("Jumlah Transaksi", color="white")
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1f2937')
        st.pyplot(fig)

elif menu == "4. Model Training & SMOTENC":
    st.title("⚙️ 4. Train-Test Split & SMOTENC Pipeline")
    st.markdown("Melakukan pembagian data latih dan uji (80:20 dengan stratifikasi) serta penanganan ketidakseimbangan kelas menggunakan **SMOTENC** khusus fitur campuran (kategorikal & numerik).")

    # Persiapan Data
    features = ["Part ID", "Unit", "WO_MR_Days", "MR_Month", "MR_DayOfWeek"]
    X = df[features]
    y = df["Kategori_LeadTime"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    categorical_features = ["Part ID", "Unit"]
    numeric_features = ["WO_MR_Days", "MR_Month", "MR_DayOfWeek"]

    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X_train_cat = encoder.fit_transform(X_train[categorical_features])
    X_test_cat = encoder.transform(X_test[categorical_features])

    imputer = SimpleImputer(strategy="median")
    X_train_num = imputer.fit_transform(X_train[numeric_features])
    X_test_num = imputer.transform(X_test[numeric_features])

    X_train_encoded = np.column_stack([X_train_cat, X_train_num])
    X_test_encoded = np.column_stack([X_test_cat, X_test_num])

    smote = SMOTENC(categorical_features=[0, 1], random_state=42, k_neighbors=5)
    X_train_smote, y_train_smote = smote.fit_resample(X_train_encoded, y_train)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribusi Sebelum SMOTENC (Train)")
        st.write(y_train.value_counts())
    with col2:
        st.subheader("Distribusi Sesudah SMOTENC (Train)")
        st.write(pd.Series(y_train_smote).value_counts())

    st.subheader("📊 Perbandingan Grafik Sebelum & Sesudah SMOTENC")
    before = pd.Series(y_train).value_counts()
    after = pd.Series(y_train_smote).value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(before.index, before.values, color="#3b82f6")
    axes[0].set_title("Sebelum SMOTENC", color="white")
    axes[0].set_xlabel("Kategori", color="white")
    axes[0].set_ylabel("Jumlah", color="white")
    axes[0].set_facecolor('#1f2937')

    axes[1].bar(after.index, after.values, color="#ec4899")
    axes[1].set_title("Sesudah SMOTENC", color="white")
    axes[1].set_xlabel("Kategori", color="white")
    axes[1].set_ylabel("Jumlah", color="white")
    axes[1].set_facecolor('#1f2937')

    fig.patch.set_facecolor('#0e1117')
    st.pyplot(fig)

elif menu == "5. Evaluasi & Overfitting Check":
    st.title("🏆 5. Evaluasi Random Forest & Cek Overfitting")

    # Proses Training & Prediksi secara otomatis untuk keperluan evaluasi
    @st.cache_resource
    def run_training_pipeline():
        features = ["Part ID", "Unit", "WO_MR_Days", "MR_Month", "MR_DayOfWeek"]
        X = df[features]
        y = df["Kategori_LeadTime"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

        categorical_features = ["Part ID", "Unit"]
        numeric_features = ["WO_MR_Days", "MR_Month", "MR_DayOfWeek"]

        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        X_train_cat = encoder.fit_transform(X_train[categorical_features])
        X_test_cat = encoder.transform(X_test[categorical_features])

        imputer = SimpleImputer(strategy="median")
        X_train_num = imputer.fit_transform(X_train[numeric_features])
        X_test_num = imputer.transform(X_test[numeric_features])

        X_train_encoded = np.column_stack([X_train_cat, X_train_num])
        X_test_encoded = np.column_stack([X_test_cat, X_test_num])

        smote = SMOTENC(categorical_features=[0, 1], random_state=42, k_neighbors=5)
        X_train_smote, y_train_smote = smote.fit_resample(X_train_encoded, y_train)

        rf = RandomForestClassifier(n_estimators=500, random_state=42, n_jobs=-1)
        rf.fit(X_train_smote, y_train_smote)

        y_pred = rf.predict(X_test_encoded)
        y_train_pred = rf.predict(X_train_smote)

        return rf, y_test, y_pred, y_train_smote, y_train_pred, X_test_encoded

    rf_classifier, y_test, y_pred, y_train_smote, y_train_pred, X_test_encoded = run_training_pipeline()

    # Metrik Evaluasi
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    bal_acc = balanced_accuracy_score(y_test, y_pred)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Akurasi", f"{acc:.2%}")
    c2.metric("Precision", f"{prec:.2%}")
    c3.metric("Recall", f"{rec:.2%}")
    c4.metric("F1-Score", f"{f1:.2%}")
    c5.metric("Balanced Acc", f"{bal_acc:.2%}")

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🔍 Analisis Overfitting")
        train_acc = accuracy_score(y_train_smote, y_train_pred)
        test_acc = accuracy_score(y_test, y_pred)
        selisih = train_acc - test_acc

        st.write(f"- **Training Accuracy**: `{train_acc:.2%}`")
        st.write(f"- **Testing Accuracy**: `{test_acc:.2%}`")
        st.write(f"- **Selisih Gap**: `{selisih:.2%}`")
        st.info("💡 **Analisis**: Terdapat gap performa antara data training dan testing yang mengindikasikan sedikit overfitting (hal ini wajar pada model Random Forest dengan SMOTE, dan perlu didiskusikan dalam laporan penelitian).")

    with col_right:
        st.subheader("📉 Confusion Matrix")
        labels = ["Cepat", "Standar", "Lambat"]
        cm = confusion_matrix(y_test, y_pred, labels=labels)

        fig, ax = plt.subplots(figsize=(6, 4.5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels, ax=ax)
        ax.set_title("Confusion Matrix", color="white")
        ax.set_xlabel("Prediksi", color="white")
        ax.set_ylabel("Aktual", color="white")
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1f2937')
        st.pyplot(fig)

    st.subheader("📋 Classification Report")
    report_dict = classification_report(y_test, y_pred, labels=["Cepat", "Standar", "Lambat"], zero_division=0, output_dict=True)
    st.dataframe(pd.DataFrame(report_dict).transpose(), use_container_width=True)

elif menu == "6. Prediksi Real-Time Mandiri":
    st.title("🔮 6. Form Prediksi Lead Time Transaksi Baru")
    st.markdown("Masukkan parameter transaksi material di bawah ini untuk memprediksi kategori lead time secara langsung menggunakan model terlatih.")

    @st.cache_resource
    def get_trained_model_and_tools():
        features = ["Part ID", "Unit", "WO_MR_Days", "MR_Month", "MR_DayOfWeek"]
        X = df[features]
        y = df["Kategori_LeadTime"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
        categorical_features = ["Part ID", "Unit"]
        numeric_features = ["WO_MR_Days", "MR_Month", "MR_DayOfWeek"]

        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        encoder.fit(X_train[categorical_features])

        imputer = SimpleImputer(strategy="median")
        imputer.fit(X_train[numeric_features])

        X_train_cat = encoder.transform(X_train[categorical_features])
        X_train_num = imputer.transform(X_train[numeric_features])
        X_train_encoded = np.column_stack([X_train_cat, X_train_num])

        smote = SMOTENC(categorical_features=[0, 1], random_state=42, k_neighbors=5)
        X_train_smote, y_train_smote = smote.fit_resample(X_train_encoded, y_train)

        rf = RandomForestClassifier(n_estimators=500, random_state=42, n_jobs=-1)
        rf.fit(X_train_smote, y_train_smote)

        return rf, encoder, imputer

    rf, encoder, imputer = get_trained_model_and_tools()

    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        with col1:
            part_id_input = st.selectbox("Part ID", options=sorted(df["Part ID"].unique()))
            unit_input = st.selectbox("Unit", options=sorted(df["Unit"].dropna().unique()))
            wo_mr_days_input = st.number_input("WO to MR Days (Selisih Hari WO & MR)", min_value=0, max_value=365, value=2)
        with col2:
            mr_month_input = st.slider("Bulan MR (MR Month)", min_value=1, max_value=12, value=5)
            mr_dow_input = st.selectbox("Hari dalam Minggu (MR Day of Week)", options=[0, 1, 2, 3, 4, 5, 6], format_func=lambda x: ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][x])

        submit_btn = st.form_submit_button("🚀 Jalankan Prediksi")

        if submit_btn:
            input_cat = encoder.transform([[part_id_input, unit_input]])
            input_num = imputer.transform([[wo_mr_days_input, mr_month_input, mr_dow_input]])
            input_encoded = np.column_stack([input_cat, input_num])

            prediction = rf.predict(input_encoded)[0]
            probabilities = rf.predict_proba(input_encoded)[0]

            st.markdown("---")
            st.subheader("✨ Hasil Prediksi Model:")
            
            if prediction == "Cepat":
                st.success(f"### Kategori Prediksi: **{prediction}** 🟢")
            elif prediction == "Standar":
                st.warning(f"### Kategori Prediksi: **{prediction}** 🟡")
            else:
                st.error(f"### Kategori Prediksi: **{prediction}** 🔴")

            st.write("Probabilitas Tiap Kelas:")
            prob_df = pd.DataFrame({
                "Kategori": rf.classes_,
                "Probabilitas": [f"{p*100:.2f}%" for p in probabilities]
            })
            st.dataframe(prob_df, use_container_width=True)