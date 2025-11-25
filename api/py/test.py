"""
Vercel Python関数: デバッグテスト
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from pathlib import Path


class handler(BaseHTTPRequestHandler):
    """テストハンドラー"""
    
    def do_GET(self):
        """GET リクエスト処理"""
        # 環境情報を収集
        info = {
            'python_version': sys.version,
            'cwd': os.getcwd(),
            'sys_path': sys.path[:10],
            'file_location': str(Path(__file__).resolve()),
            'parent_dir': str(Path(__file__).resolve().parent),
            'project_root': str(Path(__file__).resolve().parent.parent.parent),
        }
        
        # core/ ディレクトリの存在確認
        project_root = Path(__file__).resolve().parent.parent.parent
        core_dir = project_root / 'core'
        info['core_exists'] = core_dir.exists()
        
        if core_dir.exists():
            info['core_files'] = [f.name for f in core_dir.iterdir() if f.is_file()]
        
        # data/ ディレクトリの確認
        data_dir = project_root / 'data'
        info['data_exists'] = data_dir.exists()
        
        # libgomp.so.1 の確認
        current_dir = Path(__file__).resolve().parent
        libgomp_path = current_dir / 'libgomp.so.1'
        info['libgomp_exists'] = libgomp_path.exists()
        
        # インポートテスト
        import_results = {}
        
        try:
            import numpy
            import_results['numpy'] = f"OK: {numpy.__version__}"
        except Exception as e:
            import_results['numpy'] = f"FAIL: {e}"
        
        try:
            import pandas
            import_results['pandas'] = f"OK: {pandas.__version__}"
        except Exception as e:
            import_results['pandas'] = f"FAIL: {e}"
        
        try:
            import lightgbm
            import_results['lightgbm'] = f"OK: {lightgbm.__version__}"
        except Exception as e:
            import_results['lightgbm'] = f"FAIL: {e}"
        
        # core モジュールのインポートテスト
        sys.path.insert(0, str(project_root / 'core'))
        try:
            from model_loader import load_model_loader
            import_results['model_loader'] = "OK"
        except Exception as e:
            import_results['model_loader'] = f"FAIL: {e}"
        
        info['imports'] = import_results
        
        # レスポンス送信
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(info, indent=2, default=str).encode('utf-8'))

