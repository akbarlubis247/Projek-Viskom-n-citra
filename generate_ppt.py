import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # Palet Warna Modern
    COLOR_BG_DARK = RGBColor(15, 23, 42)      # #0F172A (Deep Slate)
    COLOR_BG_LIGHT = RGBColor(248, 250, 252)  # #F8FAFC (Light Slate)
    COLOR_WHITE = RGBColor(255, 255, 255)
    COLOR_PRIMARY = RGBColor(14, 165, 233)    # #0EA5E9 (Sky Blue)
    COLOR_ACCENT = RGBColor(16, 185, 129)     # #10B981 (Emerald Green)
    COLOR_DARK_TEXT = RGBColor(30, 41, 59)    # #1E293B (Slate 800)
    COLOR_MUTED_TEXT = RGBColor(100, 116, 139)# #64748B (Slate 500)
    COLOR_CARD_BORDER = RGBColor(226, 232, 240)# #E2E8F0
    COLOR_CARD_BG = RGBColor(255, 255, 255)
    COLOR_CARD_HEADER = RGBColor(241, 245, 249)

    def set_slide_background(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, title_text, category_text="VISUALISASI KOMPUTER DAN PEMROSESAN CITRA"):
        # Category / Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_PRIMARY
        
        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_DARK_TEXT

    def add_card(slide, left, top, width, height, bg_color=COLOR_WHITE, border_color=COLOR_CARD_BORDER):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        if border_color:
            shape.line.color.rgb = border_color
            shape.line.width = Pt(1.5)
        else:
            shape.line.fill.background()
        return shape

    # ==========================================================
    # SLIDE 1: TITLE SLIDE (DARK THEME)
    # ==========================================================
    slide1 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide1, COLOR_BG_DARK)

    # Accent decorative bar
    bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.5), Inches(0.8), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_ACCENT
    bar.line.fill.background()

    # Tag / Course
    box = slide1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(0.5))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = "PROYEK AKHIR MATA KULIAH: VISUALISASI KOMPUTER DAN PEMROSESAN CITRA"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    # Title
    box = slide1.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(11.3), Inches(2.2))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Klasifikasi Jenis Sampah Berdasarkan Citra Digital"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    
    p2 = tf.add_paragraph()
    p2.text = "Menggunakan Ekstraksi Fitur Multi-Domain & K-Nearest Neighbor (KNN)"
    p2.font.size = Pt(24)
    p2.font.bold = False
    p2.font.color.rgb = COLOR_ACCENT
    p2.space_before = Pt(8)

    # Team & Institution Info Card
    card1 = add_card(slide1, Inches(1.0), Inches(5.2), Inches(11.3), Inches(1.5), bg_color=RGBColor(30, 41, 59), border_color=RGBColor(51, 65, 85))
    box = slide1.shapes.add_textbox(Inches(1.3), Inches(5.4), Inches(10.7), Inches(1.1))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Disusun Oleh : Muhammad Akbar Rafli Lubis & Tim Mahasiswa"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    
    p = tf.add_paragraph()
    p.text = "Program Studi Teknologi Rekayasa Perangkat Lunak | Sekolah Vokasi | Institut Pertanian Bogor"
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.space_before = Pt(4)

    # ==========================================================
    # SLIDE 2: LATAR BELAKANG & MASALAH
    # ==========================================================
    slide2 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide2, COLOR_BG_LIGHT)
    add_header(slide2, "Latar Belakang: Urgensi Pemilahan Sampah Presisi")

    card_w = Inches(3.64)
    card_h = Inches(5.0)
    top_pos = Inches(1.7)

    # Card 1: Problem Sampah
    add_card(slide2, Inches(0.8), top_pos, card_w, card_h)
    box = slide2.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.2), card_w - Inches(0.4), card_h - Inches(0.4))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "1. Timbulan Sampah Padat"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT
    
    bullets = [
        "Pemisahan biner (organik vs anorganik) sudah tidak memadai untuk industri daur ulang modern.",
        "Setiap material anorganik memerlukan jalur daur ulang yang spesifik (peleburan kaca, pencacahan plastik, pengolahan pulp kardus, pemurnian kaleng).",
        "Ketidakteraturan pemilahan menurunkan nilai ekonomis material daur ulang secara drastis."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(10)

    # Card 2: Limitasi Pemilahan Manual
    add_card(slide2, Inches(4.84), top_pos, card_w, card_h)
    box = slide2.shapes.add_textbox(Inches(5.04), top_pos + Inches(0.2), card_w - Inches(0.4), card_h - Inches(0.4))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "2. Limitasi Metode Manual"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    bullets = [
        "Throughput Rendah: Kecepatan pemilahan oleh tenaga manusia di bank sampah sangat terbatas.",
        "Human Error & Kelelahan: Menurunnya konsistensi pemilahan akibat kelelahan visual operator.",
        "Risiko Kesehatan & Keselamatan: Bahaya paparan mikroba/patogen dan cidera benda tajam (pecahan kaca, tepi kaleng)."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(10)

    # Card 3: Solusi Visi Komputer
    add_card(slide2, Inches(8.88), top_pos, card_w, card_h)
    box = slide2.shapes.add_textbox(Inches(9.08), top_pos + Inches(0.2), card_w - Inches(0.4), card_h - Inches(0.4))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "3. Solusi Computer Vision"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    bullets = [
        "Otomatisasi Cepat: Mampu mengenali jenis material dalam hitungan milidetik secara objektif.",
        "Karakteristik Fisik Unik: Warna, reflektansi cahaya, kebundaran bentuk, dan tekstur permukaan dapat dimodelkan matematis.",
        "Siap Terap: Dapat diintegrasikan ke konveyor pintar, web app, maupun perangkat IoT bank sampah mandiri."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(10)

    # ==========================================================
    # SLIDE 3: PENDEKATAN KAMI VS DEEP LEARNING (MENGAPA KNN & FITUR MANUAL?)
    # ==========================================================
    slide3 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide3, COLOR_BG_LIGHT)
    add_header(slide3, "Rasional Desain: Mengapa Ekstraksi Fitur & KNN?")

    # Card Kiri: Deep Learning
    add_card(slide3, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide3.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "❌ Pendekatan Deep Learning (CNN)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = RGBColor(225, 29, 72) # Red/Rose

    dl_points = [
        ("Komputasi Tinggi: ", "Memerlukan kartu grafis (GPU) mahal dan daya listrik besar."),
        ("Kebutuhan Data Masif: ", "Membutuhkan ribuan hingga puluhan ribu citra agar tidak overfitting."),
        ("Black-Box (Kotak Hitam): ", "Keputusan klasifikasi sulit diinterpretasikan parameter fisisnya secara langsung."),
        ("Deploy Lambat di Edge: ", "Ukuran model puluhan hingga ratusan megabyte, latensi tinggi di web/IoT murah.")
    ]
    for title, desc in dl_points:
        p = tf.add_paragraph()
        p.text = "• " + title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(10)
        run = p.add_run(); run.text = desc
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # Card Kanan: Handcrafted + KNN (Solusi Kami)
    add_card(slide3, Inches(6.9), Inches(1.7), Inches(5.6), Inches(5.1), border_color=COLOR_ACCENT)
    box = slide3.shapes.add_textbox(Inches(7.2), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "✅ Handcrafted Features + KNN (Solusi Kami)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT

    our_points = [
        ("Ringan & Efisien: ", "Ukuran artefak model < 5 MB, dapat berjalan mulus pada CPU standar tanpa GPU."),
        ("Transparansi Matematis: ", "Fitur warna, morfometri, dan tekstur GLCM memiliki makna fisis terukur."),
        ("Inferensi Waktu-Nyata: ", "Waktu prediksi sangat cepat (< 0.05 detik per citra), responsif di browser web."),
        ("Akurasi Kompetitif: ", "Mampu memisahkan 5 kategori material dengan akurasi 91.67% pada data uji.")
    ]
    for title, desc in our_points:
        p = tf.add_paragraph()
        p.text = "• " + title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(10)
        run = p.add_run(); run.text = desc
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # ==========================================================
    # SLIDE 4: TUJUAN DAN RUANG LINGKUP PENELITIAN
    # ==========================================================
    slide4 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide4, COLOR_BG_LIGHT)
    add_header(slide4, "Tujuan Penelitian & Ruang Lingkup Proyek")

    # 4 Bar horizontal / Cards
    items = [
        ("1. Pipeline Segmentasi Citra Adaptif", "Mengembangkan alur pra-pemrosesan citra digital dengan Otsu Thresholding dan Gaussian Adaptive Filtering untuk mengisolasi objek sampah secara bersih.", COLOR_PRIMARY),
        ("2. Ekstraksi Fitur Multi-Domain Terpadu", "Mengekstrak 48 fitur gabungan yang mencakup ruang warna (HSV & LAB), morfometri bentuk geometris, serta tekstur GLCM dan kerapatan tepi Canny.", COLOR_ACCENT),
        ("3. Klasifikasi K-Nearest Neighbor Teroptimasi", "Melatih model KNN terstandardisasi dengan metrik jarak Manhattan (L1-norm) dan pembobotan jarak (distance-weighted) untuk memprediksi 5 kelas material.", COLOR_PRIMARY),
        ("4. Deployment Aplikasi Web Interaktif", "Mengintegrasikan sistem ke dalam antarmuka berbasis web (Streamlit) yang menampilkan visualisasi proses segmentasi, nilai vektor fitur, dan probabilitas kelas secara real-time.", COLOR_ACCENT)
    ]

    for idx, (title, desc, accent) in enumerate(items):
        top_c = Inches(1.7 + idx * 1.3)
        add_card(slide4, Inches(0.8), top_c, Inches(11.7), Inches(1.1))
        
        # Indicator strip
        strip = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top_c, Inches(0.15), Inches(1.1))
        strip.fill.solid()
        strip.fill.fore_color.rgb = accent
        strip.line.fill.background()

        box = slide4.shapes.add_textbox(Inches(1.2), top_c + Inches(0.12), Inches(11.1), Inches(0.85))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        
        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(3)

    # ==========================================================
    # SLIDE 5: DATASET & 5 KELAS MATERIAL SAMPAH
    # ==========================================================
    slide5 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide5, COLOR_BG_LIGHT)
    add_header(slide5, "Dataset: 5 Kategori Material Sampah Padat")

    classes_info = [
        ("Botol Kaca", "sampah botol kaca.jpeg", "Permukaan licin, pantulan spekular, bentuk leher botol."),
        ("Botol Plastik", "sampah botol plastik.jpeg", "Material tembus pandang/berwarna, elongasi vertikal."),
        ("Kaleng Logam", "sampah kaleng.jpg", "Bentuk silinder kompak, circularity tinggi, tekstur metalik."),
        ("Kardus", "sampah kardus.jpeg", "Tekstur serat teratur (GLCM), warna cokelat LAB khas, sudut tegas."),
        ("Kertas", "sampah kertas.jpg", "Kerapatan tepi tinggi akibat lipatan/remukan, intensitas terang.")
    ]

    item_w = Inches(2.2)
    item_h = Inches(5.1)
    for idx, (name, img_file, desc) in enumerate(classes_info):
        left_pos = Inches(0.8 + idx * 2.38)
        add_card(slide5, left_pos, Inches(1.7), item_w, item_h)
        
        # Header text
        box = slide5.shapes.add_textbox(left_pos + Inches(0.1), Inches(1.85), item_w - Inches(0.2), Inches(0.4))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = name
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT

        # Image if available
        if os.path.exists(img_file):
            slide5.shapes.add_picture(img_file, left_pos + Inches(0.2), Inches(2.3), item_w - Inches(0.4), Inches(2.1))
        
        # Description
        box = slide5.shapes.add_textbox(left_pos + Inches(0.15), Inches(4.55), item_w - Inches(0.3), Inches(2.1))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = desc
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_MUTED_TEXT

    # ==========================================================
    # SLIDE 6: ARSITEKTUR & DIAGRAM ALIR SISTEM (PIPELINE)
    # ==========================================================
    slide6 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide6, COLOR_BG_LIGHT)
    add_header(slide6, "Arsitektur Sistem & Diagram Alir Pemrosesan")

    steps = [
        ("Tahap 1", "Citra Input", "Akuisisi citra sampah RGB digital dari user/kamera"),
        ("Tahap 2", "Pra-pemrosesan", "Resize 256x256, Gaussian Blur 5x5, Grayscale"),
        ("Tahap 3", "Segmentasi", "Otsu & Adaptive Thresholding, Morfologi Closing, Kontur ROI"),
        ("Tahap 4", "Ekstraksi Fitur", "Warna (HSV & LAB), Bentuk Morfometri, Tekstur GLCM & Tepi"),
        ("Tahap 5", "Penskalaan", "StandardScaler (z-score normalisation ke 48 fitur)"),
        ("Tahap 6", "Klasifikasi KNN", "k=3, Manhattan Distance, Distance-Weighted Voting")
    ]

    card_s_w = Inches(3.64)
    card_s_h = Inches(2.35)

    # Row 1 (Steps 1, 2, 3)
    for idx, (stage, title, desc) in enumerate(steps[:3]):
        left_p = Inches(0.8 + idx * 4.04)
        top_p = Inches(1.7)
        add_card(slide6, left_p, top_p, card_s_w, card_s_h)
        
        box = slide6.shapes.add_textbox(left_p + Inches(0.2), top_p + Inches(0.2), card_s_w - Inches(0.4), card_s_h - Inches(0.4))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = stage.upper()
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY

        p = tf.add_paragraph()
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(2)

        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(6)

    # Row 2 (Steps 4, 5, 6)
    for idx, (stage, title, desc) in enumerate(steps[3:]):
        left_p = Inches(0.8 + idx * 4.04)
        top_p = Inches(4.35)
        add_card(slide6, left_p, top_p, card_s_w, card_s_h)

        box = slide6.shapes.add_textbox(left_p + Inches(0.2), top_p + Inches(0.2), card_s_w - Inches(0.4), card_s_h - Inches(0.4))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = stage.upper()
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_ACCENT

        p = tf.add_paragraph()
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(2)

        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(6)

    # ==========================================================
    # SLIDE 7: PRA-PEMROSESAN CITRA DIGITAL (PREPROCESSING)
    # ==========================================================
    slide7 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide7, COLOR_BG_LIGHT)
    add_header(slide7, "Tahap 1: Pra-Pemrosesan Citra Digital (Preprocessing)")

    pre_items = [
        ("1. Penyelarasan Resolusi Spasial (Resizing)", 
         "Penskalaan ke Dimensi 256 × 256 Piksel",
         "Menyeragamkan seluruh input citra yang berasal dari beragam kamera beresolusi berbeda menggunakan interpolasi bilinear. Penyeragaman ini memastikan konsistensi ekstraksi fitur berbasis spasial seperti area, keliling, dan histogram."),
        ("2. Reduksi Derau Frekuensi Tinggi (Gaussian Blur)",
         "Filter Konvolusi Spasial Kernel 5 × 5",
         "Menghaluskan derau bintik (noise) sensor dan fluktuasi intensitas lokal tanpa mengorbankan batas kontur utama objek. Menghasilkan gradien intensitas yang stabil untuk binerisasi."),
        ("3. Transformasi Ruang Warna Aras Keabuan",
         "Konversi BGR ke Skala Keabuan (Grayscale)",
         "Mereduksi kompleksitas 3 kanal warna menjadi 1 kanal intensitas luminansi berbobot (Y = 0.299R + 0.587G + 0.114B) untuk keperluan segmentasi ambang biner dan perhitungan matriks GLCM.")
    ]

    for idx, (tag, title, desc) in enumerate(pre_items):
        top_c = Inches(1.7 + idx * 1.7)
        add_card(slide7, Inches(0.8), top_c, Inches(11.7), Inches(1.45))
        
        box = slide7.shapes.add_textbox(Inches(1.2), top_c + Inches(0.15), Inches(11.0), Inches(1.15))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY

        p = tf.add_paragraph()
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(2)

        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(4)

    # ==========================================================
    # SLIDE 8: SEGMENTASI OBJEK & OPERASI MORFOLOGI
    # ==========================================================
    slide8 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide8, COLOR_BG_LIGHT)
    add_header(slide8, "Tahap 2: Segmentasi Citra & Morfologi Matematis")

    # Card Kiri: Otsu & Adaptive
    add_card(slide8, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide8.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Binerisasi Adaptif (Otsu & Adaptive)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    p = tf.add_paragraph()
    p.text = "• Otsu Thresholding Otomatis:"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_before = Pt(8)
    p = tf.add_paragraph()
    p.text = "Menghitung nilai ambang optimal secara otomatis dengan memaksimalkan variansi antarkelas (inter-class variance) antara foreground (objek sampah) dan background."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT

    p = tf.add_paragraph()
    p.text = "• Mekanisme Fallback Adaptif:"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_before = Pt(10)
    p = tf.add_paragraph()
    p.text = "Jika rasio piksel biner > 85% atau < 5% (akibat pencahayaan terlalu gelap atau silau ekstrem), sistem otomatis beralih ke Gaussian Adaptive Thresholding (blok 15x15, C=2) untuk mengisolasi tepi objek."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT

    # Card Kanan: Morfologi & Deteksi Kontur
    add_card(slide8, Inches(6.9), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide8.shapes.add_textbox(Inches(7.2), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Operasi Morfologi & Ekstraksi Masker"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    p = tf.add_paragraph()
    p.text = "• Morfologi Closing (Penutupan):"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT
    p.space_before = Pt(8)
    p = tf.add_paragraph()
    p.text = "Menerapkan operasi dilasi diikuti erosi dengan elemen penstruktur persegi (structuring element 5 × 5). Berfungsi menyatukan komponen objek yang terputus serta menutup lubang-lubang kecil."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT

    p = tf.add_paragraph()
    p.text = "• Seleksi Kontur Eksternal Terbesar (ROI):"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT
    p.space_before = Pt(10)
    p = tf.add_paragraph()
    p.text = "Mengeliminasi bintik noise di latar belakang dengan mencari seluruh kontur tertutup (cv2.findContours) dan hanya mengambil kontur dengan luas area maksimum sebagai masker biner tunggal."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT

    # ==========================================================
    # SLIDE 9: EKSTRAKSI FITUR MULTI-DOMAIN (BAGIAN 1: WARNA)
    # ==========================================================
    slide9 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide9, COLOR_BG_LIGHT)
    add_header(slide9, "Ekstraksi Fitur Multi-Domain: Ruang Warna HSV & CIE-LAB")

    # Card Kiri: HSV Histogram
    add_card(slide9, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide9.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Histogram Kuantisasi HSV (32 Fitur)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    p = tf.add_paragraph()
    p.text = "Mengapa ruang warna HSV?"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_before = Pt(6)
    p = tf.add_paragraph()
    p.text = "Ruang warna HSV memisahkan informasi warna murni (Hue) dari intensitas penerangan (Value), sehingga sangat tangguh terhadap bayangan dan variasi pencahayaan."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT

    hsv_details = [
        ("Hue Histogram (16 bin): ", "Menangkap spektrum corak warna (misal: botol kaca hijau vs kardus cokelat)."),
        ("Saturation Histogram (8 bin): ", "Mengukur kemurnian dan kepekatan saturasi warna objek."),
        ("Value Histogram (8 bin): ", "Mengukur tingkat kecerahan objek (membedakan kertas putih terang vs kaleng gelap)."),
        ("Normalisasi: ", "Setiap bin dibagi dengan total piksel (256 × 256) agar independen dari ukuran.")
    ]
    for t, d in hsv_details:
        p = tf.add_paragraph()
        p.text = "• " + t
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(4)
        run = p.add_run(); run.text = d
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # Card Kanan: LAB Color Moments
    add_card(slide9, Inches(6.9), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide9.shapes.add_textbox(Inches(7.2), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Momen Warna CIE-LAB (6 Fitur)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    p = tf.add_paragraph()
    p.text = "Persepsi Visual Mendekati Mata Manusia"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT
    p.space_before = Pt(6)
    p = tf.add_paragraph()
    p.text = "Ruang warna CIE-LAB dirancang berdasarkan teori persepsi visual manusia (perceptually uniform), di mana jarak antarwarna mencerminkan perbedaan yang dilihat mata manusia."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT

    lab_details = [
        ("L* (Lightness): ", "Tingkat terang-gelap (0 = hitam pekat, 100 = putih bersih)."),
        ("a* (Green-Red): ", "Poros spektrum antara warna hijau hingga merah."),
        ("b* (Blue-Yellow): ", "Poros spektrum antara warna biru hingga kuning."),
        ("Statistik yang Diekstrak: ", "Nilai rata-rata (μ) dan standar deviasi (σ) dari masing-masing kanal L*, a*, b* (3 kanal × 2 statistik = 6 fitur).")
    ]
    for t, d in lab_details:
        p = tf.add_paragraph()
        p.text = "• " + t
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(4)
        run = p.add_run(); run.text = d
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # ==========================================================
    # SLIDE 10: EKSTRAKSI FITUR MULTI-DOMAIN (BAGIAN 2: BENTUK & TEKSTUR)
    # ==========================================================
    slide10 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide10, COLOR_BG_LIGHT)
    add_header(slide10, "Ekstraksi Fitur Multi-Domain: Morfometri Bentuk, GLCM & Tepi")

    # Card Kiri: Morfometri Bentuk
    add_card(slide10, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide10.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "📐 Fitur Bentuk Morfometri (5 Fitur)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    shape_items = [
        ("Normalized Area: ", "A_norm = Area / (256 × 256), rasio besaran luas objek."),
        ("Normalized Perimeter: ", "P_norm = Keliling / 256, panjang garis keliling kontur."),
        ("Circularity (Kebundaran): ", "C = (4π × Luas) / Keliling². Nilai mendekati 1 untuk lingkaran (kaleng/tutup botol), lebih kecil untuk kardus persegi."),
        ("Aspect Ratio: ", "AR = Lebar / Tinggi dari bounding box kontur."),
        ("Solidity: ", "S = Luas Kontur / Luas Convex Hull. Mengukur kekompakan tepi objek (botol utuh bernilai tinggi, sampah kertas lecek bernilai rendah).")
    ]
    for t, d in shape_items:
        p = tf.add_paragraph()
        p.text = "• " + t
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(6)
        run = p.add_run(); run.text = d
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # Card Kanan: Tekstur GLCM & Canny
    add_card(slide10, Inches(6.9), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide10.shapes.add_textbox(Inches(7.2), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🧱 Tekstur GLCM & Edge Density (6 Fitur)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    tex_items = [
        ("Gray-Level Co-occurrence Matrix (GLCM): ", "Dihitung pada jarak d ∈ {1, 2} dan sudut θ ∈ {0°, 90°} aras 256 aras keabuan."),
        ("Contrast & Dissimilarity: ", "Mengukur intensitas perbedaan lokal antar-piksel bertetangga."),
        ("Homogeneity: ", "Mengukur keseragaman permukaan (botol kaca licin bernilai homogenitas tinggi)."),
        ("Energy & Correlation: ", "Mengukur keteraturan tekstur dan linearitas spasial piksel."),
        ("Canny Edge Density: ", "Rasio piksel tepi terhadap total citra. Membedakan kertas/kaleng kusut yang memiliki banyak lipatan tajam vs kaca yang licin.")
    ]
    for t, d in tex_items:
        p = tf.add_paragraph()
        p.text = "• " + t
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(6)
        run = p.add_run(); run.text = d
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # ==========================================================
    # SLIDE 11: KLASIFIKASI K-NEAREST NEIGHBOR (KNN)
    # ==========================================================
    slide11 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide11, COLOR_BG_LIGHT)
    add_header(slide11, "Tahap 4: Normalisasi Data & Klasifikasi K-Nearest Neighbor")

    card_knn_w = Inches(3.64)
    card_knn_h = Inches(5.0)

    # Box 1: StandardScaler
    add_card(slide11, Inches(0.8), Inches(1.7), card_knn_w, card_knn_h)
    box = slide11.shapes.add_textbox(Inches(1.0), Inches(1.9), card_knn_w - Inches(0.4), card_knn_h - Inches(0.4))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "1. Penskalaan Fitur"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    p = tf.add_paragraph()
    p.text = "StandardScaler (Z-Score):"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_before = Pt(8)
    p = tf.add_paragraph()
    p.text = "z = (x - μ) / σ"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT
    p.space_before = Pt(4)

    p = tf.add_paragraph()
    p.text = "• Menyamakan skala antara parameter histogram (0.0 - 1.0) dengan kontras GLCM yang bernilai ratusan.\n• Mencegah satu parameter mendominasi metrik jarak euclidean/manhattan secara tidak seimbang."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT
    p.space_before = Pt(6)

    # Box 2: Jarak Manhattan
    add_card(slide11, Inches(4.84), Inches(1.7), card_knn_w, card_knn_h)
    box = slide11.shapes.add_textbox(Inches(5.04), Inches(1.9), card_knn_w - Inches(0.4), card_knn_h - Inches(0.4))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "2. Metrik Manhattan"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    p = tf.add_paragraph()
    p.text = "Metrik Jarak L1-Norm:"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT
    p.space_before = Pt(8)
    p = tf.add_paragraph()
    p.text = "d(p, q) = Σ |p_i - q_i|"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT
    p.space_before = Pt(4)

    p = tf.add_paragraph()
    p.text = "• Pada ruang vektor dimensi gabungan (48 dimensi), metrik Manhattan terbukti lebih tangguh dibanding Euclidean.\n• Mengurangi dampak outlier ekstrem dan menghindari distorsi fenomena 'curse of dimensionality'."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT
    p.space_before = Pt(6)

    # Box 3: Distance Weighting
    add_card(slide11, Inches(8.88), Inches(1.7), card_knn_w, card_knn_h)
    box = slide11.shapes.add_textbox(Inches(9.08), Inches(1.9), card_knn_w - Inches(0.4), card_knn_h - Inches(0.4))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "3. Konfigurasi Optimal"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    p = tf.add_paragraph()
    p.text = "k = 3 & Invers Jarak:"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_before = Pt(8)
    p = tf.add_paragraph()
    p.text = "weight = 1 / distance"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT
    p.space_before = Pt(4)

    p = tf.add_paragraph()
    p.text = "• Nilai k = 3 memberikan kompromi terbaik antara generalisasi dan sensitivitas batas kelas lokal.\n• Voting terbobot (distance-weighted) memberi bobot suara lebih besar pada tetangga yang sangat dekat."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT
    p.space_before = Pt(6)

    # ==========================================================
    # SLIDE 12: IMPLEMENTASI APLIKASI WEB (STREAMLIT APP)
    # ==========================================================
    slide12 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide12, COLOR_BG_LIGHT)
    add_header(slide12, "Implementasi Antarmuka Sistem Berbasis Web (Streamlit)")

    # 3 Kolom Fitur Utama Aplikasi
    app_cols = [
        ("1. Visualisasi Segmentasi", "Menampilkan 3 panel citra berdampingan:\n• Citra Asli (Resized 256x256)\n• Masker Kontur Biner (Otsu)\n• Objek Tersegmentasi (Bitwise-AND)\nPengguna dapat memverifikasi kualitas isolasi objek secara visual."),
        ("2. Transparansi Fitur Numerik", "Membongkar 'black-box' dengan menampilkan nilai fisis hasil ekstraksi:\n• Momen warna LAB (mean & std)\n• Parameter bentuk geometri (circularity, aspect ratio, solidity)\n• Statistik tekstur GLCM & densitas Canny."),
        ("3. Inferensi Real-Time & Probabilitas", "Mengeluarkan kategori sampah secara instan (<0.05 detik):\n• Kategori Utama dengan Ikon Visual\n• Diagram Batang Distribusi Probabilitas Voting seluruh kelas\n• Respon cepat tanpa lag pada browser.")
    ]

    for idx, (title, desc) in enumerate(app_cols):
        left_p = Inches(0.8 + idx * 4.04)
        add_card(slide12, left_p, Inches(1.7), Inches(3.64), Inches(5.0))
        
        box = slide12.shapes.add_textbox(left_p + Inches(0.2), Inches(1.9), Inches(3.24), Inches(4.6))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT

        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(12)

    # ==========================================================
    # SLIDE 13: HASIL PENGUJIAN & EVALUASI PERFORMA
    # ==========================================================
    slide13 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide13, COLOR_BG_LIGHT)
    add_header(slide13, "Hasil Pengujian Empiris & Evaluasi Performa")

    # Big Metric Card
    add_card(slide13, Inches(0.8), Inches(1.7), Inches(3.64), Inches(5.0), border_color=COLOR_ACCENT)
    box = slide13.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(3.24), Inches(4.4))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Akurasi Keseluruhan"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_MUTED_TEXT

    p = tf.add_paragraph()
    p.text = "91.67%"
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT
    p.space_before = Pt(8)

    p = tf.add_paragraph()
    p.text = "Hasil evaluasi data uji menunjukkan model KNN dengan ekstraksi multi-domain memiliki daya pembeda yang sangat tinggi pada 5 jenis sampah padat."
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_MUTED_TEXT
    p.space_before = Pt(14)

    # Performance Breakdown Card Kanan
    add_card(slide13, Inches(4.84), Inches(1.7), Inches(7.68), Inches(5.0))
    box = slide13.shapes.add_textbox(Inches(5.14), Inches(1.9), Inches(7.08), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Analisis Performa Per Kategori Sampah"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT

    eval_items = [
        ("Kardus (F1-Score Tertinggi ~ 95%): ", "Kombinasi warna cokelat khas pada kanal LAB dan nilai homogenitas tekstur GLCM yang stabil memberikan keterpisahan kelas yang sangat sempurna."),
        ("Botol Kaca (F1-Score ~ 94%): ", "Perbedaan kontur keliling (circularity) dan ketiadaan garis kusut tepi Canny memudahkan pemisahan dari material kertas dan kaleng remuk."),
        ("Kertas (F1-Score ~ 91%): ", "Canny Edge Density yang tinggi akibat lekukan/lipatan acak menjadi fitur kunci pembeda dari permukaan licin botol plastik."),
        ("Kaleng Logam & Botol Plastik (F1-Score ~ 88-89%): ", "Terdapat sedikit kebingungan minor pada sudut pantulan cahaya tertentu di mana botol plastik bening memiliki pantulan spekular menyerupai logam."),
        ("Kecepatan Inferensi: ", "< 0.05 detik per citra pada CPU standar, membuktikan kelayakan implementasi waktu-nyata.")
    ]
    for t, d in eval_items:
        p = tf.add_paragraph()
        p.text = "• " + t
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)
        run = p.add_run(); run.text = d
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # ==========================================================
    # SLIDE 14: KEUNGGULAN DAN KETERBATASAN SISTEM
    # ==========================================================
    slide14 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide14, COLOR_BG_LIGHT)
    add_header(slide14, "Analisis Kritis: Keunggulan & Keterbatasan Sistem")

    # Card Keunggulan
    add_card(slide14, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1), border_color=COLOR_ACCENT)
    box = slide14.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🌟 Keunggulan Sistem"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT

    pros = [
        ("Komputasi Sangat Ringan: ", "Dapat dijalankan pada komputer tanpa GPU bahkan pada board komputasi tepi (Raspberry Pi/Jetson Nano)."),
        ("Transparan & Explainable AI: ", "Setiap keputusan prediksi dapat dilacak ke fitur fisik (apakah karena warna, bentuk kebundaran, atau tekstur kusut)."),
        ("Ukuran Model Minimal: ", "Artefak tersimpan (.pkl) hanya berukuran beberapa megabyte, ramah memori dan penyimpanan."),
        ("Interaktif & Siap Pakai: ", "Dilengkapi antarmuka web Streamlit yang mudah digunakan oleh operator non-teknis.")
    ]
    for t, d in pros:
        p = tf.add_paragraph()
        p.text = "✔ " + t
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)
        run = p.add_run(); run.text = d
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # Card Keterbatasan
    add_card(slide14, Inches(6.9), Inches(1.7), Inches(5.6), Inches(5.1), border_color=RGBColor(245, 158, 11)) # Amber
    box = slide14.shapes.add_textbox(Inches(7.2), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "⚠️ Keterbatasan & Tantangan"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = RGBColor(217, 119, 6)

    cons = [
        ("Sensitivitas Latar Belakang Kompleks: ", "Segmentasi Otsu bekerja optimal bila objek memiliki kontras yang cukup terhadap latar belakang; latar belakang bermotif rumit memerlukan penanganan tambahan."),
        ("Objek Tumpang Tindih (Occlusion): ", "Sistem saat ini didesain untuk citra sampah tunggal per frame (single-object classification)."),
        ("Variasi Deformasi Ekstrem: ", "Kaleng yang hancur total atau botol kaca yang telah pecah berkeping-keping dapat mengalami penurunan fitur bentuk circularity."),
        ("Pencahayaan Non-Homogen Ekstrem: ", "Meskipun memiliki fallback adaptive threshold, bayangan gelap pekat dapat mempengaruhi luas kontur.")
    ]
    for t, d in cons:
        p = tf.add_paragraph()
        p.text = "• " + t
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)
        run = p.add_run(); run.text = d
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # ==========================================================
    # SLIDE 15: KESIMPULAN & PENGEMBANGAN MASA DEPAN
    # ==========================================================
    slide15 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide15, COLOR_BG_LIGHT)
    add_header(slide15, "Kesimpulan & Rencana Pengembangan Masa Depan")

    # Kesimpulan Card Kiri
    add_card(slide15, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide15.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "📌 Kesimpulan Penelitian"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    concl_points = [
        "Integrasi metode pengolahan citra digital (Otsu, Gaussian Blur, Morfologi) berhasil mengisolasi objek sampah secara konsisten.",
        "Kombinasi fitur multi-domain (48 dimensi: HSV, LAB, Morfometri, GLCM, Canny Edge) terbukti mampu menangkap ciri fisik khas 5 jenis material.",
        "Algoritma KNN dengan jarak Manhattan dan distance weighting mencapai akurasi tinggi sebesar 91.67%.",
        "Sistem membuktikan bahwa pemodelan matematis fitur terstruktur tetap relevan, akurat, dan unggul efisiensi dibanding model deep learning untuk skenario resource-constrained."
    ]
    for pt in concl_points:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_MUTED_TEXT
        p.space_before = Pt(8)

    # Rencana Card Kanan
    add_card(slide15, Inches(6.9), Inches(1.7), Inches(5.6), Inches(5.1))
    box = slide15.shapes.add_textbox(Inches(7.2), Inches(1.9), Inches(5.0), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🚀 Rencana Pengembangan Lanjutan"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT

    future_points = [
        ("Implementasi Hardware IoT (Smart Trash Bin): ", "Integrasi kamera ESP32-CAM atau Raspberry Pi dengan aktuator servo untuk membuka tutup tempat sampah otomatis sesuai jenis material."),
        ("Segmentasi Multi-Objek: ", "Menerapkan teknik deteksi berbasis watershed atau contour grouping untuk memilah beberapa sampah sekaligus dalam satu wadah."),
        ("Augmentasi Korpus Data: ", "Memperluas variasi dataset dengan menambahkan sampel sampah kotor, basah, dan deformasi ekstrem dari fasilitas TPA nyata."),
        ("Dukungan Kategori Tambahan: ", "Menambahkan kelas material spesifik lainnya seperti limbah elektronik (e-waste), styrofoam, dan kemasan multilayer (tetra pak).")
    ]
    for t, d in future_points:
        p = tf.add_paragraph()
        p.text = "• " + t
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)
        run = p.add_run(); run.text = d
        run.font.bold = False
        run.font.color.rgb = COLOR_MUTED_TEXT

    # ==========================================================
    # SLIDE 16: Q&A / PENUTUP (DARK THEME)
    # ==========================================================
    slide16 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide16, COLOR_BG_DARK)

    # Accent decorative bar
    bar = slide16.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.0), Inches(0.8), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_ACCENT
    bar.line.fill.background()

    box = slide16.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(11.3), Inches(2.0))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Terima Kasih"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = tf.add_paragraph()
    p.text = "Sesi Tanya Jawab & Diskusi Terbuka"
    p.font.size = Pt(22)
    p.font.bold = False
    p.font.color.rgb = COLOR_ACCENT
    p.space_before = Pt(8)

    # Info card bawah
    card_end = add_card(slide16, Inches(1.0), Inches(4.7), Inches(11.3), Inches(1.8), bg_color=RGBColor(30, 41, 59), border_color=RGBColor(51, 65, 85))
    box = slide16.shapes.add_textbox(Inches(1.3), Inches(4.9), Inches(10.7), Inches(1.4))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Klasifikasi Jenis Sampah Berdasarkan Citra Digital Menggunakan Ekstraksi Fitur & KNN"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p = tf.add_paragraph()
    p.text = "Mata Kuliah: Visualisasi Komputer dan Pemrosesan Citra | Sekolah Vokasi IPB University"
    p.font.size = Pt(11)
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.space_before = Pt(3)

    p = tf.add_paragraph()
    p.text = "Demo Aplikasi: streamlit run app.py | GitHub: https://github.com/akbarlubis247/Projek-Viskom-n-citra"
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_PRIMARY
    p.space_before = Pt(6)

    # Save presentation
    output_filename = "Presentasi_Projek_Klasifikasi_Sampah_Viskom.pptx"
    prs.save(output_filename)
    print(f"[BERHASIL] File presentasi tersimpan: {output_filename}")

if __name__ == '__main__':
    create_presentation()
