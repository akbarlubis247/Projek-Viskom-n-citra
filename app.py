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

st.sidebar.header("⚙️ Pengaturan Mode")
mode = st.sidebar.radio("Pilih Mode Deteksi:", ["📁 Upload Foto", "🎥 Live Camera Scan (Webcam)"])

if mode == "📁 Upload Foto":
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

elif mode == "🎥 Live Camera Scan (Webcam)":
    st.subheader("🎥 Live Camera Scanner (Real-Time)")
    st.info("💡 **Tips:** Dekatkan benda sampah ke dalam kotak scan di depan kamera (isi 50-80% area kotak). Sistem secara otomatis memisahkan objek dari latar belakang!")

    col_btn, col_box = st.columns([1, 1])
    with col_btn:
        run_cam = st.toggle("Nyalakan Kamera", value=True)
    with col_box:
        box_size_val = st.slider("Ukuran Kotak Scan (ROI):", min_value=220, max_value=400, value=300, step=20)

    # Panel Kalibrasi / Tambah Sampel Baru Langsung dari Kamera
    with st.expander("🛠️ Ambil Foto dari Kamera & Latih Ulang Model Sendiri"):
        st.markdown("""
        **Cara menggunakan:**
        1. Nyalakan kamera dan arahkan barang Anda ke dalam kotak scan.
        2. Pilih kategori barang tersebut di bawah ini.
        3. Klik **📸 Simpan Frame Kamera Ini**.
        4. Klik **⚡ Latih Ulang Model Sekarang** (hanya ~15 detik).
        """)
        
        c_pilih, c_aksi = st.columns([1, 1])
        with c_pilih:
            calib_class = st.selectbox(
                "Pilih Kategori Sampah yang Ditunjukkan:", 
                ["botol_plastik", "botol_kaca", "kaleng", "kardus", "kertas"],
                format_func=lambda x: {
                    "botol_plastik": "Botol Plastik 🧴",
                    "botol_kaca": "Botol Kaca 🍾",
                    "kaleng": "Kaleng / Logam 🥫",
                    "kardus": "Kardus 📦",
                    "kertas": "Kertas 📄"
                }[x]
            )

        with c_aksi:
            st.write("")
            col_save, col_train = st.columns(2)
            with col_save:
                btn_save_frame = st.button("📸 Simpan Frame Ini")
            with col_train:
                btn_retrain = st.button("⚡ Latih Ulang Model")

        if btn_save_frame:
            if "last_captured_roi" in st.session_state and st.session_state["last_captured_roi"] is not None:
                import time
                save_dir = os.path.join("dataset", calib_class)
                os.makedirs(save_dir, exist_ok=True)
                save_filename = f"user_{int(time.time())}.jpg"
                save_path = os.path.join(save_dir, save_filename)
                
                # Simpan gambar ROI dalam format BGR asli
                cv2.imwrite(save_path, st.session_state["last_captured_roi"])
                st.session_state["last_saved_path"] = save_path
                st.success(f"✅ Berhasil menyimpan foto sampel ke: `{save_path}`!")
            else:
                st.warning("⚠️ Kamera belum mendeteksi frame. Pastikan kamera menyala dan mengarah ke objek.")

        if btn_retrain:
            with st.spinner("⏳ Sedang melatih ulang model KNN dengan dataset terbaru (sekitar 15-20 detik)..."):
                import subprocess
                res = subprocess.run(["python", "train.py"], capture_output=True, text=True)
                if res.returncode == 0:
                    st.success("✅ Model KNN berhasil dilatih ulang dan diperbarui!")
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.error(f"Gagal melatih: {res.stderr}")

        # Opsi hapus sampel terakhir jika salah ambil
        if "last_saved_path" in st.session_state and os.path.exists(st.session_state["last_saved_path"]):
            if st.button(f"🗑️ Hapus Sampel Terakhir ({os.path.basename(st.session_state['last_saved_path'])})"):
                os.remove(st.session_state["last_saved_path"])
                del st.session_state["last_saved_path"]
                st.info("Sampel foto berhasil dihapus. Jangan lupa klik 'Latih Ulang' jika ingin menerapkan.")

    col_cam, col_info = st.columns([2, 1])
    with col_cam:
        cam_placeholder = st.empty()
    with col_info:
        status_placeholder = st.empty()
        pred_placeholder = st.empty()
        chart_placeholder = st.empty()

    if run_cam:
        from collections import deque
        from feature_extraction import preprocess_image
        
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        label_map = {
            "botol_plastik": "Botol Plastik 🧴",
            "botol_kaca": "Botol Kaca 🍾",
            "kaleng": "Kaleng / Logam 🥫",
            "kertas": "Kertas 📄",
            "kardus": "Kardus 📦"
        }

        def check_roi_object(roi):
            _, _, mask = preprocess_image(roi)
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            std_dev = np.std(gray)
            edges = cv2.Canny(gray, 40, 120)
            edge_ratio = np.mean(edges > 0)
            
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            area_r = 0
            if cnts:
                c = max(cnts, key=cv2.contourArea)
                area_r = cv2.contourArea(c) / (roi.shape[0] * roi.shape[1])
            has_obj = (std_dev >= 15.0) and (edge_ratio >= 0.002) and (0.04 <= area_r <= 0.96)
            return has_obj, mask

        BOX_SIZE = box_size_val
        frame_counter = 0
        prob_history = deque(maxlen=6)
        CONFIDENCE_THRESHOLD = 35.0

        current_status = "Menunggu objek..."
        current_pred = "-"
        current_probs = None
        box_color = (255, 165, 0)  # RGB: Oranye

        while run_cam:
            ret, frame = cap.read()
            if not ret:
                st.error("Gagal membaca kamera webcam!")
                break

            h, w, _ = frame.shape
            x1 = max(0, (w - BOX_SIZE) // 2)
            y1 = max(0, (h - BOX_SIZE) // 2)
            x2 = min(w, x1 + BOX_SIZE)
            y2 = min(h, y1 + BOX_SIZE)

            roi = frame[y1:y2, x1:x2]
            st.session_state["last_captured_roi"] = roi.copy()

            frame_counter += 1
            if frame_counter % 3 == 0:
                has_obj, mask_seg = check_roi_object(roi)

                if not has_obj:
                    prob_history.clear()
                    current_status = "🔍 Mencari Objek..."
                    current_pred = "Arahkan sampah ke kotak scan"
                    box_color = (255, 165, 0)  # Oranye
                    current_probs = None
                else:
                    try:
                        features, _, _ = extract_all_features(roi)
                        features_scaled = scaler.transform([features])

                        if hasattr(model, "predict_proba"):
                            probs = model.predict_proba(features_scaled)[0]
                            prob_history.append(probs)

                            avg_probs = np.mean(prob_history, axis=0)
                            best_idx = np.argmax(avg_probs)
                            best_label = model.classes_[best_idx]
                            best_conf = avg_probs[best_idx] * 100

                            current_probs = {label_map.get(cls, cls): float(p) for cls, p in zip(model.classes_, avg_probs)}

                            if best_conf >= CONFIDENCE_THRESHOLD and len(prob_history) >= 2:
                                current_status = "✅ Objek Teridentifikasi"
                                current_pred = f"{label_map.get(best_label, best_label)} ({best_conf:.0f}%)"
                                box_color = (0, 255, 0)  # Hijau
                            else:
                                current_status = "⏳ Menganalisis..."
                                current_pred = "Tahan posisi sampah..."
                                box_color = (0, 200, 255)  # Kuning
                        else:
                            pred_raw = model.predict(features_scaled)[0]
                            current_status = "✅ Objek Teridentifikasi"
                            current_pred = label_map.get(pred_raw, pred_raw)
                            box_color = (0, 255, 0)
                    except Exception:
                        pass

            # Gambar Kotak Target Scan di Frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), box_color, 2)
            cv2.putText(frame_rgb, "Area Scan", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

            cam_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

            with status_placeholder.container():
                st.caption(current_status)

            with pred_placeholder.container():
                st.metric(label="Hasil Deteksi", value=current_pred)

            if current_probs:
                with chart_placeholder.container():
                    st.write("**Probabilitas Kategori:**")
                    st.bar_chart(current_probs)

        cap.release()
    else:
        st.write("Kamera dimatikan. Aktifkan saklar di atas untuk mulai scan.")
