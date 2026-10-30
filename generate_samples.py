"""
Skrip pembuat gambar sampel sintetis untuk pengujian awal sistem klasifikasi sampah.
"""
import os
import cv2
import numpy as np

CLASSES = ["botol_plastik", "kaleng", "kertas", "kardus", "botol_kaca"]

def generate_synthetic_samples():
    print("[*] Membuat gambar sintetis contoh untuk testing...")
    
    for cls in CLASSES:
        folder = os.path.join("dataset", cls)
        os.makedirs(folder, exist_ok=True)
        
        for i in range(1, 6): # buat 5 sampel per kelas
            # Background putih/terang dengan sedikit noise
            img = np.ones((300, 300, 3), dtype=np.uint8) * 240
            noise = np.random.randint(-15, 15, (300, 300, 3))
            img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            # Karakteristik per kategori
            if cls == "botol_plastik":
                # Lonjong, warna biru transparan/cyan
                color = (210, 180, 50) # BGR
                cv2.ellipse(img, (150, 150), (40, 100), 0, 0, 360, color, -1)
                cv2.rectangle(img, (135, 30), (165, 55), (180, 140, 30), -1) # tutup botol
            elif cls == "kaleng":
                # Silinder / lingkaran, warna merah cerah / silver
                color = (40, 50, 200) # Merah (kaleng soda)
                cv2.rectangle(img, (110, 80), (190, 220), color, -1)
                cv2.ellipse(img, (150, 80), (40, 15), 0, 0, 360, (180, 180, 180), -1)
            elif cls == "kertas":
                # Kotak tipis bertekstur, warna putih keabuan / kusut
                color = (220, 225, 230)
                pts = np.array([[80, 90], [220, 70], [210, 230], [90, 210]], np.int32)
                cv2.fillPoly(img, [pts], color)
                # Garis kusut
                cv2.line(img, (100, 120), (190, 160), (150, 150, 150), 2)
            elif cls == "kardus":
                # Cokelat berserat, bentuk persegi panjang
                color = (60, 120, 180) # Cokelat BGR
                cv2.rectangle(img, (80, 90), (220, 210), color, -1)
                # Tekstur garis gelombang kardus
                for y in range(100, 200, 15):
                    cv2.line(img, (90, y), (210, y), (40, 90, 140), 2)
            elif cls == "botol_kaca":
                # Hijau tua, leher botol panjang
                color = (60, 140, 50)
                cv2.ellipse(img, (150, 170), (45, 80), 0, 0, 360, color, -1)
                cv2.rectangle(img, (140, 50), (160, 100), color, -1)

            file_path = os.path.join(folder, f"sample_{i}.png")
            cv2.imwrite(file_path, img)
            
    print("[OK] Selesai membuat 25 gambar sampel dummy di folder dataset/.")

if __name__ == "__main__":
    generate_synthetic_samples()
