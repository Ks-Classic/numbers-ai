import os
import subprocess
import zipfile
import shutil
import sys

def download_and_extract():
    # 作業ディレクトリ
    temp_dir = "temp_libs"
    extract_dir = os.path.join(temp_dir, "extracted")
    target_lib_dir = "api/lib"
    
    # クリーンアップと作成
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(extract_dir, exist_ok=True)
    os.makedirs(target_lib_dir, exist_ok=True)
    
    print("Downloading LightGBM wheel...")
    # pip download コマンドを実行
    cmd = [
        sys.executable, "-m", "pip", "download", 
        "lightgbm==4.1.0", 
        "--platform", "manylinux_2_28_x86_64", 
        "--no-deps", 
        "-d", temp_dir, 
        "--only-binary=:all:", 
        "--python-version", "3.12"
    ]
    subprocess.check_call(cmd)
    
    # ダウンロードしたwhlファイルを探す
    whl_file = None
    for f in os.listdir(temp_dir):
        if f.endswith(".whl"):
            whl_file = os.path.join(temp_dir, f)
            break
            
    if not whl_file:
        print("Error: Wheel file not found.")
        return
        
    print(f"Extracting {whl_file}...")
    with zipfile.ZipFile(whl_file, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    print("Searching for libraries...")
    found_count = 0
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            # libgomp または lib_lightgbm を探す
            if "libgomp" in file or "lib_lightgbm" in file:
                source_path = os.path.join(root, file)
                target_path = os.path.join(target_lib_dir, file)
                print(f"Copying {file} to {target_lib_dir}")
                shutil.copy2(source_path, target_path)
                found_count += 1
                
    if found_count > 0:
        print(f"Success! {found_count} libraries copied.")
    else:
        print("Warning: No libraries found.")
        
    # クリーンアップ
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    download_and_extract()
