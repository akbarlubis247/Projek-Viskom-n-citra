import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import cv2
import numpy as np
from feature_extraction import preprocess_image

def create_figure1():
    # Setup Figure: 14 x 18 inches at 300 DPI for ultra-crisp publication quality
    fig, ax = plt.subplots(figsize=(13, 17), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Palette
    c_bg = '#FAFAFA'
    c_header_bg = '#1E293B'      # Dark slate
    c_stage_border = '#CBD5E1'   # Light slate border
    c_stage_bg = '#FFFFFF'       # Pure white
    c_primary = '#0284C7'        # Blue accent
    c_teal = '#0D9488'           # Teal accent
    c_emerald = '#059669'        # Green accent
    c_amber = '#D97706'          # Amber accent
    c_purple = '#7C3AED'         # Purple accent
    c_dark_text = '#0F172A'
    c_muted_text = '#475569'

    fig.patch.set_facecolor(c_bg)

    def draw_rounded_box(ax, x, y, w, h, bg_color, border_color='#CBD5E1', radius=1.2, lw=1.5, zorder=2):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad={radius},rounding_size={radius}",
            ec=border_color, fc=bg_color, lw=lw, zorder=zorder
        )
        ax.add_patch(box)
        return box

    def draw_arrow(ax, x1, y1, x2, y2, color='#64748B', lw=2.0, zorder=5):
        ax.annotate(
            '', xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=lw,
                mutation_scale=15,
                shrinkA=2, shrinkB=2
            ),
            zorder=zorder
        )

    # -------------------------------------------------------------
    # 0. MAIN TITLE HEADER (Top)
    # -------------------------------------------------------------
    draw_rounded_box(ax, 3, 93.5, 94, 4.5, bg_color=c_header_bg, border_color=c_header_bg, radius=0.8)
    ax.text(50, 96.3, "ALUR TAHAPAN PENELITIAN KLASIFIKASI SAMPAH CITRA DIGITAL", 
            ha='center', va='center', fontsize=13, fontweight='bold', color='#FFFFFF', family='sans-serif')
    ax.text(50, 94.6, "Ekstraksi Fitur Multidomain (Warna, Bentuk, Tekstur) & Algoritma K-Nearest Neighbor (KNN)", 
            ha='center', va='center', fontsize=9.5, fontweight='normal', color='#94A3B8', family='sans-serif')

    # -------------------------------------------------------------
    # TAHAP 1: AKUISISI & DATASET CITRA (y: 81.5 - 91.5)
    # -------------------------------------------------------------
    draw_rounded_box(ax, 5, 81.0, 90, 10.5, bg_color=c_stage_bg, border_color='#93C5FD', lw=1.5)
    
    # Badge Tahap 1
    draw_rounded_box(ax, 7, 88.8, 22, 2.2, bg_color='#EFF6FF', border_color='#3B82F6', radius=0.5, lw=1.2)
    ax.text(18, 89.9, "TAHAP 1: AKUISISI DATASET", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1D4ED8')
    
    ax.text(32, 89.9, "Korpus 2.395 Citra Digital (5 Kategori Sampah Anorganik: 80% Latih / 20% Uji)", 
            ha='left', va='center', fontsize=8.5, fontweight='bold', color=c_dark_text)

    # Sample images thumbnails
    sample_files = [
        ('sampah botol kaca.jpeg', 'Botol Kaca\n(502 sampel)'),
        ('sampah botol plastik.jpeg', 'Botol Plastik\n(483 sampel)'),
        ('sampah kaleng.jpg', 'Kaleng Logam\n(411 sampel)'),
        ('sampah kardus.jpeg', 'Kardus\n(404 sampel)'),
        ('sampah kertas.jpg', 'Kertas\n(595 sampel)')
    ]
    x_positions = [14, 32, 50, 68, 86]
    for (img_f, lbl), x_p in zip(sample_files, x_positions):
        try:
            im = cv2.imread(img_f)
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            im = cv2.resize(im, (100, 100))
            imagebox = OffsetImage(im, zoom=0.28)
            ab = AnnotationBbox(imagebox, (x_p, 85.3), frameon=True,
                                bboxprops=dict(edgecolor='#CBD5E1', linewidth=1.2, boxstyle="round,pad=0.1"))
            ax.add_artist(ab)
        except Exception as e:
            pass
        ax.text(x_p, 82.2, lbl, ha='center', va='center', fontsize=7.2, fontweight='bold', color=c_muted_text)

    # Panah Tahap 1 -> Tahap 2
    draw_arrow(ax, 50, 81.0, 50, 77.5, color='#3B82F6', lw=2.2)

    # -------------------------------------------------------------
    # TAHAP 2: PRA-PEMROSESAN & SEGMENTASI ADAPTIF (y: 63.5 - 77.2)
    # -------------------------------------------------------------
    draw_rounded_box(ax, 5, 63.5, 90, 13.7, bg_color=c_stage_bg, border_color='#A7F3D0', lw=1.5)

    # Badge Tahap 2
    draw_rounded_box(ax, 7, 74.5, 33, 2.2, bg_color='#ECFDF5', border_color='#10B981', radius=0.5, lw=1.2)
    ax.text(23.5, 75.6, "TAHAP 2: PRA-PEMROSESAN & SEGMENTASI", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#047857')

    # Visualisasi proses percontohan menggunakan gambar kaleng
    try:
        sample_img = cv2.imread('sampah kaleng.jpg')
        im_res, im_gray, im_mask = preprocess_image(sample_img)
        im_res_rgb = cv2.cvtColor(im_res, cv2.COLOR_BGR2RGB)
        im_masked = cv2.bitwise_and(im_res_rgb, im_res_rgb, mask=im_mask)
        im_mask_rgb = cv2.cvtColor(im_mask, cv2.COLOR_GRAY2RGB)

        proc_steps = [
            (im_res_rgb, "1. Resize 256×256\n& Gaussian Filter (5×5)"),
            (im_mask_rgb, "2. Binerisasi Otsu &\nKoreksi Orientasi Tepi"),
            (im_masked, "3. Operasi Morfologi &\nMasker Objek Terpilih (ROI)")
        ]
        proc_x = [18, 35, 52]
        for (img_data, cap), px in zip(proc_steps, proc_x):
            ib = OffsetImage(img_data, zoom=0.23)
            ab = AnnotationBbox(ib, (px, 69.2), frameon=True,
                                bboxprops=dict(edgecolor='#CBD5E1', linewidth=1.2, boxstyle="round,pad=0.1"))
            ax.add_artist(ab)
            ax.text(px, 65.0, cap, ha='center', va='center', fontsize=6.8, fontweight='bold', color=c_dark_text)

        draw_arrow(ax, 23.5, 69.2, 29.5, 69.2, color='#10B981', lw=1.5)
        draw_arrow(ax, 40.5, 69.2, 46.5, 69.2, color='#10B981', lw=1.5)
    except Exception as e:
        pass

    # Deskripsi detail teknis di sebelah kanan
    draw_rounded_box(ax, 62, 64.7, 31, 8.5, bg_color='#F8FAFC', border_color='#E2E8F0', radius=0.6, lw=1.0)
    ax.text(63.5, 71.8, "Spesifikasi Pra-Pemrosesan:", ha='left', va='center', fontsize=7.8, fontweight='bold', color='#0F172A')
    desc_t2 = (
        "• Resolusi Spasial: Standar seragam 256×256 piksel\n"
        "• Reduksi Derau: Gaussian Blur (kernel 5×5, σ=0)\n"
        "• Otsu Thresholding: Binerisasi adaptif otomatis\n"
        "• Border Correction: Balik masker jika tepi > 50% putih\n"
        "• Morfologi: Closing & Opening (struktur 5×5)\n"
        "• ROI Mask: Kontur terluar dengan area terbesar"
    )
    ax.text(63.5, 67.8, desc_t2, ha='left', va='center', fontsize=6.8, color=c_muted_text, linespacing=1.25)

    # Panah Tahap 2 -> Tahap 3
    draw_arrow(ax, 50, 63.5, 50, 60.0, color='#10B981', lw=2.2)

    # -------------------------------------------------------------
    # TAHAP 3: EKSTRAKSI FITUR MULTIDOMAIN (49 Dimensi) (y: 35.5 - 59.8)
    # -------------------------------------------------------------
    draw_rounded_box(ax, 5, 35.5, 90, 24.3, bg_color=c_stage_bg, border_color='#FED7AA', lw=1.5)

    # Badge Tahap 3
    draw_rounded_box(ax, 7, 57.0, 36, 2.2, bg_color='#FFF7ED', border_color='#F97316', radius=0.5, lw=1.2)
    ax.text(25, 58.1, "TAHAP 3: EKSTRAKSI FITUR MULTIDOMAIN (49D)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#C2410C')

    # Sub-box 1: Warna (38 Fitur)
    draw_rounded_box(ax, 8, 37.0, 26, 18.5, bg_color='#FFFBEB', border_color='#FCD34D', radius=0.8, lw=1.2)
    draw_rounded_box(ax, 9.5, 52.8, 23, 2.0, bg_color='#FEF3C7', border_color='#F59E0B', radius=0.4, lw=1.0)
    ax.text(21, 53.8, "1. Fitur Warna (38 Fitur)", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#B45309')
    
    txt_c = (
        "• Kuantisasi Histogram HSV:\n"
        "  - 16 bin Hue (rentang 0-180)\n"
        "  - 8 bin Saturation (0-256)\n"
        "  - 8 bin Value (0-256)\n"
        "  - Total: 32 bin ternormalisasi L1\n"
        "  * Dihitung murni pada piksel\n"
        "    masker objek (abaikan latar)\n\n"
        "• Momen Statistik CIE-LAB:\n"
        "  - Rata-rata (Mean) L*, a*, b*\n"
        "  - Standar Deviasi (Std) L*, a*, b*\n"
        "  - Total: 6 parameter warna"
    )
    ax.text(9.5, 45.2, txt_c, ha='left', va='center', fontsize=6.8, color='#78350F', linespacing=1.2)

    # Sub-box 2: Bentuk Morfometri (5 Fitur)
    draw_rounded_box(ax, 37, 37.0, 26, 18.5, bg_color='#F0FDF4', border_color='#86EFAC', radius=0.8, lw=1.2)
    draw_rounded_box(ax, 38.5, 52.8, 23, 2.0, bg_color='#DCFCE7', border_color='#22C55E', radius=0.4, lw=1.0)
    ax.text(50, 53.8, "2. Morfometri Bentuk (5 Fitur)", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#15803D')
    
    txt_s = (
        "• Deskriptor Geometri Kontur:\n"
        "  - Normalized Area:\n"
        "    A_norm = Area / (256 × 256)\n"
        "  - Normalized Perimeter:\n"
        "    P_norm = Perimeter / 256\n"
        "  - Circularity (Kebundaran):\n"
        "    C = 4π × Area / Perimeter²\n"
        "  - Aspect Ratio (Rasio Dimensi):\n"
        "    AR = Lebar / Tinggi\n"
        "  - Solidity (Kepadatan Convex):\n"
        "    S = Area / Area_ConvexHull\n\n"
        "  * Membedakan botol/kaleng silinder\n"
        "    terhadap lembaran kertas/kardus"
    )
    ax.text(38.5, 45.2, txt_s, ha='left', va='center', fontsize=6.8, color='#14532D', linespacing=1.2)

    # Sub-box 3: Tekstur & Edge (6 Fitur)
    draw_rounded_box(ax, 66, 37.0, 26, 18.5, bg_color='#F5F3FF', border_color='#C4B5FD', radius=0.8, lw=1.2)
    draw_rounded_box(ax, 67.5, 52.8, 23, 2.0, bg_color='#EDE9FE', border_color='#8B5CF6', radius=0.4, lw=1.0)
    ax.text(79, 53.8, "3. Tekstur & Edge (6 Fitur)", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#6D28D9')
    
    txt_t = (
        "• Haralick GLCM (5 Fitur):\n"
        "  - Jarak piksel d ∈ {1, 2}\n"
        "  - Sudut θ ∈ {0°, 90°}\n"
        "  - Kontras (Contrast)\n"
        "  - Disimilaritas (Dissimilarity)\n"
        "  - Homogenitas (Homogeneity)\n"
        "  - Energi (Energy / ASM)\n"
        "  - Korelasi (Correlation)\n\n"
        "• Kerapatan Tepi Canny (1 Fitur):\n"
        "  - Ambang histeresis 40 / 120\n"
        "  - Rasio piksel tepi pada objek\n"
        "  * Membedakan kerutan kertas/kaleng"
    )
    ax.text(67.5, 45.2, txt_t, ha='left', va='center', fontsize=6.8, color='#4C1D95', linespacing=1.2)

    # Panah Gabungan dari 3 Sub-box ke Penskalaan
    draw_arrow(ax, 21, 37.0, 48, 32.5, color='#F59E0B', lw=1.5)
    draw_arrow(ax, 50, 37.0, 50, 32.5, color='#22C55E', lw=1.5)
    draw_arrow(ax, 79, 37.0, 52, 32.5, color='#8B5CF6', lw=1.5)

    # -------------------------------------------------------------
    # TAHAP 4: PENSKALAAN & KLASIFIKASI KNN (y: 18.0 - 32.0)
    # -------------------------------------------------------------
    draw_rounded_box(ax, 5, 18.0, 90, 14.0, bg_color=c_stage_bg, border_color='#DDD6FE', lw=1.5)

    # Badge Tahap 4
    draw_rounded_box(ax, 7, 29.3, 34, 2.2, bg_color='#F5F3FF', border_color='#7C3AED', radius=0.5, lw=1.2)
    ax.text(24, 30.4, "TAHAP 4: PENSKALAAN & INFERENSI KNN", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#6D28D9')

    # Box Penskalaan StandardScaler
    draw_rounded_box(ax, 8, 19.5, 38, 8.8, bg_color='#FAF5FF', border_color='#C084FC', radius=0.6, lw=1.0)
    ax.text(27, 26.8, "Standardisasi Vektor Fitur (StandardScaler)", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#6B21A8')
    txt_sc = (
        "• Penggabungan: Vektor numerik terpadu 1×49\n"
        "• Transformasi Skor Baku: z = (x - μ) / σ\n"
        "• Fungsi: Menghilangkan bias antar-skala fitur\n"
        "  (misal luas ribuan piksel vs kebundaran desimal)\n"
        "• Parameter skaler disimpan ke scaler.pkl"
    )
    ax.text(9.5, 23.0, txt_sc, ha='left', va='center', fontsize=6.8, color='#581C87', linespacing=1.2)

    # Panah StandardScaler -> Model KNN
    draw_arrow(ax, 46.5, 23.9, 52.5, 23.9, color='#7C3AED', lw=2.0)

    # Box Model K-Nearest Neighbor
    draw_rounded_box(ax, 53, 19.5, 40, 8.8, bg_color='#EEF2FF', border_color='#818CF8', radius=0.6, lw=1.0)
    ax.text(73, 26.8, "Klasifikasi K-Nearest Neighbor (KNN)", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#3730A3')
    txt_knn = (
        "• Hyperparameter Optimal: k = 5 tetangga terdekat\n"
        "• Metrik Jarak: Manhattan L1-norm D(x,y) = ∑|xi - yi|\n"
        "  (lebih tangguh thd dimensi tinggi dibanding L2)\n"
        "• Voting: Pembobotan jarak w = 1 / (d + ε)\n"
        "• Model disimpan ke berkas knn_model.pkl (<4.2 MB)"
    )
    ax.text(54.5, 23.0, txt_knn, ha='left', va='center', fontsize=6.8, color='#312E81', linespacing=1.2)

    # Panah Tahap 4 -> Tahap 5
    draw_arrow(ax, 73, 19.5, 73, 15.0, color='#6366F1', lw=2.2)

    # -------------------------------------------------------------
    # TAHAP 5: KELUARAN & IMPLEMENTASI SISTEM (y: 2.5 - 14.5)
    # -------------------------------------------------------------
    draw_rounded_box(ax, 5, 2.5, 90, 12.0, bg_color=c_stage_bg, border_color='#BAE6FD', lw=1.5)

    # Badge Tahap 5
    draw_rounded_box(ax, 7, 11.8, 30, 2.2, bg_color='#F0F9FF', border_color='#0284C7', radius=0.5, lw=1.2)
    ax.text(22, 12.9, "TAHAP 5: EVALUASI & DEPLOYMENT", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#0369A1')

    # Evaluasi Hasil
    draw_rounded_box(ax, 8, 3.8, 41, 7.2, bg_color='#F0FDF4', border_color='#4ADE80', radius=0.5, lw=1.0)
    ax.text(28.5, 9.3, "Evaluasi Kinerja Pengujian (Test Set)", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#15803D')
    txt_res = (
        "• Akurasi Keseluruhan: 91,67% (440 dari 480 sampel uji benar)\n"
        "• F1-Score Tertinggi: Botol Kaca (94,12%) & Kardus (92,77%)\n"
        "• Rata-rata Makro: Presisi 91,52%, Recall 91,71%, F1 91,60%\n"
        "• Total Waktu Inferensi: 57,3 ms per citra (~17 frame/detik)"
    )
    ax.text(9.5, 6.4, txt_res, ha='left', va='center', fontsize=6.8, color='#14532D', linespacing=1.2)

    # Implementasi Perangkat Lunak
    draw_rounded_box(ax, 52, 3.8, 41, 7.2, bg_color='#EFF6FF', border_color='#60A5FA', radius=0.5, lw=1.0)
    ax.text(72.5, 9.3, "Integrasi Antarmuka Sistem (Deployment)", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#1D4ED8')
    txt_dep = (
        "• Aplikasi Web Interaktif Streamlit (app.py)\n"
        "• Mode 1: Unggah Citra Digital & Visualisasi Masker/Fitur\n"
        "• Mode 2: Pemindaian Kamera Langsung (Webcam Real-Time)\n"
        "• Ringan Komputasi, Siap Dipasang pada Perangkat CPU/Edge"
    )
    ax.text(53.5, 6.4, txt_dep, ha='left', va='center', fontsize=6.8, color='#1E40AF', linespacing=1.2)

    # Simpan gambar beresolusi tinggi 300 DPI
    output_png = 'figure1_metodologi.png'
    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[BERHASIL] Gambar {output_png} berhasil dibuat dengan resolusi 300 DPI!")

if __name__ == '__main__':
    create_figure1()
