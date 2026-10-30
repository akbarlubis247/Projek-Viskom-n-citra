import os
import glob
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, accuracy_score
from feature_extraction import extract_all_features

DATASET_DIR = "dataset"
MODEL_PATH = "models/knn_model.pkl"
SCALER_PATH = "models/scaler.pkl"
MAX_SAMPLES_PER_CLASS = 150

def load_dataset():
    X = []
    y = []
    classes = [d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))]
    print(f"[*] Meload data dari kategori: {classes}")

    for label in classes:
        folder = os.path.join(DATASET_DIR, label)
        paths = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            paths.extend(glob.glob(os.path.join(folder, ext)))
        
        # Prioritaskan sampel user terlebih dahulu
        paths.sort(key=lambda p: 0 if "user_" in os.path.basename(p) else 1)
        paths = paths[:MAX_SAMPLES_PER_CLASS]
        print(f" -> Kelas '{label}': {len(paths)} gambar...")

        for idx, p in enumerate(paths):
            try:
                feats, _, _ = extract_all_features(p)
                # Beri bobot lebih tinggi pada user sample dengan duplikasi kecil
                if "user_" in os.path.basename(p):
                    for _ in range(5):
                        X.append(feats)
                        y.append(label)
                else:
                    X.append(feats)
                    y.append(label)
            except Exception as e:
                pass

    return np.array(X), np.array(y), classes

def main():
    os.makedirs("models", exist_ok=True)
    X, y, classes = load_dataset()
    print(f"[*] Total fitur berhasil diekstrak: {len(X)} sampel (Dimensi: {X.shape[1]})")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # KNN dengan k=3 dan bobot distance
    knn = KNeighborsClassifier(n_neighbors=3, weights='distance', metric='manhattan')
    knn.fit(X_scaled, y)

    joblib.dump(knn, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print("[OK] Model KNN baru berhasil dilatih dan disimpan!")

if __name__ == "__main__":
    main()
