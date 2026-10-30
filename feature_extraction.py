import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

def preprocess_image(image_input, target_size=(256, 256)):
    """
    Preprocessing citra:
    1. Resize gambar ke resolusi standar 256x256
    2. Reduksi noise menggunakan Gaussian Blur
    3. Segmentasi biner menggunakan Otsu Thresholding
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

    # Segmentasi Otsu (Deteksi objek yang kontras terhadap latar belakang)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Jika mask mendominasi > 85% atau < 5% frame, gunakan threshold adaptive
    mask_ratio = np.mean(mask > 0)
    if mask_ratio > 0.85 or mask_ratio < 0.05:
        mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 2)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Ambil kontur terbesar
    contours, _ = cv2.findContours(mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    final_mask = np.zeros_like(mask_cleaned)
    if contours:
        c_largest = max(contours, key=cv2.contourArea)
        cv2.drawContours(final_mask, [c_largest], -1, 255, thickness=cv2.FILLED)
    else:
        final_mask = mask_cleaned

    return img_resized, gray, final_mask

def extract_color_features(img_bgr, mask=None):
    """
    Ekstraksi Fitur Warna Lengkap:
    1. HSV Histogram (16 bin Hue, 8 bin Saturation, 8 bin Value) -> Mampu membedakan botol hijau, plastik bening, kaleng metalik
    2. LAB Mean & Std Dev -> Lebih sensitif terhadap perbedaan persepsi visual manusia
    """
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    
    # Histogram Warna HSV
    h_hist = cv2.calcHist([hsv], [0], None, [16], [0, 180]).flatten() / (256 * 256)
    s_hist = cv2.calcHist([hsv], [1], None, [8], [0, 256]).flatten() / (256 * 256)
    v_hist = cv2.calcHist([hsv], [2], None, [8], [0, 256]).flatten() / (256 * 256)

    # Rata-rata dan Standar Deviasi kanal LAB
    mean_lab = np.mean(lab, axis=(0, 1))
    std_lab = np.std(lab, axis=(0, 1))

    return np.concatenate([h_hist, s_hist, v_hist, mean_lab, std_lab]).tolist()

def extract_shape_features(mask):
    """
    Ekstraksi Fitur Bentuk:
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
    circularity = (4 * np.pi * cv2.contourArea(c)) / (cv2.arcLength(c, True) ** 2) if cv2.arcLength(c, True) > 0 else 0.0

    x, y, w, h = cv2.boundingRect(c)
    aspect_ratio = float(w) / h if h > 0 else 0.0

    hull = cv2.convexHull(c)
    hull_area = cv2.contourArea(hull)
    solidity = float(cv2.contourArea(c)) / hull_area if hull_area > 0 else 0.0

    return [float(area), float(perimeter), float(circularity), float(aspect_ratio), float(solidity)]

def extract_texture_features(gray_img):
    """
    Ekstraksi Fitur Tekstur & Edge:
    - GLCM (Contrast, Dissimilarity, Homogeneity, Energy, Correlation)
    - Edge Density (Canny) -> Membedakan kertas/kaleng remuk yang banyak lipatan vs permukaan halus
    """
    glcm = graycomatrix(gray_img, distances=[1, 2], angles=[0, np.pi/2], levels=256, symmetric=True, normed=True)
    c = graycoprops(glcm, 'contrast').mean()
    d = graycoprops(glcm, 'dissimilarity').mean()
    h = graycoprops(glcm, 'homogeneity').mean()
    e = graycoprops(glcm, 'energy').mean()
    corr = graycoprops(glcm, 'correlation').mean()

    # Kerapatan tepi (banyak lekukan/remukan vs datar)
    edges = cv2.Canny(gray_img, 40, 120)
    edge_density = float(np.mean(edges > 0))

    return [float(c), float(d), float(h), float(e), float(corr), edge_density]

def extract_all_features(image_input):
    """
    Gabungan vektor fitur kaya:
    Total dimensi fitur = 38 (32 warna + 5 bentuk + 6 tekstur & edge)
    """
    img_resized, gray, mask = preprocess_image(image_input)
    color_feats = extract_color_features(img_resized, mask)
    shape_feats = extract_shape_features(mask)
    texture_feats = extract_texture_features(gray)

    features = color_feats + shape_feats + texture_feats
    return np.array(features, dtype=np.float32), img_resized, mask
