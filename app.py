import streamlit as st
import cv2
import numpy as np
import joblib
import os
from feature_extraction import extract_all_features

MODEL_PATH = "models/knn_model.pkl"
SCALER_PATH = "models/scaler.pkl"

st.set_page_config(page_title="Klasifikasi Sampah - CV & KNN", layout="wide", page_icon="♻️")

st.title("♻️ Sistem Klasifikasi Sampah Cerdas")
st.markdown("""
Aplikasi pemrosesan citra digital untuk ekstraksi fitur (**Histogram Warna HSV & LAB**, **Bentuk Morfologi**, **Tekstur GLCM & Kerapatan Tepi**) 
serta klasifikasi menggunakan algoritma **K-Nearest Neighbor (KNN)**.
""")

if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
    st.warning("⚠️ Model KNN belum dilatih! Jalankan `python train.py` terlebih dahulu.")
    st.stop()

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

st.sidebar.header("⚙️ Pengaturan")
uploaded_file = st.sidebar.file_uploader("Upload Foto Sampah", type=["jpg", "jpeg", "png", "bmp", "webp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    with st.spinner("Memproses citra dan mengekstrak fitur..."):
        features, img_resized, mask = extract_all_features(img_bgr)
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)

    # 1. Visualisasi Segmentasi
    st.subheader("1. Tahap Pemrosesan Citra & Segmentasi")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image(img_rgb, caption="1. Citra Input (256x256)", use_container_width=True)
    with col2:
        st.image(mask, caption="2. Mask Kontur Objek (Otsu & Adaptive)", use_container_width=True)
    with col3:
        masked_obj = cv2.bitwise_and(img_rgb, img_rgb, mask=mask)
        st.image(masked_obj, caption="3. Objek Tersegmentasi", use_container_width=True)

    # 2. Vektor Fitur
    st.subheader(f"2. Vektor Fitur Hasil Ekstraksi ({len(features)} Dimensi)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**🎨 Fitur Warna (Histogram HSV & LAB)**")
        st.write(f"- LAB Mean: `{features[32]:.1f}, {features[33]:.1f}, {features[34]:.1f}`")
        st.write(f"- LAB Std: `{features[35]:.1f}, {features[36]:.1f}, {features[37]:.1f}`")
        st.caption("Termasuk 32 bin histogram gabungan Hue, Saturation, dan Value.")

    with c2:
        st.markdown("**📐 Fitur Bentuk (Morfologi Kontur)**")
        st.write(f"- Area Rasio: `{features[38]:.3f}`")
        st.write(f"- Keliling Rasio: `{features[39]:.3f}`")
        st.write(f"- Circularity (Kebundaran): `{features[40]:.3f}`")
        st.write(f"- Aspect Ratio: `{features[41]:.2f}`")
        st.write(f"- Solidity: `{features[42]:.2f}`")

    with c3:
        st.markdown("**🧱 Fitur Tekstur & Edge**")
        st.write(f"- GLCM Contrast: `{features[43]:.2f}`")
        st.write(f"- GLCM Homogeneity: `{features[45]:.3f}`")
        st.write(f"- GLCM Energy: `{features[46]:.3f}`")
        st.write(f"- Kerapatan Tepi (Canny Edges): `{features[48]:.3f}`")

    # 3. Prediksi KNN
    st.subheader("3. Hasil Klasifikasi KNN")
    features_scaled = scaler.transform([features])
    prediction = model.predict(features_scaled)[0]
    
    # Format label rapi
    label_map = {
        "botol_plastik": "Botol Plastik 🧴",
        "botol_kaca": "Botol Kaca 🍾",
        "kaleng": "Kaleng / Logam 🥫",
        "kertas": "Kertas 📄",
        "kardus": "Kardus 📦"
    }

    pretty_pred = label_map.get(prediction, prediction.upper())
    st.success(f"### Kategori Terdeteksi: **{pretty_pred}**")

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(features_scaled)[0]
        prob_dict = {label_map.get(cls, cls): float(prob) for cls, prob in zip(model.classes_, probs)}
        st.bar_chart(prob_dict)
else:
    st.info("Silakan upload foto sampah di sidebar sebelah kiri.")
