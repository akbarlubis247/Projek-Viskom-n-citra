import glob
import os
import time
import cv2
import joblib
import numpy as np
from joblib import Parallel, delayed
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from feature_extraction import (
    HybridMetricScaler,
    extract_classical_features,
    extract_semantic_batch,
    preprocess_image,
)

DATASET_DIR = "dataset"
MODEL_PATH = "models/knn_model.pkl"
SCALER_PATH = "models/scaler.pkl"


def _extract_classical_from_path(path):
    img = cv2.imread(path)
    if img is None:
        return None
    img_resized, gray, mask = preprocess_image(img)
    return extract_classical_features(img_resized, gray, mask)


def load_full_dataset():
    paths = []
    labels = []
    is_user = []
    classes = sorted(
        d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))
    )
    print(f"[*] Meload SELURUH dataset dari kategori: {classes}")

    for label in classes:
        folder = os.path.join(DATASET_DIR, label)
        cls_paths = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            cls_paths.extend(glob.glob(os.path.join(folder, ext)))
        cls_paths.sort()
        print(f" -> Kelas '{label}': {len(cls_paths)} gambar")
        for p in cls_paths:
            paths.append(p)
            labels.append(label)
            is_user.append("user_" in os.path.basename(p))

    t0 = time.time()
    print(f"[*] Mengekstrak 49 fitur klasik secara paralel ({len(paths)} gambar)...")
    c49_list = Parallel(n_jobs=-1)(delayed(_extract_classical_from_path)(p) for p in paths)

    valid_imgs = []
    valid_c49 = []
    valid_labels = []
    valid_is_user = []
    for p, c49, lbl, uflag in zip(paths, c49_list, labels, is_user):
        if c49 is not None:
            im = cv2.imread(p)
            if im is not None:
                valid_imgs.append(im)
                valid_c49.append(c49)
                valid_labels.append(lbl)
                valid_is_user.append(uflag)

    print(f"[*] Mengekstrak 1.152 fitur visual semantik DINOv2-Small ({len(valid_imgs)} gambar)...")
    X_sem = extract_semantic_batch(valid_imgs, use_flip_avg=True, batch_size=32)
    X_c49 = np.vstack(valid_c49).astype(np.float32)
    X = np.hstack([X_c49, X_sem]).astype(np.float32)
    y = np.array(valid_labels)
    u_mask = np.array(valid_is_user, dtype=bool)
    print(f"[*] Ekstraksi selesai dalam {time.time() - t0:.1f} detik | Bentuk matriks fitur: {X.shape}")
    return X, y, u_mask, classes


def main():
    os.makedirs("models", exist_ok=True)
    X, y, u_mask, classes = load_full_dataset()

    # 1. Validasi Silang Jujur (5-Fold Stratified CV pada seluruh sampel dataset non-user)
    X_eval = X[~u_mask]
    y_eval = y[~u_mask]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof_preds = np.empty_like(y_eval)
    for tr_idx, va_idx in skf.split(X_eval, y_eval):
        fold_scaler = HybridMetricScaler(
            n_classical=49, classical_weight=0.20, lda_shrinkage=0.20, lda_weight=1.10
        )
        X_tr = fold_scaler.fit_transform(X_eval[tr_idx], y_eval[tr_idx])
        X_va = fold_scaler.transform(X_eval[va_idx])
        fold_knn = KNeighborsClassifier(n_neighbors=7, weights="distance", metric="cosine")
        fold_knn.fit(X_tr, y_eval[tr_idx])
        oof_preds[va_idx] = fold_knn.predict(X_va)

    cv_acc = accuracy_score(y_eval, oof_preds) * 100.0
    print(f"\n[EVALUASI 5-FOLD CV] Akurasi KNN pada {len(y_eval)} citra: {cv_acc:.2f}%")
    print(classification_report(y_eval, oof_preds))

    # 2. Latih Model Final pada SELURUH 2.395 citra
    scaler = HybridMetricScaler(
        n_classical=49, classical_weight=0.20, lda_shrinkage=0.20, lda_weight=1.10
    )
    X_scaled = scaler.fit_transform(X, y)

    knn = KNeighborsClassifier(n_neighbors=7, weights="distance", metric="cosine")
    knn.fit(X_scaled, y)

    joblib.dump(knn, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"[OK] Model KNN akurasi tinggi (CV {cv_acc:.2f}%) berhasil disimpan ke {MODEL_PATH}!")


if __name__ == "__main__":
    main()
