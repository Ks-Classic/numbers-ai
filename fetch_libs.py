import urllib.request
import zipfile
import os
import shutil

# LightGBMのx86_64用WheelファイルのURL (PyPIから)
# manylinux_2_28_x86_64対応のバージョン4.1.0を使用
WHEEL_URL = "https://files.pythonhosted.org/packages/e1/4c/4685ccfae9806f561de716e32549190c1520e31690b1319d06e25d27d722/lightgbm-4.1.0-py3-none-manylinux_2_28_x86_64.whl"
DOWNLOAD_PATH = "lightgbm_x86_64.whl"
EXTRACT_DIR = "temp_extract"
TARGET_LIB_DIR = "api/lib"

def download_and_extract_libgomp():
    print(f"Downloading {WHEEL_URL}...")
    try:
        urllib.request.urlretrieve(WHEEL_URL, DOWNLOAD_PATH)
        print("Download complete.")
    except Exception as e:
        print(f"Download failed: {e}")
        return

    print("Extracting wheel...")
    try:
        with zipfile.ZipFile(DOWNLOAD_PATH, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)
        
        # 抽出したディレクトリから共有ライブラリを探す
        # 通常は lightgbm/lib_lightgbm.so や 依存ライブラリがある
        # manylinuxホイールには依存ライブラリがバンドルされていることが多い
        
        found = False
        os.makedirs(TARGET_LIB_DIR, exist_ok=True)
        
        # 再帰的に .so ファイルを探す
        for root, dirs, files in os.walk(EXTRACT_DIR):
            for file in files:
                if "libgomp" in file or "lib_lightgbm" in file:
                    source_path = os.path.join(root, file)
                    target_path = os.path.join(TARGET_LIB_DIR, file)
                    print(f"Found library: {file}")
                    shutil.copy2(source_path, target_path)
                    found = True
                    
        if found:
            print(f"Success! Libraries copied to {TARGET_LIB_DIR}")
            print("Files in api/lib:")
            for f in os.listdir(TARGET_LIB_DIR):
                print(f" - {f}")
        else:
            print("Warning: libgomp not found in the wheel. This might be a problem.")
            
    except Exception as e:
        print(f"Extraction failed: {e}")
    finally:
        # クリーンアップ
        if os.path.exists(DOWNLOAD_PATH):
            os.remove(DOWNLOAD_PATH)
        if os.path.exists(EXTRACT_DIR):
            shutil.rmtree(EXTRACT_DIR)

if __name__ == "__main__":
    download_and_extract_libgomp()
