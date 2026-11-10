import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

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
    circularity = (4 * np.pi * cv2.contourArea(c)) / (cv2.arcLength(c, True) ** 2) if cv2.arcLength(c, True) > 0 else 0.0

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
    # Jika ada mask dan kontur, crop fokus ke objek agar tekstur background tidak ikut
    crop_gray = gray_img
    if mask is not None:
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            if w > 20 and h > 20:
                crop_gray = gray_img[y:y+h, x:x+w]

    crop_gray = cv2.resize(crop_gray, (128, 128))

    glcm = graycomatrix(crop_gray, distances=[1, 2], angles=[0, np.pi/2], levels=256, symmetric=True, normed=True)
    c = graycoprops(glcm, 'contrast').mean() / 100.0
    d = graycoprops(glcm, 'dissimilarity').mean() / 50.0
    h = graycoprops(glcm, 'homogeneity').mean()
    e = graycoprops(glcm, 'energy').mean()
    corr = graycoprops(glcm, 'correlation').mean()

    # Kerapatan tepi Canny
    edges = cv2.Canny(crop_gray, 40, 120)
    edge_density = float(np.mean(edges > 0))

    return [float(c), float(d), float(h), float(e), float(corr), edge_density]

def extract_all_features(image_input):
    """
    Gabungan vektor fitur multi-domain:
    Total dimensi fitur = 49 (32 HSV histogram + 6 LAB stats + 5 bentuk + 6 tekstur & edge)
    """
    img_resized, gray, mask = preprocess_image(image_input)
    color_feats = extract_color_features(img_resized, mask)
    shape_feats = extract_shape_features(mask)
    texture_feats = extract_texture_features(gray, mask)

    features = color_feats + shape_feats + texture_feats
    return np.array(features, dtype=np.float32), img_resized, mask
