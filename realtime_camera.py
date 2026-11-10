import cv2
import numpy as np
import joblib
import os
from collections import deque
from feature_extraction import extract_all_features

MODEL_PATH = "models/knn_model.pkl"
SCALER_PATH = "models/scaler.pkl"

if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
    print("Error: Model belum dilatih! Jalankan python train_improved.py terlebih dahulu.")
    exit(1)

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

label_map = {
    "botol_plastik": "Botol Plastik",
    "botol_kaca": "Botol Kaca",
    "kaleng": "Kaleng / Logam",
    "kertas": "Kertas",
    "kardus": "Kardus"
}

def is_object_present(roi):
    """
    Mendeteksi apakah ada objek sampah nyata di dalam kotak ROI
    atau hanya latar belakang kosong / tembok / tangan kosong.
    """
    from feature_extraction import preprocess_image
    _, _, mask = preprocess_image(roi)
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    std_dev = np.std(gray)
    edges = cv2.Canny(gray, 40, 120)
    edge_ratio = np.mean(edges > 0)
    
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area_ratio = 0
    if cnts:
        c = max(cnts, key=cv2.contourArea)
        max_area_ratio = cv2.contourArea(c) / (roi.shape[0] * roi.shape[1])
        
    has_obj = (std_dev >= 15.0) and (edge_ratio >= 0.002) and (0.04 <= max_area_ratio <= 0.96)
    return has_obj, mask, max_area_ratio

def main():
    # Buka webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: Tidak dapat membuka kamera!")
        exit(1)

    print("=" * 60)
    print("  SCANNER REAL-TIME SAMPAH CERDAS (CV & KNN)")
    print("  - Arahkan objek sampah ke dalam kotak tengah")
    print("  - Sistem otomatis menstabilkan dan menyaring prediksi")
    print("  - Tekan 'q' pada jendela kamera untuk keluar")
    print("=" * 60)

    # Buffer untuk smoothing temporal (menyimpan 8 prediksi terakhir)
    WINDOW_SIZE = 8
    prob_history = deque(maxlen=WINDOW_SIZE)

    CONFIDENCE_THRESHOLD = 38.0  # Batas keyakinan minimum (%) agar tidak menebak ngaco
    BOX_SIZE = 280
    frame_count = 0
    last_display_text = "Menunggu objek..."
    last_box_color = (0, 165, 255)  # Oranye (menunggu)
    last_mask_thumb = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape
        x1 = (w - BOX_SIZE) // 2
        y1 = (h - BOX_SIZE) // 2
        x2 = x1 + BOX_SIZE
        y2 = y1 + BOX_SIZE

        roi = frame[y1:y2, x1:x2]
        frame_count += 1

        # Proses ekstraksi dan prediksi tiap 3 frame untuk efisiensi
        if frame_count % 3 == 0:
            has_object, mask, area_r = is_object_present(roi)
            
            # Buat thumbnail mask segmentasi
            mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            last_mask_thumb = cv2.resize(mask_color, (120, 120))

            if not has_object:
                # Jika kotak kosong / tidak ada objek yang jelas
                prob_history.clear()
                last_display_text = "Mencari Objek... Arahkan sampah ke kotak"
                last_box_color = (0, 165, 255)  # Oranye
            else:
                try:
                    features, _, _ = extract_all_features(roi)
                    features_scaled = scaler.transform([features])
                    
                    if hasattr(model, "predict_proba"):
                        probs = model.predict_proba(features_scaled)[0]
                        prob_history.append(probs)
                        
                        # Hitung rata-rata probabilitas dari buffer history
                        avg_probs = np.mean(prob_history, axis=0)
                        best_idx = np.argmax(avg_probs)
                        best_label = model.classes_[best_idx]
                        best_conf = avg_probs[best_idx] * 100
                        
                        if best_conf >= CONFIDENCE_THRESHOLD and len(prob_history) >= 3:
                            pretty_label = label_map.get(best_label, best_label)
                            last_display_text = f"Terdeteksi: {pretty_label} ({best_conf:.0f}%)"
                            last_box_color = (0, 255, 0)  # Hijau (yakin)
                        else:
                            last_display_text = "Menganalisis... Tahan posisi sampah"
                            last_box_color = (255, 200, 0)  # Biru/Kuning (proses)
                    else:
                        pred_class = model.predict(features_scaled)[0]
                        pretty_label = label_map.get(pred_class, pred_class)
                        last_display_text = f"Terdeteksi: {pretty_label}"
                        last_box_color = (0, 255, 0)
                except Exception as e:
                    pass

        # 1. Gambar Kotak Target Scan
        cv2.rectangle(frame, (x1, y1), (x2, y2), last_box_color, 2)
        
        # Sudut aksen (corner brackets) untuk tampilan modern & jelas
        corner_len = 20
        # Top-Left
        cv2.line(frame, (x1, y1), (x1 + corner_len, y1), last_box_color, 4)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_len), last_box_color, 4)
        # Top-Right
        cv2.line(frame, (x2, y1), (x2 - corner_len, y1), last_box_color, 4)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_len), last_box_color, 4)
        # Bottom-Left
        cv2.line(frame, (x1, y2), (x1 + corner_len, y2), last_box_color, 4)
        cv2.line(frame, (x1, y2), (x1, y2 - corner_len), last_box_color, 4)
        # Bottom-Right
        cv2.line(frame, (x2, y2), (x2 - corner_len, y2), last_box_color, 4)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_len), last_box_color, 4)

        # 2. Header Status Bar di Atas Frame
        header_bar = np.zeros((65, w, 3), dtype=np.uint8)
        cv2.putText(header_bar, last_display_text, (20, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, last_box_color, 2)
        
        combined_frame = np.vstack([header_bar, frame])

        # 3. PiP Thumbnail Mask Segmentasi di Pojok Kanan Bawah
        if last_mask_thumb is not None:
            th, tw, _ = last_mask_thumb.shape
            pos_y1 = combined_frame.shape[0] - th - 10
            pos_y2 = pos_y1 + th
            pos_x1 = combined_frame.shape[1] - tw - 10
            pos_x2 = pos_x1 + tw
            
            cv2.rectangle(combined_frame, (pos_x1 - 2, pos_y1 - 18), (pos_x2 + 2, pos_y2 + 2), (50, 50, 50), -1)
            cv2.putText(combined_frame, "Mask Segmentasi", (pos_x1, pos_y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            combined_frame[pos_y1:pos_y2, pos_x1:pos_x2] = last_mask_thumb

        # Keterangan panduan di bagian bawah
        cv2.putText(combined_frame, "Tekan 'q' untuk keluar", (20, combined_frame.shape[0] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        cv2.imshow("Scanner Sampah Cerdas - Real-Time (CV & KNN)", combined_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
