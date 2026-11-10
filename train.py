import os
import glob
import joblib
import numpy as np
import cv2
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from feature_extraction import extract_all_features

DATASET_DIR = "dataset"
MODEL_PATH = "models/knn_model.pkl"
SCALER_PATH = "models/scaler.pkl"
MAX_SAMPLES_PER_CLASS = 300

def load_dataset():
    X = []
    y = []
    classes = [d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))]
    print(f"[*] Meload data dari kategori: {classes}")

    user_sample_count = 0

    for label in classes:
        folder = os.path.join(DATASET_DIR, label)
        paths = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            paths.extend(glob.glob(os.path.join(folder, ext)))
        
        # Prioritaskan sampel user webcam terlebih dahulu
        paths.sort(key=lambda p: 0 if "user_" in os.path.basename(p) else 1)
        paths = paths[:MAX_SAMPLES_PER_CLASS]
        print(f" -> Kelas '{label}': {len(paths)} gambar...")

        for idx, p in enumerate(paths):
            try:
                is_user_sample = "user_" in os.path.basename(p)
                img = cv2.imread(p)
                if img is None:
                    continue

                feats, _, _ = extract_all_features(img)

                if is_user_sample:
                    user_sample_count += 1
                    # Beri bobot lebih tinggi pada foto yang diambil langsung dari kamera user
                    for _ in range(5):
                        X.append(feats)
                        y.append(label)
                    # Tambahkan variasi sedikit terang dan redup untuk sampel user
                    b_img = cv2.convertScaleAbs(img, alpha=1.1, beta=15)
                    fb, _, _ = extract_all_features(b_img)
                    X.append(fb)
                    y.append(label)
                else:
                    X.append(feats)
                    y.append(label)
            except Exception as e:
                pass

    print(f"[*] Berhasil memuat {user_sample_count} sampel kustom dari kamera user.")
    return np.array(X, dtype=np.float32), np.array(y), classes

def main():
    os.makedirs("models", exist_ok=True)
    X, y, classes = load_dataset()
    print(f"[*] Total fitur berhasil diekstrak: {len(X)} sampel (Dimensi: {X.shape[1]})")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # KNN k=5 dengan Manhattan distance untuk kestabilan tinggi
    knn = KNeighborsClassifier(n_neighbors=5, weights='distance', metric='manhattan')
    knn.fit(X_scaled, y)

    joblib.dump(knn, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print("[OK] Model KNN baru berhasil dilatih dan disimpan ke models/!")

if __name__ == "__main__":
    main()
