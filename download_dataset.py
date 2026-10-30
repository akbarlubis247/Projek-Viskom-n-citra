import os
import shutil
import zipfile
import urllib.request

DATASET_ZIP_URL = "https://raw.githubusercontent.com/garythung/trashnet/master/data/dataset-resized.zip"
ZIP_DEST = "dataset-resized.zip"
TARGET_DATASET_DIR = "dataset"

# Mapping kategori TrashNet ke kategori proyek kamu
CLASS_MAP = {
    "plastic": "botol_plastik",
    "metal": "kaleng",
    "paper": "kertas",
    "cardboard": "kardus",
    "glass": "botol_kaca"
}

def download_file(url, dest):
    print(f"[*] Mendownload TrashNet dataset (~40 MB)...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
        total_size = int(response.info().get('Content-Length', 0))
        downloaded = 0
        block_size = 1024 * 64
        while True:
            chunk = response.read(block_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = downloaded * 100 / total_size
                print(f"\r  -> Progress: {percent:.1f}% ({downloaded // (1024*1024)} MB)", end="")
    print("\n[OK] Download selesai.")

def extract_and_organize():
    print("[*] Mengekstrak file zip...")
    temp_dir = "temp_trashnet"
    with zipfile.ZipFile(ZIP_DEST, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    print("[*] Mengorganisasi dataset ke folder projek...")
    # Cari folder dataset-resized di dalam ekstraksi
    source_root = None
    for root, dirs, _ in os.walk(temp_dir):
        if "dataset-resized" in dirs or os.path.basename(root) == "dataset-resized":
            source_root = root if os.path.basename(root) == "dataset-resized" else os.path.join(root, "dataset-resized")
            break

    if not source_root:
        source_root = temp_dir

    for src_name, target_name in CLASS_MAP.items():
        src_path = os.path.join(source_root, src_name)
        target_path = os.path.join(TARGET_DATASET_DIR, target_name)
        
        # Bersihkan folder sampel dummy lama
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        os.makedirs(target_path, exist_ok=True)

        if os.path.exists(src_path):
            files = [f for f in os.listdir(src_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"  -> Memindahkan {len(files)} foto untuk kelas '{target_name}'...")
            for f in files:
                shutil.copy2(os.path.join(src_path, f), os.path.join(target_path, f))

    # Bersihkan file zip dan temporary
    print("[*] Membersihkan file sementara...")
    shutil.rmtree(temp_dir, ignore_errors=True)
    if os.path.exists(ZIP_DEST):
        os.remove(ZIP_DEST)

    print("[OK] Dataset TrashNet asli siap digunakan di folder dataset/!")

if __name__ == "__main__":
    download_file(DATASET_ZIP_URL, ZIP_DEST)
    extract_and_organize()
