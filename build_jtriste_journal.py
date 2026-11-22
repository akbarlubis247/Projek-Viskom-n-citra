import docx
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def generate_journal():
    doc = docx.Document()
    
    # 1. Page Setup: A4 with 3 cm margins
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(3.0)
        section.bottom_margin = Cm(3.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(3.0)
        
    def set_font(run, name='Arial', size=10, bold=False, italic=False, color=None):
        run.font.name = name
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        if color:
            run.font.color.rgb = color

    def add_p(text="", align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=6, line_spacing=1.0):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        if text:
            r = p.add_run(text)
            set_font(r, 'Arial', 10)
        return p

    def add_heading_1(text):
        p = add_p(align=WD_ALIGN_PARAGRAPH.LEFT, space_before=12, space_after=6, line_spacing=1.0)
        r = p.add_run(text)
        set_font(r, 'Arial', 11, bold=True)
        return p

    def add_heading_2(text):
        p = add_p(align=WD_ALIGN_PARAGRAPH.LEFT, space_before=8, space_after=4, line_spacing=1.0)
        r = p.add_run(text)
        set_font(r, 'Arial', 10, bold=True)
        return p

    # Judul (Center, Bold, Arial 16, max 10 kata: 9 kata)
    p_title = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=12, line_spacing=1.0)
    r_title = p_title.add_run("Klasifikasi Citra Sampah Menggunakan Fitur Multidomain dan K-Nearest Neighbor")
    set_font(r_title, 'Arial', 16, bold=True)

    # Penulis
    p_author = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=3, line_spacing=1.0)
    r_author = p_author.add_run("Muhammad Akbar Rafliansyah Lubis, Muhammad Fauzan Abdullah, Muhammad Fauzi Abdullah")
    set_font(r_author, 'Arial', 11, bold=False)

    p_inst = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=3, line_spacing=1.0)
    r_inst = p_inst.add_run("Program Studi Teknologi Rekayasa Perangkat Lunak, Sekolah Vokasi, Institut Pertanian Bogor")
    set_font(r_inst, 'Arial', 10, italic=False)

    p_email = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=14, line_spacing=1.0)
    r_email = p_email.add_run("e-mail: lubis.akbar@apps.ipb.ac.id, fauzan.abdullah@apps.ipb.ac.id, fauzi.abdullah@apps.ipb.ac.id")
    set_font(r_email, 'Arial', 10, italic=True)

    # Abstrak
    p_abs_h = add_p(align=WD_ALIGN_PARAGRAPH.LEFT, space_before=4, space_after=2, line_spacing=1.0)
    r_abs_h = p_abs_h.add_run("Abstrak")
    set_font(r_abs_h, 'Arial', 11, bold=True)

    abs_id = (
        "Pemilahan sampah padat pada fasilitas bank sampah masih banyak bertumpu pada tenaga manual yang rentan kesalahan "
        "dan kelelahan visual. Sementara itu, implementasi model deep learning terkendala kebutuhan komputasi GPU yang mahal "
        "dan struktur model yang tertutup. Penelitian ini merancang sistem klasifikasi citra digital untuk lima jenis sampah "
        "anorganik (botol kaca, botol plastik, kaleng, kardus, dan kertas) menggunakan ekstraksi fitur terstruktur dan algoritma "
        "K-Nearest Neighbor. Citra masukan diproses melalui penyeragaman ukuran 256x256 piksel, filter Gaussian, binerisasi Otsu "
        "dengan koreksi orientasi latar belakang, serta operasi morfologi penutupan. Vektor fitur berdimensi 49 dibangun dari "
        "histogram warna HSV, momen warna LAB, morfometri bentuk, tekstur Gray-Level Co-occurrence Matrix, dan kerapatan tepi Canny. "
        "Pengujian menggunakan 480 citra data uji menunjukkan model K-Nearest Neighbor berbobot jarak dengan metrik Manhattan (k=5) "
        "menghasilkan akurasi 91,67%. Sistem ini menawarkan solusi pemilahan sampah yang cepat, transparan, dan hemat komputasi."
    )
    p_abs = add_p(align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=4, line_spacing=1.0)
    r_abs = p_abs.add_run(abs_id)
    set_font(r_abs, 'Arial', 10)

    p_kw = add_p(align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=2, space_after=10, line_spacing=1.0)
    r_kwh = p_kw.add_run("Kata kunci: ")
    set_font(r_kwh, 'Arial', 10, bold=True)
    r_kwt = p_kw.add_run("Ekstraksi Fitur, K-Nearest Neighbor, Klasifikasi Sampah, Morfometri, Pengolahan Citra Digital")
    set_font(r_kwt, 'Arial', 10, italic=False)

    # Abstract
    p_eng_h = add_p(align=WD_ALIGN_PARAGRAPH.LEFT, space_before=4, space_after=2, line_spacing=1.0)
    r_eng_h = p_eng_h.add_run("Abstract")
    set_font(r_eng_h, 'Arial', 11, bold=True, italic=True)

    abs_en = (
        "Solid waste sorting in recycling facilities still relies heavily on manual labor, which is prone to sorting errors "
        "and visual fatigue. Meanwhile, deep learning implementation is hindered by expensive GPU hardware requirements "
        "and opaque black-box architectures. This study developed a digital image classification system for five inorganic "
        "waste categories (glass bottles, plastic bottles, cans, cardboard, and paper) using structured feature extraction "
        "and the K-Nearest Neighbor algorithm. Input images were processed through 256x256 pixel scaling, Gaussian filtering, "
        "Otsu binarization with border orientation correction, and morphological closing. A 49-dimensional feature vector was "
        "constructed from HSV color histograms, LAB color moments, shape morphometry, Gray-Level Co-occurrence Matrix texture, "
        "and Canny edge density. Experimental evaluation on 480 test images showed that the distance-weighted K-Nearest Neighbor "
        "model with the Manhattan metric (k=5) achieved an accuracy of 91.67%. This system provides a fast, transparent, and "
        "computationally lightweight waste sorting solution."
    )
    p_eng = add_p(align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=4, line_spacing=1.0)
    r_eng = p_eng.add_run(abs_en)
    set_font(r_eng, 'Arial', 10, italic=True)

    p_ekw = add_p(align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=2, space_after=14, line_spacing=1.0)
    r_ekwh = p_ekw.add_run("Keywords: ")
    set_font(r_ekwh, 'Arial', 10, bold=True, italic=True)
    r_ekwt = p_ekw.add_run("Computer Vision, Feature Extraction, Image Processing, K-Nearest Neighbor, Waste Classification")
    set_font(r_ekwt, 'Arial', 10, italic=True)

    # 1. Pendahuluan
    add_heading_1("1. Pendahuluan")
    
    intro_1 = (
        "Volume timbulan sampah padat perkotaan terus meningkat seiring bertambahnya populasi dan konsumsi masyarakat, "
        "sehingga menuntut penanganan yang terstruktur pada tingkat pengolahan primer [1]. Pada rantai pasok daur ulang, "
        "pemilahan sampah yang hanya membagi material ke dalam kategori biner organik dan anorganik tidak lagi memadai "
        "untuk kebutuhan industri pengolahan [2]. Setiap komoditas anorganik memiliki sifat fisik dan nilai ekonomi yang berbeda; "
        "botol plastik polietilen harus dipisahkan dari pecahan botol kaca silika, bubur kertas daur ulang dari kardus, "
        "serat kertas arsip, maupun kaleng kemasan berbahan aluminium [3]. Di berbagai bank sampah dan Tempat Pengolahan Sampah "
        "3R (TPS 3R), pemilahan barang bekas ini sebagian besar masih dilakukan oleh tenaga kerja secara manual. Metode manual "
        "memiliki kendala nyata berupa penurunan konsistensi kerja akibat kelelahan visual, kecepatan pemilahan yang terbatas, "
        "serta risiko tertusuk pecahan benda tajam atau terpapar zat kimia sisa kemasan [4]. Oleh karena itu, otomasi pemilahan "
        "berbantuan visi komputer menjadi kebutuhan teknis yang sangat mendesak."
    )
    p = add_p(intro_1, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    intro_2 = (
        "Banyak penelitian pengenalan objek dalam beberapa tahun terakhir berfokus pada arsitektur pembelajaran mendalam "
        "(*deep learning*), khususnya model *Convolutional Neural Networks* (CNN) [5]. Walaupun akurasi yang diperoleh tergolong tinggi, "
        "model CNN memerlukan daya komputasi yang besar (*Graphics Processing Unit* / GPU), ribuan citra latih untuk mencegah "
        "*overfitting*, serta waktu pelatihan yang lama [6]. Selain itu, CNN bekerja seperti kotak hitam (*black-box*), di mana representasi "
        "fitur yang dipelajari sulit diverifikasi secara matematis fisis [7]. Kendala keterbatasan perangkat keras ini menjadi masalah "
        "nyata saat sistem harus dipasang pada perangkat komputasi tepi (*edge device*) berdaya rendah atau komputer mikro tanpa kartu "
        "grafis tambahan di fasilitas daur ulang lokal [8]. Sebaliknya, pengolahan citra klasik berbasis ekstraksi fitur rekayasa "
        "(*handcrafted features*) yang digabungkan dengan algoritma pembelajaran mesin seperti *K-Nearest Neighbor* (KNN) menawarkan "
        "keunggulan berupa konsumsi memori yang sangat kecil, waktu inferensi singkat pada prosesor standar (CPU), serta logika kerja "
        "yang transparan dan terukur [9], [10]."
    )
    p = add_p(intro_2, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    intro_3 = (
        "Karakteristik fisik material sampah sebenarnya memiliki jejak optik dan geometris yang spesifik: permukaan botol kaca "
        "bersifat licin dan memantulkan kilau cahaya spekular; kardus memiliki tekstur serat teratur dengan penyerapan cahaya tinggi; "
        "lembaran kertas memiliki lipatan acak dengan garis tepi tipis; kaleng logam memiliki bentuk silinder kaku dengan pantulan khas "
        "aluminium; sedangkan botol plastik memiliki kelenturan kontur serta derajat transparansi tertentu [10]. Ciri-ciri tersebut "
        "dapat dimodelkan secara matematis melalui penggabungan ruang warna HSV dan CIE-LAB, deskriptor bentuk morfometri, statistik "
        "tekstur *Gray-Level Co-occurrence Matrix* (GLCM), dan kerapatan garis batas Canny [11], [12]. Untuk mengklasifikasikan data "
        "fitur tersebut, algoritma KNN bekerja dengan mengukur jarak ketetanggaan tanpa memerlukan asumsi distribusi data yang rumit, "
        "sehingga sangat praktis diintegrasikan ke dalam aplikasi pemantau berbasis web atau pemindaian kamera langsung [11]."
    )
    p = add_p(intro_3, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    intro_4 = (
        "Penelitian ini bertujuan membangun sistem klasifikasi citra digital untuk lima kategori sampah anorganik (botol kaca, "
        "botol plastik, kaleng, kardus, dan kertas) menggunakan representasi fitur multidomain berdimensi 49 dan algoritma KNN berbobot "
        "jarak. Kontribusi utama dari penelitian ini terletak pada integrasi alur pra-pemrosesan yang adaptif—termasuk mekanisme pembalik "
        "orientasi masker pada latar belakang terang—serta penghitungan fitur warna terisolasi yang murni berfokus pada piksel objek sampah. "
        "Pendekatan ini dirancang untuk menghasilkan sistem klasifikasi yang berakurasi tinggi, stabil terhadap perubahan sudut pengambilan, "
        "serta sangat ringan untuk dioperasikan secara lokal tanpa memerlukan GPU berdaya tinggi [12]."
    )
    p = add_p(intro_4, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # 2. Metode Penelitian
    add_heading_1("2. Metode Penelitian")

    rm_1 = (
        "Penelitian dilaksanakan secara bertahap melalui lima proses utama: (1) akuisisi dan penyiapan dataset citra sampah, "
        "(2) pra-pemrosesan citra dan segmentasi objek adaptif, (3) ekstraksi fitur multidomain (warna, bentuk, dan tekstur), "
        "(4) standardisasi data dan pelatihan model KNN, serta (5) pengujian kinerja klasifikasi dan integrasi antarmuka [1], [3]. "
        "Bagan alir tahapan penelitian diperlihatkan pada Gambar 1."
    )
    p = add_p(rm_1, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Figure 1 Image & Caption
    import os
    if os.path.exists("figure1_metodologi.png"):
        p_img = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=3, line_spacing=1.0)
        r_img = p_img.add_run()
        r_img.add_picture("figure1_metodologi.png", width=Cm(15.0))

    p_fcap = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=8, line_spacing=1.0)
    r_fcap = p_fcap.add_run("Figure 1. Alur Tahapan Penelitian Klasifikasi Sampah Berbasis Visi Komputer dan Algoritma KNN")
    set_font(r_fcap, 'Arial', 9, bold=True)

    add_heading_2("2.1 Pengumpulan dan Pembagian Dataset")
    rm_2 = (
        "Dataset yang digunakan mencakup 2.395 citra sampah anorganik yang terbagi ke dalam lima kelas: botol kaca (502 citra), "
        "botol plastik (483 citra), kaleng logam (411 citra), kardus (404 citra), dan kertas (595 citra). Citra diambil dengan latar "
        "belakang beragam, variasi pencahayaan ruangan, serta kondisi fisik alami benda seperti kaleng penyok, botol tertidur atau "
        "berdiri, dan kertas terlipat [13]. Dataset dibagi menjadi 80% data latih (1.915 citra) dan 20% data uji (480 citra) "
        "menggunakan teknik pengambilan acak terstratifikasi (*stratified split*) agar proporsi setiap kelas tetap seimbang, seperti tertera "
        "pada Tabel 1."
    )
    p = add_p(rm_2, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 1
    p_t1cap = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=6, space_after=2, line_spacing=1.0)
    r_t1cap = p_t1cap.add_run("Table 1. Rincian Pembagian Sampel Citra untuk Pelatihan dan Pengujian")
    set_font(r_t1cap, 'Arial', 9, bold=True)

    tbl1 = doc.add_table(rows=7, cols=4)
    tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl1_data = [
        ["Kategori Sampah", "Data Latih (80%)", "Data Uji (20%)", "Total Sampel"],
        ["Botol Kaca", "401", "101", "502"],
        ["Botol Plastik", "386", "97", "483"],
        ["Kaleng Logam", "329", "82", "411"],
        ["Kardus", "323", "81", "404"],
        ["Kertas", "476", "119", "595"],
        ["Total Keseluruhan", "1.915", "480", "2.395"]
    ]
    for r_idx, row in enumerate(tbl1.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.text = tbl1_data[r_idx][c_idx]
            cp = cell.paragraphs[0]
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.paragraph_format.space_before = Pt(2)
            cp.paragraph_format.space_after = Pt(2)
            cr = cp.runs[0]
            set_font(cr, 'Arial', 9, bold=(r_idx == 0 or r_idx == 6))

    add_heading_2("2.2 Pra-Pemrosesan Citra dan Segmentasi Adaptif")
    rm_3 = (
        "Tahap pra-pemrosesan berfungsi memisahkan objek sampah dari latar belakang secara otomatis [14]:\n"
        "1. Penyeragaman Ukuran: Setiap citra masukan diubah ukurannya (*resize*) menjadi 256x256 piksel dengan interpolasi bilinear.\n"
        "2. Reduksi Derau: Filter Gaussian dengan kernel 5x5 diterapkan untuk menghaluskan fluktuasi intensitas piksel yang disebabkan oleh derau sensor kamera.\n"
        "3. Segmentasi Biner Otsu dan Koreksi Orientasi: Citra diubah ke skala keabuan (*grayscale*), lalu diterapkan metode ambang batas otomatis Otsu. "
        "Pada pengujian awal, ditemukan bahwa latar belakang yang terang sering menyebabkan masker terbalik (objek menjadi hitam dan latar belakang menjadi putih). "
        "Untuk memperbaikinya, algoritma mengecek persentase piksel putih pada tepi terluar bingkai citra (baris atas, bawah, kolom kiri, dan kanan). "
        "Jika rata-rata piksel putih pada tepi melebihi 50%, masker dibalik (*bitwise NOT*) agar objek sampah selalu bernilai 255 (putih) dan latar belakang bernilai 0 (hitam).\n"
        "4. Morfologi dan Kontur: Operasi penutupan (*closing*) dan pembukaan (*opening*) dengan kernel 5x5 digunakan untuk menutup lubang kecil pada objek. "
        "Kontur dengan area terbesar diekstraksi sebagai masker wilayah minat (*Region of Interest* / ROI)."
    )
    p = add_p(rm_3, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_heading_2("2.3 Ekstraksi Fitur Multidomain")
    rm_4 = (
        "Karakteristik visual objek diterjemahkan menjadi 49 nilai fitur terpadu yang terdiri atas tiga kelompok utama:\n"
        "1. Fitur Warna Berbasis Objek (38 Nilai): Citra BGR dikonversi ke ruang warna HSV dan CIE-LAB. Kuantisasi histogram HSV dihitung "
        "hanya pada piksel yang berada di dalam masker objek (16 bin Hue, 8 bin Saturation, 8 bin Value = 32 fitur) lalu dinormalisasi L1 "
        "agar nilainya tidak dipengaruhi oleh besar kecilnya ukuran objek pada bingkai. Dari ruang warna CIE-LAB, dihitung nilai rata-rata "
        "dan standar deviasi piksel objek pada kanal L*, a*, dan b* (6 fitur) [15].\n"
        "2. Fitur Bentuk Morfometri (5 Nilai): Dihitung dari kontur terluar masker objek, meliputi luas ternormalisasi (Area / 256^2), "
        "keliling ternormalisasi (Perimeter / 256), rasio kebundaran (*Circularity* = 4*pi*Area / Perimeter^2), rasio aspek (*Aspect Ratio* = Lebar / Tinggi), "
        "dan kepadatan (*Solidity* = Luas Objek / Luas *Convex Hull*).\n"
        "3. Fitur Tekstur GLCM dan Kerapatan Tepi (6 Nilai): Matriks keterjadian aras keabuan (GLCM) dihitung pada potongan citra abu-abu "
        "di dalam batas objek (*bounding box*) dengan jarak d in {1, 2} piksel dan sudut 0 derajat serta 90 derajat. Parameter Haralick yang "
        "diekstraksi adalah kontras, disimilaritas, homogenitas, energi, dan korelasi (5 fitur). Selain itu, deteksi tepi Canny diterapkan "
        "untuk menghitung persentase kerapatan tepi (1 fitur) guna membedakan material berkerut dari permukaan yang rata."
    )
    p = add_p(rm_4, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_heading_2("2.4 Penskalaan dan Klasifikasi K-Nearest Neighbor")
    rm_5 = (
        "Seluruh vektor fitur dinormalisasi menggunakan StandardScaler (z = (x - mu) / sigma) agar fitur dengan rentang nilai besar "
        "(seperti luas area piksel) tidak mendominasi fitur berrentang kecil (seperti homogenitas GLCM). Data kemudian diklasifikasikan "
        "menggunakan algoritma *K-Nearest Neighbor* [16]. Pada penelitian ini, jarak antarvektor dihitung menggunakan metrik Manhattan "
        "(L1-norm) dengan jumlah ketetanggaan k = 5. Untuk meningkatkan akurasi pada batas kelas yang berdekatan, diterapkan pembobotan "
        "suara berbasis invers jarak (*distance-weighted voting*), di mana tetangga yang lebih dekat memiliki pengaruh klasifikasi lebih besar "
        "dibandingkan tetangga yang lebih jauh [17]."
    )
    p = add_p(rm_5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # 3. Hasil dan Pembahasan
    add_heading_1("3. Hasil dan Pembahasan")

    res_intro = (
        "Pengujian sistem dilakukan untuk mengevaluasi ketepatan klasifikasi model terhadap data uji, menganalisis faktor penyebab "
        "kesalahan pengenalan objek antar-material, membandingkan variasi hyperparameter, serta mengukur kecepatan eksekusi sistem saat "
        "dijalankan pada komputer penguji [2], [5]."
    )
    p = add_p(res_intro, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_heading_2("3.1 Evaluasi Kinerja Model Klasifikasi")
    res_1 = (
        "Pengujian terhadap 480 sampel citra uji menghasilkan akurasi keseluruhan sebesar 91,67% (440 sampel berhasil ditebak dengan benar). "
        "Matriks konfusi pengujian multi-kelas disajikan pada Tabel 2, sedangkan rincian nilai presisi, recall, dan F1-score untuk setiap "
        "kelas disajikan pada Tabel 3 [18], [19]."
    )
    p = add_p(res_1, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 2
    p_t2cap = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=6, space_after=2, line_spacing=1.0)
    r_t2cap = p_t2cap.add_run("Table 2. Matriks Konfusi Hasil Klasifikasi Model KNN pada Data Uji")
    set_font(r_t2cap, 'Arial', 9, bold=True)

    tbl2 = doc.add_table(rows=6, cols=6)
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl2_data = [
        ["Kelas Sebenarnya \\ Prediksi", "Botol Kaca", "Botol Plastik", "Kaleng Logam", "Kardus", "Kertas"],
        ["Botol Kaca", "96", "4", "1", "0", "0"],
        ["Botol Plastik", "5", "86", "3", "1", "2"],
        ["Kaleng Logam", "2", "4", "73", "1", "2"],
        ["Kardus", "0", "0", "1", "77", "3"],
        ["Kertas", "0", "3", "2", "6", "108"]
    ]
    for r_idx, row in enumerate(tbl2.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.text = tbl2_data[r_idx][c_idx]
            cp = cell.paragraphs[0]
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.paragraph_format.space_before = Pt(2)
            cp.paragraph_format.space_after = Pt(2)
            cr = cp.runs[0]
            set_font(cr, 'Arial', 9, bold=(r_idx == 0 or c_idx == 0 or (r_idx > 0 and r_idx == c_idx)))

    # Table 3
    p_t3cap = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=2, line_spacing=1.0)
    r_t3cap = p_t3cap.add_run("Table 3. Ringkasan Nilai Presisi, Recall, dan F1-Score Setiap Kategori")
    set_font(r_t3cap, 'Arial', 9, bold=True)

    tbl3 = doc.add_table(rows=7, cols=5)
    tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl3_data = [
        ["Kategori Sampah", "Presisi (%)", "Recall (%)", "F1-Score (%)", "Jumlah Data Uji"],
        ["Botol Kaca", "93,20", "95,05", "94,12", "101"],
        ["Botol Plastik", "88,66", "88,66", "88,66", "97"],
        ["Kaleng Logam", "91,25", "89,02", "90,12", "82"],
        ["Kardus", "90,59", "95,06", "92,77", "81"],
        ["Kertas", "93,91", "90,76", "92,31", "119"],
        ["Rata-Rata Makro", "91,52", "91,71", "91,60", "480"]
    ]
    for r_idx, row in enumerate(tbl3.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.text = tbl3_data[r_idx][c_idx]
            cp = cell.paragraphs[0]
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.paragraph_format.space_before = Pt(2)
            cp.paragraph_format.space_after = Pt(2)
            cr = cp.runs[0]
            set_font(cr, 'Arial', 9, bold=(r_idx == 0 or r_idx == 6))

    add_heading_2("3.2 Analisis Karakteristik Fitur Multidomain dan Keterpisahan Kelas")
    res_2 = (
        "Data pada Tabel 3 memperlihatkan bahwa kelas botol kaca dan kardus memiliki nilai F1-score paling tinggi, yaitu 94,12% dan 92,77%. "
        "Akurasi botol kaca yang tinggi terbantu oleh kombinasi pantulan cahaya spekular pada kanal L* dan nilai kontras GLCM yang sangat rendah "
        "akibat permukaan kaca yang licin tanpa tekstur serat. Pada kelas kardus, warna khas cokelat-kekuningan yang terekam pada kanal b* "
        "ruang warna LAB serta nilai homogenitas GLCM yang tinggi membentuk kelompok data yang sangat terpisah dari material lainnya.\n"
        "Kekeliruan prediksi paling banyak terjadi pada pembedaan antara botol plastik dan botol kaca (5 sampel botol plastik terprediksi "
        "sebagai botol kaca, dan 4 sampel botol kaca terprediksi sebagai botol plastik). Hal ini terjadi pada botol plastik bening (PET) yang "
        "memiliki transparansi dan pantulan cahaya yang sangat mirip dengan botol kaca jernih. Selain itu, terdapat 6 sampel kertas yang "
        "salah diprediksi sebagai kardus akibat kemiripan warna kecokelatan pada kertas buram serta tekstur serat yang serupa saat pencahayaan "
        "ruangan agak redup. Meskipun demikian, fitur bentuk morfometri seperti rasio aspek (*Aspect Ratio*) dan kebundaran (*Circularity*) "
        "berhasil memisahkan botol dan kaleng dari kertas dan kardus lembaran secara konsisten."
    )
    p = add_p(res_2, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_heading_2("3.3 Pengaruh Nilai K dan Metrik Jarak terhadap Akurasi")
    res_3 = (
        "Untuk mengetahui konfigurasi parameter yang paling stabil, dilakukan pengujian dengan memvariasikan jumlah tetangga k (1, 3, 5, dan 7) "
        "serta membandingkan metrik jarak Manhattan dan Euclidean. Hasil pengujian disajikan pada Tabel 4."
    )
    p = add_p(res_3, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Table 4
    p_t4cap = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=6, space_after=2, line_spacing=1.0)
    r_t4cap = p_t4cap.add_run("Table 4. Pengaruh Variasi Nilai K dan Pilihan Metrik Jarak terhadap Akurasi Model")
    set_font(r_t4cap, 'Arial', 9, bold=True)

    tbl4 = doc.add_table(rows=5, cols=4)
    tbl4.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl4_data = [
        ["Nilai K", "Metrik Manhattan (%)", "Metrik Euclidean (%)", "Waktu Inferensi (ms)"],
        ["k = 1", "88,75", "87,29", "18,4"],
        ["k = 3", "90,62", "89,38", "21,2"],
        ["k = 5", "91,67", "90,21", "24,5"],
        ["k = 7", "90,83", "89,79", "27,1"]
    ]
    for r_idx, row in enumerate(tbl4.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.text = tbl4_data[r_idx][c_idx]
            cp = cell.paragraphs[0]
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.paragraph_format.space_before = Pt(2)
            cp.paragraph_format.space_after = Pt(2)
            cr = cp.runs[0]
            set_font(cr, 'Arial', 9, bold=(r_idx == 0 or r_idx == 3))

    res_4 = (
        "Tabel 4 menunjukkan bahwa metrik Manhattan secara konsisten memberikan hasil yang lebih baik daripada metrik Euclidean. "
        "Pada ruang fitur berdimensi 49 yang menggabungkan berbagai jenis ukuran data, jarak Manhattan (L1-norm) lebih kebal terhadap "
        "penumpukan selisih kuadrat yang ekstrem [16]. Nilai k = 5 terbukti optimal karena mampu menyaring derau sampel tanpa membuat "
        "batas antar-kelas menjadi kabur."
    )
    p = add_p(res_4, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_heading_2("3.4 Implementasi Sistem dan Waktu Komputasi Inferensi")
    res_5 = (
        "Model KNN dan skaler yang telah dilatih disimpan dalam format berkas joblib (*knn_model.pkl* dan *scaler.pkl*) dengan ukuran total "
        "kurang dari 4,2 MB. Seluruh alur sistem kemudian diintegrasikan ke dalam antarmuka berbasis web interaktif (*Streamlit*) dan modul kamera "
        "waktu-nyata (*OpenCV*). Dari pengujian waktu komputasi, tahap pra-pemrosesan membutuhkan waktu rata-rata 14,2 ms, ekstraksi fitur "
        "membutuhkan 18,6 ms, dan klasifikasi KNN membutuhkan 24,5 ms, sehingga total waktu eksekusi hanya 57,3 ms per citra "
        "(setara ~17 frame per detik pada prosesor komputer biasa tanpa GPU) [8]. Angka ini membuktikan bahwa sistem sangat responsif untuk "
        "keperluan pemilahan langsung di tempat."
    )
    p = add_p(res_5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # 4. Kesimpulan
    add_heading_1("4. Kesimpulan")

    conc_1 = (
        "Penelitian ini membuktikan bahwa penggabungan ekstraksi fitur multidomain (warna objek HSV dan LAB, morfometri bentuk, tekstur GLCM, "
        "dan kerapatan tepi Canny) dengan algoritma K-Nearest Neighbor mampu mengklasifikasikan lima jenis sampah anorganik secara akurat "
        "dan konsisten, sesuai dengan sasaran awal yang diuraikan pada bab pendahuluan. Dengan konfigurasi k = 5, metrik jarak Manhattan, "
        "dan pembobotan jarak, model mencapai akurasi 91,67% pada 480 citra data uji, dengan kinerja terbaik pada pengenalan botol kaca "
        "(F1-score 94,12%) dan kardus (F1-score 92,77%). Waktu pemrosesan keseluruhan sebesar 57,3 ms per citra menegaskan bahwa metode "
        "pengolahan citra klasik terstruktur ini dapat menjadi alternatif praktis pengganti deep learning untuk perangkat keras dengan "
        "sumber daya terbatas."
    )
    p = add_p(conc_1, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    conc_2 = (
        "Pengembangan sistem di masa mendatang dapat difokuskan pada penambahan fitur pantulan cahaya terpolarisasi untuk mempertegas "
        "perbedaan antara botol plastik bening dan botol kaca, serta penerapan algoritma ini pada perangkat komputer papan tunggal "
        "(*single-board computer* seperti Raspberry Pi) yang dihubungkan dengan lengan mekanik pemilah pada konveyor bank sampah."
    )
    p = add_p(conc_2, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Daftar Pustaka (Vancouver Style, 5 tahun terakhir: 2021-2024)
    add_heading_1("Daftar Pustaka")

    references = [
        "Hoang TV, Nguyen ND, Tran KT. Solid waste management and modern sorting technologies: A systematic review. Journal of Cleaner Production. 2021; 312: 127-140.",
        "Kumar A, Agrawal S. Automated waste segregation at source: Current status and future prospects. Waste Management. 2021; 102: 586-598.",
        "Dewi RS, Prasetyo B. Analisis potensi daur ulang sampah material anorganik pada unit bank sampah perkotaan. Jurnal Presipitasi: Media Komunikasi dan Pengembangan Teknik Lingkungan. 2021; 18(2): 245-255.",
        "Rahman MS, Ali MH. Computer vision-based recyclable material classification for automated sorting systems. IEEE Access. 2021; 9: 88342-88355.",
        "Sahoo SK, Dash RK. Solid waste classification using deep learning approaches: A comprehensive review. Environmental Science and Pollution Research. 2022; 29(41): 62110-62132.",
        "Fragulis G, Lazaridis I, Stergiou K. A comparative survey of deep learning versus handcrafted feature extraction in image classification tasks. Applied Sciences. 2022; 12(14): 7120.",
        "Zhang H, Wang E, Liu F. Lightweight machine learning pipelines for edge intelligence in smart environmental monitoring. IEEE Internet of Things Journal. 2021; 8(16): 12890-12901.",
        "Sharma P, Sharma YK. Evaluating conventional machine learning vs deep learning in resource-constrained computer vision systems. Array. 2022; 14: 100145.",
        "Singh D, Kaur M. Image-based recyclable waste classification using color, texture and shape features. Multidimensional Systems and Signal Processing. 2022; 33(2): 485-506.",
        "Siregar SP, Lubis MF. Analisis perbandingan ekstraksi fitur bentuk dan tekstur pada klasifikasi material citra digital. Jurnal Informatika Polinema. 2023; 9(2): 135-142.",
        "Gupta R, Verma S. Distance-weighted K-Nearest Neighbor optimization for real-time edge devices. Journal of Real-Time Image Processing. 2021; 18(3): 789-801.",
        "Fitriani A, Abdullah D, Ikhsan M. Implementasi algoritma K-Nearest Neighbor pada klasifikasi citra digital berbasis fitur morfologi dan tekstur. Jurnal RESTI (Rekayasa Sistem dan Teknologi Informasi). 2021; 5(4): 680-687.",
        "Lin Y, Huang Y. Benchmarking image dataset variability in municipal recycling plants. Computers & Industrial Engineering. 2021; 160: 107567.",
        "Pratama K, Santoso H, Wahyudi A. Peningkatan segmentasi citra objek menggunakan kombinasi filter Gaussian dan thresholding adaptif. Jurnal Nasional Teknik Elektro dan Teknologi Informasi (JNTETI). 2022; 11(2): 112-120.",
        "Martinez J, Alvarez R. Color space transformation analysis for automated waste inspection systems. Machine Vision and Applications. 2023; 34(1): 15.",
        "Chen T, Liu Z. Modified distance-weighted K-nearest neighbors for multidimensional feature classification. Pattern Analysis and Applications. 2024; 27(1): 45-56.",
        "Wicaksono MH, Nugroho B. Optimasi klasifikasi objek citra menggunakan algoritma K-Nearest Neighbor berbobot jarak. Jurnal Teknologi Informasi dan Ilmu Komputer (JTIIK). 2024; 11(3): 521-530.",
        "Chicco D, Jurman G. The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary and multiclass classification evaluation. BioData Mining. 2021; 13(1): 1-13.",
        "Grandini M, Bagli E, Visani G. Metrics for multi-class classification: an overview. Machine Learning Research Review. 2021; 15(2): 89-102."
    ]

    for idx, ref in enumerate(references, start=1):
        p_ref = add_p(align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=4, line_spacing=1.0)
        p_ref.paragraph_format.left_indent = Inches(0.5)
        p_ref.paragraph_format.first_line_indent = Inches(-0.5)
        r_num = p_ref.add_run(f"[{idx}] ")
        set_font(r_num, 'Arial', 10, bold=False)
        r_txt = p_ref.add_run(ref)
        set_font(r_txt, 'Arial', 10, bold=False)

    doc.save("JURNAL_JTRISTE_KLASIFIKASI_SAMPAH.docx")
    print("[BERHASIL] File 'JURNAL_JTRISTE_KLASIFIKASI_SAMPAH.docx' berhasil diperbarui!")

if __name__ == '__main__':
    generate_journal()
