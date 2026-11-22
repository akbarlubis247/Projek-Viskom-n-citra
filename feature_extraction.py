import os
import urllib.request
import cv2
import numpy as np
import onnxruntime as ort
from skimage.feature import graycomatrix, graycoprops
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.preprocessing import StandardScaler, normalize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DINO_ONNX_PATH = os.path.join(BASE_DIR, "models", "dinov2_small_quantized.onnx")
DINO_ONNX_URL = (
    "https://huggingface.co/onnx-community/dinov2-with-registers-small/"
    "resolve/main/onnx/model_quantized.onnx"
)

_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 3, 1, 1)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 3, 1, 1)
_DINO_SESSION = None


def _get_dino_session():
    """Memuat sesi ONNX Runtime DINOv2-Small secara lazy (singleton)."""
    global _DINO_SESSION
    if _DINO_SESSION is None:
        if not os.path.exists(DINO_ONNX_PATH):
            os.makedirs(os.path.dirname(DINO_ONNX_PATH), exist_ok=True)
            req = urllib.request.Request(DINO_ONNX_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp, open(DINO_ONNX_PATH, "wb") as out_f:
                out_f.write(resp.read())
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _DINO_SESSION = ort.InferenceSession(
            DINO_ONNX_PATH, sess_options=opts, providers=["CPUExecutionProvider"]
        )
    return _DINO_SESSION


class HybridMetricScaler(BaseEstimator, TransformerMixin):
    """
    Transformasi ruang fitur terpadu untuk K-Nearest Neighbor (KNN):
    1. Menstandarisasi 49 fitur klasik (HSV, CIE-LAB, Morfologi Bentuk, GLCM & Canny).
    2. Menggabungkan fitur visual semantik DINOv2 (1.152-D) dengan fitur klasik berbobot.
    3. Memproyeksikan komponen diskriminan terregularisasi (Residual LDA shrinkage) agar
       jarak Cosine pada KNN memisahkan 5 kategori sampah secara maksimal sekaligus
       tetap general pada berbagai latar belakang foto nyata & kamera.
    """

    def __init__(
        self,
        n_classical: int = 49,
        classical_weight: float = 0.20,
        lda_shrinkage: float = 0.20,
        lda_weight: float = 1.10,
    ):
        self.n_classical = n_classical
        self.classical_weight = classical_weight
        self.lda_shrinkage = lda_shrinkage
        self.lda_weight = lda_weight

    def fit(self, X, y):
        X = np.asarray(X, dtype=np.float32)
        X_cls = X[:, : self.n_classical]
        X_sem = X[:, self.n_classical :]

        self.classical_scaler_ = StandardScaler()
        cls_norm = normalize(self.classical_scaler_.fit_transform(X_cls))
        base = normalize(np.hstack([X_sem, cls_norm * self.classical_weight]))

        self.lda_ = LinearDiscriminantAnalysis(solver="eigen", shrinkage=self.lda_shrinkage)
        self.lda_.fit(base, y)
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=np.float32)
        X_cls = X[:, : self.n_classical]
        X_sem = X[:, self.n_classical :]

        cls_norm = normalize(self.classical_scaler_.transform(X_cls))
        base = normalize(np.hstack([X_sem, cls_norm * self.classical_weight]))
        proj = normalize(self.lda_.transform(base)) * self.lda_weight
        return normalize(np.hstack([base, proj])).astype(np.float32)

    def transform_classical_zscore(self, X_classical):
        X_classical = np.asarray(X_classical, dtype=np.float32)
        return self.classical_scaler_.transform(X_classical)


def fix_mask_orientation(mask):
    """
    Memastikan mask objek selalu putih (255) di tengah dan background hitam (0) di tepi.
    Jika tepi frame didominasi warna putih (> 50%), berarti mask terbalik dan harus di-invert.
    """
    top = mask[0, :]
    bottom = mask[-1, :]
    left = mask[:, 0]
    right = mask[:, -1]
    border = np.concatenate([top, bottom, left, right])
    if np.mean(border > 0) > 0.5:
        mask = cv2.bitwise_not(mask)
    return mask


def preprocess_image(image_input, target_size=(256, 256)):
    """
    Preprocessing citra:
    1. Resize gambar ke resolusi standar 256x256
    2. Reduksi noise menggunakan Gaussian Blur
    3. Segmentasi adaptif Otsu dengan koreksi orientasi latar belakang
    4. Ekstraksi mask kontur objek utama
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            raise ValueError(f"Gagal membaca gambar: {image_input}")
    else:
        img = image_input.copy()

    img_resized = cv2.resize(img, target_size)
    blurred = cv2.GaussianBlur(img_resized, (5, 5), 0)
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

    # Segmentasi Otsu
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Perbaiki orientasi agar background selalu 0 (hitam) dan objek selalu 255 (putih)
    mask = fix_mask_orientation(mask)

    # Bersihkan noise dengan operasi morfologi Close dan Open
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_OPEN, kernel)

    # Ambil kontur terbesar
    contours, _ = cv2.findContours(mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    final_mask = np.zeros_like(mask_cleaned)
    if contours:
        c_largest = max(contours, key=cv2.contourArea)
        # Hanya gunakan kontur jika luasnya masuk akal (> 2% frame)
        if cv2.contourArea(c_largest) > (256 * 256 * 0.02):
            cv2.drawContours(final_mask, [c_largest], -1, 255, thickness=cv2.FILLED)
        else:
            final_mask = mask_cleaned
    else:
        final_mask = mask_cleaned

    return img_resized, gray, final_mask


def extract_color_features(img_bgr, mask=None):
    """
    Ekstraksi Fitur Warna Berbasis Objek:
    - Histogram HSV dihitung HANYA pada piksel objek sampah (mengabaikan background kamar)
    - LAB Mean & Std Dev dihitung murni pada piksel objek
    """
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

    # Gunakan mask jika memiliki cukup piksel objek (> 100 piksel)
    calc_mask = mask if (mask is not None and np.sum(mask > 0) > 100) else None

    # Histogram Warna HSV
    h_hist = cv2.calcHist([hsv], [0], calc_mask, [16], [0, 180]).flatten()
    s_hist = cv2.calcHist([hsv], [1], calc_mask, [8], [0, 256]).flatten()
    v_hist = cv2.calcHist([hsv], [2], calc_mask, [8], [0, 256]).flatten()

    # Normalisasi L1 agar independen dari ukuran objek
    h_hist = h_hist / (np.sum(h_hist) + 1e-6)
    s_hist = s_hist / (np.sum(s_hist) + 1e-6)
    v_hist = v_hist / (np.sum(v_hist) + 1e-6)

    # Rata-rata dan Standar Deviasi kanal LAB murni pada objek
    if calc_mask is not None:
        obj_pixels = lab[calc_mask > 0]
        mean_lab = np.mean(obj_pixels, axis=0) / 255.0
        std_lab = np.std(obj_pixels, axis=0) / 255.0
    else:
        mean_lab = np.mean(lab, axis=(0, 1)) / 255.0
        std_lab = np.std(lab, axis=(0, 1)) / 255.0

    return np.concatenate([h_hist, s_hist, v_hist, mean_lab, std_lab]).tolist()


def extract_shape_features(mask):
    """
    Ekstraksi Fitur Bentuk (Morfologi Kontur):
    - Area & Perimeter normalisasi
    - Circularity (kebundaran botol/kaleng vs kardus)
    - Aspect Ratio (panjang vs lebar)
    - Solidity & Extent
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return [0.0, 0.0, 0.0, 0.0, 0.0]

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c) / (256 * 256)
    perimeter = cv2.arcLength(c, True) / 256
    circularity = (
        (4 * np.pi * cv2.contourArea(c)) / (cv2.arcLength(c, True) ** 2)
        if cv2.arcLength(c, True) > 0
        else 0.0
    )

    x, y, w, h = cv2.boundingRect(c)
    aspect_ratio = float(w) / h if h > 0 else 0.0

    hull = cv2.convexHull(c)
    hull_area = cv2.contourArea(hull)
    solidity = float(cv2.contourArea(c)) / hull_area if hull_area > 0 else 0.0

    return [float(area), float(perimeter), float(circularity), float(aspect_ratio), float(solidity)]


def extract_texture_features(gray_img, mask=None):
    """
    Ekstraksi Fitur Tekstur & Edge:
    - GLCM (Contrast, Dissimilarity, Homogeneity, Energy, Correlation) pada bounding box objek
    - Edge Density (Canny) pada objek
    """
    crop_gray = gray_img
    if mask is not None:
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            if w > 20 and h > 20:
                crop_gray = gray_img[y : y + h, x : x + w]

    crop_gray = cv2.resize(crop_gray, (128, 128))

    glcm = graycomatrix(
        crop_gray, distances=[1, 2], angles=[0, np.pi / 2], levels=256, symmetric=True, normed=True
    )
    c = graycoprops(glcm, "contrast").mean() / 100.0
    d = graycoprops(glcm, "dissimilarity").mean() / 50.0
    h = graycoprops(glcm, "homogeneity").mean()
    e = graycoprops(glcm, "energy").mean()
    corr = graycoprops(glcm, "correlation").mean()

    # Kerapatan tepi Canny
    edges = cv2.Canny(crop_gray, 40, 120)
    edge_density = float(np.mean(edges > 0))

    return [float(c), float(d), float(h), float(e), float(corr), edge_density]


def _prep_dino_tensor(img_bgr, size=224, flip=False):
    if flip:
        img_bgr = cv2.flip(img_bgr, 1)
    resized = cv2.resize(img_bgr, (size, size), interpolation=cv2.INTER_CUBIC)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    chw = np.transpose(rgb, (2, 0, 1))[None, ...]
    return (chw - _IMAGENET_MEAN) / _IMAGENET_STD


def _pool_dino_output(hidden_state):
    """Ekstrak representasi visual multi-token DINOv2: CLS + Patch Mean + Patch Max (1.152-D)."""
    cls_tok = normalize(hidden_state[:, 0, :])
    patch_mean = normalize(hidden_state[:, 5:, :].mean(axis=1))
    patch_max = normalize(hidden_state[:, 5:, :].max(axis=1))
    return normalize(np.concatenate([cls_tok * 1.2, patch_mean * 1.0, patch_max * 0.5], axis=1))


def extract_semantic_features(img_bgr, use_flip_avg=True):
    """
    Ekstraksi fitur visual semantik DINOv2-Small (1.152 dimensi) menggunakan ONNX Runtime.
    Saat use_flip_avg=True, vektor dirata-ratakan dengan versi flip horizontal agar invarian orientasi.
    """
    sess = _get_dino_session()
    in_name = sess.get_inputs()[0].name
    if use_flip_avg:
        batch = np.concatenate(
            [_prep_dino_tensor(img_bgr, flip=False), _prep_dino_tensor(img_bgr, flip=True)], axis=0
        )
        out = sess.run(None, {in_name: batch})[0]
        pooled = _pool_dino_output(out)
        vec = normalize((pooled[0:1] + pooled[1:2]))[0]
    else:
        batch = _prep_dino_tensor(img_bgr, flip=False)
        out = sess.run(None, {in_name: batch})[0]
        vec = _pool_dino_output(out)[0]
    return vec.astype(np.float32)


def extract_semantic_batch(img_bgr_list, use_flip_avg=True, batch_size=32):
    """Ekstraksi batch cepat untuk proses training seluruh dataset."""
    sess = _get_dino_session()
    in_name = sess.get_inputs()[0].name
    results = []
    for i in range(0, len(img_bgr_list), batch_size):
        chunk = img_bgr_list[i : i + batch_size]
        b_orig = np.concatenate([_prep_dino_tensor(im, flip=False) for im in chunk], axis=0)
        p_orig = _pool_dino_output(sess.run(None, {in_name: b_orig})[0])
        if use_flip_avg:
            b_flip = np.concatenate([_prep_dino_tensor(im, flip=True) for im in chunk], axis=0)
            p_flip = _pool_dino_output(sess.run(None, {in_name: b_flip})[0])
            pooled = normalize(p_orig + p_flip)
        else:
            pooled = p_orig
        results.append(pooled)
    return np.vstack(results).astype(np.float32)


def extract_classical_features(img_resized, gray, mask):
    """Ekstraksi tepat 49 fitur klasik (32 HSV + 6 LAB + 5 bentuk + 6 tekstur & edge)."""
    color_feats = extract_color_features(img_resized, mask)
    shape_feats = extract_shape_features(mask)
    texture_feats = extract_texture_features(gray, mask)
    return np.array(color_feats + shape_feats + texture_feats, dtype=np.float32)


def extract_all_features(image_input, use_flip_avg=True):
    """
    Gabungan vektor fitur multi-domain (1.201 dimensi):
    - Indeks [0..48]    : 49 fitur klasik (32 HSV + 6 LAB + 5 Morfologi Bentuk + 6 Tekstur GLCM & Canny)
    - Indeks [49..1200] : 1.152 fitur visual semantik DINOv2-Small (invarian latar & pencahayaan)
    """
    if isinstance(image_input, str):
        raw_img = cv2.imread(image_input)
        if raw_img is None:
            raise ValueError(f"Gagal membaca gambar: {image_input}")
    else:
        raw_img = image_input

    img_resized, gray, mask = preprocess_image(raw_img)
    classical_49 = extract_classical_features(img_resized, gray, mask)
    semantic_1152 = extract_semantic_features(raw_img, use_flip_avg=use_flip_avg)

    features = np.concatenate([classical_49, semantic_1152]).astype(np.float32)
    return features, img_resized, mask
