import base64
import os
import random
import time
import webbrowser
from threading import Lock, Timer
from typing import Optional

import cv2
import joblib
import numpy as np
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from skimage.feature import graycomatrix, graycoprops
from sklearn.neighbors import KNeighborsClassifier

from feature_extraction import (
    extract_all_features,
    extract_color_features,
    extract_shape_features,
    extract_texture_features,
    preprocess_image,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "knn_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI(
    title="Viskom Lab — Sistem Klasifikasi Citra Sampah",
    description="Workbench Pemrosesan Citra Digital & Klasifikasi K-Nearest Neighbor (49-D Feature Space)",
    version="2.0.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def disable_browser_cache(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

# Metadata kelas dan penjelasan domain
CLASS_META = {
    "botol_kaca": {
        "label": "Botol Kaca",
        "code": "GLS-01",
        "material": "Silika / Kaca Anorganik",
        "recyclable": "Dapat Didaur Ulang (Anorganik Keras)",
        "accent": "#0F766E",
        "characteristic": "Permukaan reflektif dengan kontras tepi tajam, bentuk silinder memanjang (aspect ratio rendah-sedang) dan solidity tinggi.",
    },
    "botol_plastik": {
        "label": "Botol Plastik",
        "code": "PET-02",
        "material": "Polyethylene Terephthalate (PET)",
        "recyclable": "Dapat Didaur Ulang (Plastik PET/HDPE)",
        "accent": "#1D4ED8",
        "characteristic": "Transparan atau berwarna cerah pada kanal HSV, tekstur homogen tinggi dengan variasi pencahayaan spekular.",
    },
    "kaleng": {
        "label": "Kaleng / Logam",
        "code": "ALU-03",
        "material": "Aluminium / Pelat Timah",
        "recyclable": "Nilai Daur Ulang Tinggi (Logam)",
        "accent": "#B45309",
        "characteristic": "Pantulan metalik berintensitas tinggi pada kanal Value (V), circularity silinder kompak, dan kerapatan tepi Canny tinggi dari cetakan label.",
    },
    "kardus": {
        "label": "Kardus",
        "code": "CRD-04",
        "material": "Serat Selulosa Bergelombang (Corrugated)",
        "recyclable": "Dapat Didaur Ulang (Serat Kertas Tebal)",
        "accent": "#A16207",
        "characteristic": "Dominasi spektrum Hue hangat (cokelat/kuning-merah), saturasi sedang, geometri poligonal/kotak dengan area rasio besar.",
    },
    "kertas": {
        "label": "Kertas",
        "code": "PPR-05",
        "material": "Serat Selulosa Lembaran",
        "recyclable": "Dapat Didaur Ulang (Serat Kertas)",
        "accent": "#4338CA",
        "characteristic": "Luminansi (L*) tinggi, saturasi rendah, serta tekstur lipatan/kusut yang terukur melalui GLCM contrast dan Canny edge.",
    },
}

PRESET_SAMPLES = [
    {
        "id": "botol_kaca",
        "label": "Sampel Botol Kaca",
        "category": "botol_kaca",
        "filename": "sampah botol kaca.jpeg",
    },
    {
        "id": "botol_plastik",
        "label": "Sampel Botol Plastik",
        "category": "botol_plastik",
        "filename": "sampah botol plastik.jpeg",
    },
    {
        "id": "kaleng",
        "label": "Sampel Kaleng",
        "category": "kaleng",
        "filename": "sampah kaleng.jpg",
    },
    {
        "id": "kardus",
        "label": "Sampel Kardus",
        "category": "kardus",
        "filename": "sampah kardus.jpeg",
    },
    {
        "id": "kertas",
        "label": "Sampel Kertas",
        "category": "kertas",
        "filename": "sampah kertas.jpg",
    },
]


def load_artifacts():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        raise RuntimeError("Model KNN atau Scaler belum tersedia. Jalankan `python train.py` terlebih dahulu.")
    knn_model = joblib.load(MODEL_PATH)
    std_scaler = joblib.load(SCALER_PATH)
    return knn_model, std_scaler


model, scaler = load_artifacts()
MODEL_LOCK = Lock()


def encode_png_base64(img_bgr_or_gray: np.ndarray) -> str:
    success, buf = cv2.imencode(".png", img_bgr_or_gray)
    if not success:
        raise ValueError("Gagal melakukan encoding citra ke PNG.")
    b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def lab_to_hex(l_norm: float, a_norm: float, b_norm: float) -> str:
    """Konversi rata-rata LAB (skala 0..1 dari OpenCV 0..255) menjadi warna RGB Hex."""
    l_cv = int(np.clip(round(l_norm * 255.0), 0, 255))
    a_cv = int(np.clip(round(a_norm * 255.0), 0, 255))
    b_cv = int(np.clip(round(b_norm * 255.0), 0, 255))
    patch_lab = np.uint8([[[l_cv, a_cv, b_cv]]])
    patch_bgr = cv2.cvtColor(patch_lab, cv2.COLOR_LAB2BGR)[0, 0]
    r, g, b = int(patch_bgr[2]), int(patch_bgr[1]), int(patch_bgr[0])
    return f"#{r:02X}{g:02X}{b:02X}"


def build_feature_catalog(raw_vec: np.ndarray, scaled_vec: np.ndarray):
    catalog = []
    # 0..15: Hue histogram (16 bin, 0..180 derajat OpenCV -> 0..360 derajat nyata)
    for i in range(16):
        deg_start = int(i * 22.5)
        deg_end = int((i + 1) * 22.5)
        catalog.append({
            "index": i,
            "code": f"HSV_H_{i:02d}",
            "name": f"Histogram Hue Bin {i + 1} ({deg_start}°–{deg_end}°)",
            "group": "Warna HSV",
            "raw": float(raw_vec[i]),
            "scaled": float(scaled_vec[i]),
        })
    # 16..23: Saturation histogram (8 bin)
    for i in range(8):
        idx = 16 + i
        s_start = i * 32
        s_end = (i + 1) * 32 - 1
        catalog.append({
            "index": idx,
            "code": f"HSV_S_{i:02d}",
            "name": f"Histogram Saturation Bin {i + 1} ({s_start}–{s_end})",
            "group": "Warna HSV",
            "raw": float(raw_vec[idx]),
            "scaled": float(scaled_vec[idx]),
        })
    # 24..31: Value histogram (8 bin)
    for i in range(8):
        idx = 24 + i
        v_start = i * 32
        v_end = (i + 1) * 32 - 1
        catalog.append({
            "index": idx,
            "code": f"HSV_V_{i:02d}",
            "name": f"Histogram Value Bin {i + 1} ({v_start}–{v_end})",
            "group": "Warna HSV",
            "raw": float(raw_vec[idx]),
            "scaled": float(scaled_vec[idx]),
        })
    # 32..37: LAB Mean & Std
    lab_names = [
        ("LAB_L_MEAN", "CIE-LAB Rata-rata Luminance (L*)"),
        ("LAB_A_MEAN", "CIE-LAB Rata-rata Kanal Hijau-Merah (a*)"),
        ("LAB_B_MEAN", "CIE-LAB Rata-rata Kanal Biru-Kuning (b*)"),
        ("LAB_L_STD", "CIE-LAB Simpangan Baku Luminance (σ L*)"),
        ("LAB_A_STD", "CIE-LAB Simpangan Baku Kanal a* (σ a*)"),
        ("LAB_B_STD", "CIE-LAB Simpangan Baku Kanal b* (σ b*)"),
    ]
    for offset, (code, label) in enumerate(lab_names):
        idx = 32 + offset
        catalog.append({
            "index": idx,
            "code": code,
            "name": label,
            "group": "Warna CIE-LAB",
            "raw": float(raw_vec[idx]),
            "scaled": float(scaled_vec[idx]),
        })
    # 38..42: Shape features
    shape_names = [
        ("SHP_AREA", "Rasio Luas Kontur Objek (Area Ratio)"),
        ("SHP_PERIM", "Rasio Keliling Kontur (Perimeter Ratio)"),
        ("SHP_CIRC", "Kebundaran Kontur (Circularity 4πA/P²)"),
        ("SHP_ASPECT", "Rasio Aspek Bounding Box (W / H)"),
        ("SHP_SOLID", "Kepadatan Bentuk (Solidity Area/Hull)"),
    ]
    for offset, (code, label) in enumerate(shape_names):
        idx = 38 + offset
        catalog.append({
            "index": idx,
            "code": code,
            "name": label,
            "group": "Morfologi Bentuk",
            "raw": float(raw_vec[idx]),
            "scaled": float(scaled_vec[idx]),
        })
    # 43..48: Texture & Edge features
    tex_names = [
        ("GLCM_CONT", "GLCM Contrast (Variasi Intensitas Lokal)"),
        ("GLCM_DISS", "GLCM Dissimilarity (Ketidakmiripan Pasangan Piksel)"),
        ("GLCM_HOMO", "GLCM Homogeneity (Kehalusan Permukaan)"),
        ("GLCM_ENER", "GLCM Energy (Keseragaman Tekstur)"),
        ("GLCM_CORR", "GLCM Correlation (Korelasi Linear Ketetanggaan)"),
        ("EDGE_DENS", "Kerapatan Tepi Canny (Canny Edge Density)"),
    ]
    for offset, (code, label) in enumerate(tex_names):
        idx = 43 + offset
        catalog.append({
            "index": idx,
            "code": code,
            "name": label,
            "group": "Tekstur & Tepi",
            "raw": float(raw_vec[idx]),
            "scaled": float(scaled_vec[idx]),
        })
    return catalog


def hex_to_bgr(hex_str: str):
    h = hex_str.lstrip("#")
    if len(h) != 6:
        return (64, 210, 95)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b, g, r)


def draw_focus_frame_annotated(
    img_resized: np.ndarray,
    c_main,
    hull,
    bbox_info: dict,
    class_label: str,
    class_code: str,
    confidence_pct: float,
    accent_hex: str,
) -> np.ndarray:
    """
    Membuat visualisasi tahap 2.1 resolusi tajam (512x512) dengan:
    - Kontur objek (hijau zamrud) & Convex Hull (jingga)
    - Bingkai fokus sudut-L (L-brackets) berwarna aksen kelas terdeteksi
    - Label kelas & persentase keyakinan langsung menempel pada bingkai objek
    """
    scale = 2
    canvas = cv2.resize(img_resized, (256 * scale, 256 * scale), interpolation=cv2.INTER_CUBIC)
    accent_bgr = hex_to_bgr(accent_hex)

    if c_main is not None and hull is not None:
        cv2.drawContours(canvas, [hull * scale], -1, (30, 144, 255), 1, cv2.LINE_AA)
        cv2.drawContours(canvas, [c_main * scale], -1, (64, 210, 95), 2, cv2.LINE_AA)

        x = bbox_info["x"] * scale
        y = bbox_info["y"] * scale
        w = bbox_info["w"] * scale
        h = bbox_info["h"] * scale
        x2, y2 = x + w, y + h

        # Kotak tipis panduan Bounding Box
        cv2.rectangle(canvas, (x, y), (x2, y2), (240, 240, 236), 1, cv2.LINE_AA)

        # Sudut bidik (L-brackets) tegas pada 4 pojok bingkai
        corner = max(14, min(28, int(min(w, h) * 0.2)))
        t = 3
        # Kiri-atas
        cv2.line(canvas, (x, y), (x + corner, y), accent_bgr, t, cv2.LINE_AA)
        cv2.line(canvas, (x, y), (x, y + corner), accent_bgr, t, cv2.LINE_AA)
        # Kanan-atas
        cv2.line(canvas, (x2, y), (x2 - corner, y), accent_bgr, t, cv2.LINE_AA)
        cv2.line(canvas, (x2, y), (x2, y + corner), accent_bgr, t, cv2.LINE_AA)
        # Kiri-bawah
        cv2.line(canvas, (x, y2), (x + corner, y2), accent_bgr, t, cv2.LINE_AA)
        cv2.line(canvas, (x, y2), (x, y2 - corner), accent_bgr, t, cv2.LINE_AA)
        # Kanan-bawah
        cv2.line(canvas, (x2, y2), (x2 - corner, y2), accent_bgr, t, cv2.LINE_AA)
        cv2.line(canvas, (x2, y2), (x2, y2 - corner), accent_bgr, t, cv2.LINE_AA)

        # Tag label kelas + confidence di tepi atas bingkai
        tag_text = f"{class_code} | {class_label.upper()} {confidence_pct:.1f}%"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.48
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(tag_text, font, font_scale, thickness)
        pad_x, pad_y = 8, 6
        box_w = tw + pad_x * 2
        box_h = th + pad_y * 2

        tag_x = max(4, min(x, canvas.shape[1] - box_w - 4))
        tag_y = y - box_h - 4 if (y - box_h - 4) >= 4 else min(y + 4, canvas.shape[0] - box_h - 4)

        cv2.rectangle(canvas, (tag_x, tag_y), (tag_x + box_w, tag_y + box_h), accent_bgr, -1)
        cv2.rectangle(canvas, (tag_x, tag_y), (tag_x + box_w, tag_y + box_h), (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(
            canvas,
            tag_text,
            (tag_x + pad_x, tag_y + th + pad_y - 1),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )

    return canvas


def run_vision_pipeline(img_bgr: np.ndarray, source_name: str = "Citra Input", fast_mode: bool = False):
    t0 = time.perf_counter()
    orig_h, orig_w = img_bgr.shape[:2]

    # 1. Preprocessing & Ekstraksi Fitur Terpadu (49 klasik + 1.152 semantik DINOv2)
    features, img_resized, mask = extract_all_features(img_bgr, use_flip_avg=(not fast_mode))
    gray = cv2.cvtColor(cv2.GaussianBlur(img_resized, (5, 5), 0), cv2.COLOR_BGR2GRAY)

    # 2. Ekstrak kontur & bounding box utama
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bbox_info = {"x": 0, "y": 0, "w": 256, "h": 256, "contour_px": 0, "hull_px": 0, "perimeter_px": 0.0}
    c_main = None
    hull = None
    crop_gray = gray
    if contours:
        c_main = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c_main)
        hull = cv2.convexHull(c_main)
        c_area = float(cv2.contourArea(c_main))
        h_area = float(cv2.contourArea(hull))
        perim = float(cv2.arcLength(c_main, True))
        bbox_info = {
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
            "contour_px": int(round(c_area)),
            "hull_px": int(round(h_area)),
            "perimeter_px": round(perim, 1),
        }
        if w > 20 and h > 20:
            crop_gray = gray[y:y + h, x:x + w]

    # 3. Standarisasi & Prediksi KNN
    features_scaled = scaler.transform([features])
    if hasattr(scaler, "transform_classical_zscore"):
        classical_z = scaler.transform_classical_zscore([features[:49]])[0]
    else:
        classical_z = features_scaled[0][:49]
    pred_class = str(model.predict(features_scaled)[0])
    probs = model.predict_proba(features_scaled)[0]

    # 4. Bedah K-Nearest Neighbors di Ruang 49-D
    distances, indices = model.kneighbors(features_scaled, n_neighbors=model.n_neighbors, return_distance=True)
    d_list = distances[0]
    i_list = indices[0]
    inv_weights = [1.0 / (float(d) + 1e-6) for d in d_list]
    total_w = sum(inv_weights) + 1e-9

    neighbors_breakdown = []
    for rank, (dist_val, train_idx, w_val) in enumerate(zip(d_list, i_list, inv_weights), start=1):
        cls_idx = int(model._y[train_idx])
        cls_key = str(model.classes_[cls_idx])
        meta = CLASS_META.get(cls_key, {"label": cls_key, "code": cls_key.upper()})
        neighbors_breakdown.append({
            "rank": rank,
            "sample_index": int(train_idx),
            "class_key": cls_key,
            "class_label": meta["label"],
            "class_code": meta["code"],
            "manhattan_distance": round(float(dist_val), 3),
            "vote_weight": round(float(w_val / total_w) * 100.0, 2),
        })

    # 5. Susun probabilitas per kelas
    prob_list = []
    for cls_key, p_val in zip(model.classes_, probs):
        cls_str = str(cls_key)
        meta = CLASS_META.get(cls_str, {"label": cls_str, "code": cls_str.upper(), "accent": "#333"})
        prob_list.append({
            "class_key": cls_str,
            "label": meta["label"],
            "code": meta["code"],
            "accent": meta["accent"],
            "probability": round(float(p_val) * 100.0, 2),
        })
    prob_list.sort(key=lambda item: item["probability"], reverse=True)

    pred_meta = CLASS_META.get(pred_class, {
        "label": pred_class.upper(),
        "code": "UNK-00",
        "material": "-",
        "recyclable": "-",
        "accent": "#1B5E3C",
        "characteristic": "",
    })

    # 6. Buat visualisasi 4 tahap pemrosesan citra
    # Tahap A: Bingkai deteksi + label kelas + kontur + convex hull
    annotated = draw_focus_frame_annotated(
        img_resized=img_resized,
        c_main=c_main,
        hull=hull,
        bbox_info=bbox_info,
        class_label=pred_meta["label"],
        class_code=pred_meta["code"],
        confidence_pct=prob_list[0]["probability"],
        accent_hex=pred_meta["accent"],
    )

    # Tahap B: Mask Biner Otsu & Morfologi
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    # Tahap C: Objek Tersegmentasi (latar belakang dibuat gelap terstruktur agar kontras)
    checker_bg = np.full_like(img_resized, 22)
    isolated = np.where(mask[..., None] > 0, img_resized, checker_bg)

    # Tahap D: Peta Tepi Canny 128x128 pada ROI
    crop_gray_128 = cv2.resize(crop_gray, (128, 128))
    edges_128 = cv2.Canny(crop_gray_128, 40, 120)
    edge_vis = cv2.cvtColor((crop_gray_128 * 0.38).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    edge_vis[edges_128 > 0] = (45, 230, 145)
    edge_vis_256 = cv2.resize(edge_vis, (256, 256), interpolation=cv2.INTER_NEAREST)

    # 7. Ringkasan Warna, Bentuk, dan Tekstur
    dominant_hex = lab_to_hex(float(features[32]), float(features[33]), float(features[34]))
    mask_coverage_pct = round(float(np.mean(mask > 0)) * 100.0, 2)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        "source_name": source_name,
        "original_resolution": f"{orig_w}×{orig_h} px",
        "working_resolution": "256×256 px",
        "processing_time_ms": elapsed_ms,
        "mask_coverage_pct": mask_coverage_pct,
        "bbox": bbox_info,
        "stages": {
            "original": encode_png_base64(img_resized),
            "annotated": encode_png_base64(annotated),
            "mask": encode_png_base64(mask_bgr),
            "isolated": encode_png_base64(isolated),
            "edges": encode_png_base64(edge_vis_256),
        },
        "prediction": {
            "class_key": pred_class,
            "label": pred_meta["label"],
            "code": pred_meta["code"],
            "material": pred_meta["material"],
            "recyclable": pred_meta["recyclable"],
            "accent": pred_meta["accent"],
            "characteristic": pred_meta["characteristic"],
            "confidence_pct": prob_list[0]["probability"],
        },
        "probabilities": prob_list,
        "neighbors": neighbors_breakdown,
        "color_analysis": {
            "dominant_hex": dominant_hex,
            "hue_bins": [round(float(x), 4) for x in features[0:16]],
            "sat_bins": [round(float(x), 4) for x in features[16:24]],
            "val_bins": [round(float(x), 4) for x in features[24:32]],
            "lab_mean": [round(float(features[32]) * 255.0, 1), round(float(features[33]) * 255.0, 1), round(float(features[34]) * 255.0, 1)],
            "lab_std": [round(float(features[35]) * 255.0, 1), round(float(features[36]) * 255.0, 1), round(float(features[37]) * 255.0, 1)],
            "lab_norm": [round(float(x), 4) for x in features[32:38]],
        },
        "shape_analysis": [
            {
                "key": "area_ratio",
                "name": "Area Ratio (Proporsi Luas)",
                "formula": "A_kontur / (256 × 256)",
                "value": round(float(features[38]), 4),
                "z_score": round(float(classical_z[38]), 3),
                "pct": min(100.0, round(float(features[38]) * 100.0, 1)),
                "desc": "Proporsi luas piksel objek terhadap bidang frame 256×256.",
            },
            {
                "key": "perimeter_ratio",
                "name": "Perimeter Ratio (Rasio Keliling)",
                "formula": "P_kontur / 256",
                "value": round(float(features[39]), 4),
                "z_score": round(float(classical_z[39]), 3),
                "pct": min(100.0, round((float(features[39]) / 4.5) * 100.0, 1)),
                "desc": "Panjang garis batas luar kontur objek yang dinormalisasi.",
            },
            {
                "key": "circularity",
                "name": "Circularity (Indeks Kebundaran)",
                "formula": "4π × Area / Perimeter²",
                "value": round(float(features[40]), 4),
                "z_score": round(float(classical_z[40]), 3),
                "pct": min(100.0, round(float(features[40]) * 100.0, 1)),
                "desc": "Mendekati 1.0 untuk objek bundar/kompak, lebih kecil untuk bentuk memanjang atau bergerigi.",
            },
            {
                "key": "aspect_ratio",
                "name": "Aspect Ratio (Rasio Lebar/Tinggi)",
                "formula": "Width_bbox / Height_bbox",
                "value": round(float(features[41]), 4),
                "z_score": round(float(classical_z[41]), 3),
                "pct": min(100.0, round((float(features[41]) / 2.2) * 100.0, 1)),
                "desc": "Perbandingan dimensi horizontal dan vertikal kotak pembatas (bounding box).",
            },
            {
                "key": "solidity",
                "name": "Solidity (Kepadatan Cembung)",
                "formula": "Area_kontur / Area_ConvexHull",
                "value": round(float(features[42]), 4),
                "z_score": round(float(classical_z[42]), 3),
                "pct": min(100.0, round(float(features[42]) * 100.0, 1)),
                "desc": "Mengukur tingkat keutuhan kontur terhadap selubung cembung (Convex Hull).",
            },
        ],
        "texture_analysis": [
            {
                "key": "glcm_contrast",
                "name": "GLCM Contrast",
                "formula": "∑ |i - j|² P(i,j) / 100",
                "value": round(float(features[43]), 4),
                "z_score": round(float(classical_z[43]), 3),
                "pct": min(100.0, round((float(features[43]) / 6.0) * 100.0, 1)),
                "desc": "Mengukur tajamnya fluktuasi intensitas lokal pada permukaan objek.",
            },
            {
                "key": "glcm_dissimilarity",
                "name": "GLCM Dissimilarity",
                "formula": "∑ |i - j| P(i,j) / 50",
                "value": round(float(features[44]), 4),
                "z_score": round(float(classical_z[44]), 3),
                "pct": min(100.0, round((float(features[44]) / 1.0) * 100.0, 1)),
                "desc": "Jarak rata-rata tingkat keabuan antar pasangan piksel bertetangga.",
            },
            {
                "key": "glcm_homogeneity",
                "name": "GLCM Homogeneity",
                "formula": "∑ P(i,j) / (1 + |i - j|²)",
                "value": round(float(features[45]), 4),
                "z_score": round(float(classical_z[45]), 3),
                "pct": min(100.0, round(float(features[45]) * 100.0, 1)),
                "desc": "Tingkat kehalusan tekstur permukaan (tinggi pada permukaan kaca/plastik mulus).",
            },
            {
                "key": "glcm_energy",
                "name": "GLCM Energy (ASM)",
                "formula": "√(∑ P(i,j)²)",
                "value": round(float(features[46]), 4),
                "z_score": round(float(classical_z[46]), 3),
                "pct": min(100.0, round(float(features[46]) * 250.0, 1)),
                "desc": "Keseragaman pola distribusi intensitas keabuan lokal.",
            },
            {
                "key": "glcm_correlation",
                "name": "GLCM Correlation",
                "formula": "Cov(i,j) / (σ_i × σ_j)",
                "value": round(float(features[47]), 4),
                "z_score": round(float(classical_z[47]), 3),
                "pct": min(100.0, max(0.0, round(float(features[47]) * 100.0, 1))),
                "desc": "Keterkaitan struktur garis/pola arah horizontal (0°) dan vertikal (90°).",
            },
            {
                "key": "canny_edge_density",
                "name": "Canny Edge Density",
                "formula": "N_edge(40,120) / (128 × 128)",
                "value": round(float(features[48]), 4),
                "z_score": round(float(classical_z[48]), 3),
                "pct": min(100.0, round(float(features[48]) * 350.0, 1)),
                "desc": "Kerapatan piksel tepi Canny pada ROI objek (tekstur tulisan, lipatan, atau lekukan).",
            },
        ],
        "vector_49d": build_feature_catalog(features[:49], classical_z),
    }


class SampleRequest(BaseModel):
    sample_id: Optional[str] = None
    random_from_dataset: bool = False
    category: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="File templates/index.html belum ditemukan.")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/info")
async def get_system_info():
    available_presets = []
    for item in PRESET_SAMPLES:
        full_p = os.path.join(BASE_DIR, item["filename"])
        if os.path.exists(full_p):
            available_presets.append(item)

    dataset_counts = {}
    if os.path.exists(DATASET_DIR):
        for cls_name in os.listdir(DATASET_DIR):
            cls_dir = os.path.join(DATASET_DIR, cls_name)
            if os.path.isdir(cls_dir):
                files = [f for f in os.listdir(cls_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
                dataset_counts[cls_name] = len(files)

    return {
        "model_type": "K-Nearest Neighbors (KNN)",
        "n_neighbors": int(model.n_neighbors),
        "metric": str(model.metric).capitalize(),
        "weights": str(model.weights).capitalize(),
        "training_samples": int(model._fit_X.shape[0]),
        "feature_dimensions": int(model._fit_X.shape[1]),
        "classes": [
            {
                "key": str(c),
                **CLASS_META.get(str(c), {"label": str(c), "code": str(c).upper()}),
                "dataset_count": dataset_counts.get(str(c), 0),
            }
            for c in model.classes_
        ],
        "presets": available_presets,
    }


@app.get("/api/preset-image/{sample_id}")
async def get_preset_thumbnail(sample_id: str):
    for item in PRESET_SAMPLES:
        if item["id"] == sample_id:
            full_p = os.path.join(BASE_DIR, item["filename"])
            if os.path.exists(full_p):
                return FileResponse(full_p)
    raise HTTPException(status_code=404, detail="Sampel tidak ditemukan.")


@app.post("/api/analyze")
async def analyze_uploaded_image(file: UploadFile = File(...), fast: bool = False):
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="File gambar kosong.")
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Format file tidak didukung atau gambar rusak.")
    return run_vision_pipeline(img_bgr, source_name=file.filename or "Unggahan Pengguna", fast_mode=fast)


@app.post("/api/predict-live")
async def predict_live_frame(file: UploadFile = File(...)):
    """Endpoint ringan berlatensi rendah untuk HUD deteksi kelas langsung pada bingkai fokus kamera / crop."""
    t0 = time.perf_counter()
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Frame kosong.")
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Gagal mendekode frame.")

    features, img_resized, mask = extract_all_features(img_bgr, use_flip_avg=False)

    features_scaled = scaler.transform([features])
    pred_class = str(model.predict(features_scaled)[0])
    probs = model.predict_proba(features_scaled)[0]

    prob_list = []
    for cls_key, p_val in zip(model.classes_, probs):
        cls_str = str(cls_key)
        meta = CLASS_META.get(cls_str, {"label": cls_str, "code": cls_str.upper(), "accent": "#175938"})
        prob_list.append({
            "class_key": cls_str,
            "label": meta["label"],
            "code": meta["code"],
            "accent": meta["accent"],
            "probability": round(float(p_val) * 100.0, 1),
        })
    prob_list.sort(key=lambda item: item["probability"], reverse=True)

    pred_meta = CLASS_META.get(pred_class, {
        "label": pred_class.upper(),
        "code": "UNK-00",
        "accent": "#175938",
        "material": "-",
    })
    conf_pct = prob_list[0]["probability"]
    mask_coverage_pct = round(float(np.mean(mask > 0)) * 100.0, 1)

    if mask_coverage_pct < 6.0:
        guidance = "Objek terlalu kecil — dekatkan sampah ke dalam bingkai"
        guidance_level = "warn"
    elif mask_coverage_pct > 84.0:
        guidance = "Bingkai terlalu penuh / latar ramai — sedikit jauhkan"
        guidance_level = "warn"
    elif conf_pct < 55.0:
        guidance = "Objek terbaca — tahan stabil di latar polos agar lebih akurat"
        guidance_level = "mid"
    else:
        guidance = "Posisi fokus baik — siap dijepret & dianalisis!"
        guidance_level = "ready"

    mini_mask = cv2.resize(mask, (96, 96), interpolation=cv2.INTER_AREA)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)

    return {
        "prediction": {
            "class_key": pred_class,
            "label": pred_meta["label"],
            "code": pred_meta["code"],
            "accent": pred_meta["accent"],
            "material": pred_meta["material"],
            "confidence_pct": conf_pct,
        },
        "top3": prob_list[:3],
        "mask_coverage_pct": mask_coverage_pct,
        "guidance": guidance,
        "guidance_level": guidance_level,
        "mini_mask": encode_png_base64(mini_mask),
        "processing_time_ms": elapsed_ms,
    }


@app.post("/api/dataset/add")
async def add_photo_to_dataset(
    file: UploadFile = File(...),
    category: str = Form(...),
):
    """
    Menyimpan foto baru langsung ke folder dataset/<category>/user_<ts>.jpg
    dan langsung menambahkannya ke ruang fitur KNN (online incremental update < 0.3 detik)
    serta menyimpan models/knn_model.pkl secara atomik.
    """
    global model
    t0 = time.perf_counter()

    valid_classes = {str(c) for c in model.classes_}
    if category not in valid_classes:
        raise HTTPException(
            status_code=400,
            detail=f"Kategori '{category}' tidak valid. Pilihan: {sorted(valid_classes)}",
        )

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="File gambar kosong.")

    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Gambar tidak dapat dibaca.")

    # 1. Simpan gambar ke folder dataset/<category>/
    target_dir = os.path.join(DATASET_DIR, category)
    os.makedirs(target_dir, exist_ok=True)
    ts_ms = int(time.time() * 1000)
    filename = f"user_{ts_ms}.jpg"
    full_save_path = os.path.join(target_dir, filename)
    ok = cv2.imwrite(full_save_path, img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not ok:
        raise HTTPException(status_code=500, detail="Gagal menyimpan gambar ke folder dataset.")

    # 2. Ekstrak vektor fitur penuh & transformasi ke ruang metrik KNN
    features, _, _ = extract_all_features(img_bgr, use_flip_avg=True)
    x_new = scaler.transform([features]).astype(np.float32)

    # 3. Pembaruan instan model KNN (thread-safe & atomic write ke disk)
    with MODEL_LOCK:
        X_old = np.asarray(model._fit_X, dtype=np.float32)
        y_old = np.asarray(model.classes_[model._y])
        X_updated = np.vstack([X_old, x_new])
        y_updated = np.concatenate([y_old, np.array([category])])

        updated_knn = KNeighborsClassifier(
            n_neighbors=model.n_neighbors,
            weights=model.weights,
            metric=model.metric,
        )
        updated_knn.fit(X_updated, y_updated)

        tmp_path = MODEL_PATH + ".tmp"
        joblib.dump(updated_knn, tmp_path)
        os.replace(tmp_path, MODEL_PATH)
        model = updated_knn

    class_files = [
        f for f in os.listdir(target_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    meta = CLASS_META.get(category, {"label": category})
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)

    return {
        "status": "ok",
        "saved_path": f"dataset/{category}/{filename}",
        "category": category,
        "category_label": meta["label"],
        "class_dataset_count": len(class_files),
        "total_training_samples": int(model._fit_X.shape[0]),
        "feature_dimensions": int(model._fit_X.shape[1]),
        "elapsed_ms": elapsed_ms,
    }


@app.post("/api/analyze-sample")
async def analyze_sample_image(req: SampleRequest):
    if req.random_from_dataset:
        if not os.path.exists(DATASET_DIR):
            raise HTTPException(status_code=404, detail="Folder dataset tidak ditemukan.")
        valid_classes = [
            d for d in os.listdir(DATASET_DIR)
            if os.path.isdir(os.path.join(DATASET_DIR, d))
        ]
        if req.category and req.category in valid_classes:
            chosen_cls = req.category
        else:
            chosen_cls = random.choice(valid_classes)
        cls_folder = os.path.join(DATASET_DIR, chosen_cls)
        candidates = [
            f for f in os.listdir(cls_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if not candidates:
            raise HTTPException(status_code=404, detail=f"Tidak ada gambar di kategori {chosen_cls}.")
        chosen_file = random.choice(candidates)
        full_path = os.path.join(cls_folder, chosen_file)
        img_bgr = cv2.imread(full_path)
        if img_bgr is None:
            raise HTTPException(status_code=500, detail="Gagal membaca gambar sampel dari dataset.")
        return run_vision_pipeline(img_bgr, source_name=f"dataset/{chosen_cls}/{chosen_file}")

    for item in PRESET_SAMPLES:
        if item["id"] == req.sample_id:
            full_path = os.path.join(BASE_DIR, item["filename"])
            if not os.path.exists(full_path):
                raise HTTPException(status_code=404, detail=f"File {item['filename']} tidak ditemukan.")
            img_bgr = cv2.imread(full_path)
            if img_bgr is None:
                raise HTTPException(status_code=500, detail="Gagal membaca file sampel.")
            return run_vision_pipeline(img_bgr, source_name=item["filename"])

    raise HTTPException(status_code=404, detail="ID sampel tidak dikenali.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    url = f"http://127.0.0.1:{port}"
    print("=" * 68)
    print("  VISKOM LAB — WORKBENCH KLASIFIKASI CITRA SAMPAH (CV & KNN 49-D)")
    print(f"  Server berjalan di : {url}")
    print("=" * 68)
    Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
