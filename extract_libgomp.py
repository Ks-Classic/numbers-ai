import urllib.request
import gzip
import os
import io

# RPMファイルのURL (CentOS 7 x86_64用 libgomp)
url = "http://mirror.centos.org/centos/7/os/x86_64/Packages/libgomp-4.8.5-44.el7.x86_64.rpm"
output_dir = "api/lib"
os.makedirs(output_dir, exist_ok=True)

print(f"Downloading {url}...")
try:
    # ダウンロード
    with urllib.request.urlopen(url) as response:
        rpm_data = response.read()
    
    print("Download complete. Extracting...")
    
    # RPMヘッダーをスキップしてGZIP圧縮されたCPIOアーカイブを探す
    # マジックナンバー: 1f 8b 08 (GZIP)
    gzip_magic = b'\x1f\x8b\x08'
    start = rpm_data.find(gzip_magic)
    
    if start == -1:
        print("Error: Could not find GZIP header in RPM.")
        exit(1)
        
    gz_data = rpm_data[start:]
    
    # GZIP解凍
    with gzip.GzipFile(fileobj=io.BytesIO(gz_data)) as f:
        cpio_data = f.read()
        
    # CPIOアーカイブから libgomp.so.1 を探す
    # CPIO (New ASCII Format) の解析は複雑なので、単純なバイト列検索でファイル内容を特定するのは危険
    # 代わりに、一時ファイルに保存してシステムコマンドで...いや、rpm2cpioがないんだった。
    
    # 仕方ないので、もっと確実なソース（GitHubなど）から直接 .so をダウンロードする
    # あるいは、PythonでCPIOを解凍するライブラリを使う（標準ではない）
    
    print("Complex extraction required. Switching strategy.")
    
except Exception as e:
    print(f"Error: {e}")
