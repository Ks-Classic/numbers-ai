"""
Vercel Python関数: デバッグテスト
"""

import os
import sys
from pathlib import Path

# 【重要】LightGBMインポート前にlibgomp.so.1をロード
current_dir = Path(__file__).resolve().parent
libgomp_path = current_dir / 'libgomp.so.1'

if libgomp_path.exists():
    # LD_LIBRARY_PATH を設定
    os.environ['LD_LIBRARY_PATH'] = str(current_dir) + ':' + os.environ.get('LD_LIBRARY_PATH', '')
    
    # ctypes で明示的にロード
    import ctypes
    try:
        ctypes.CDLL(str(libgomp_path), mode=ctypes.RTLD_GLOBAL)
        LIBGOMP_LOADED = True
    except Exception as e:
        LIBGOMP_LOADED = f"FAIL: {e}"
else:
    LIBGOMP_LOADED = "NOT_FOUND"

from http.server import BaseHTTPRequestHandler
import json


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
            
            # モデルロードテスト
            models_dir = project_root / 'data' / 'models'
            import_results['models_dir_exists'] = models_dir.exists()
            if models_dir.exists():
                import_results['model_files'] = [f.name for f in models_dir.iterdir() if f.suffix == '.pkl']
                
                # 実際にモデルをロード
                try:
                    loader = load_model_loader(models_dir)
                    import_results['model_loader_init'] = "OK"
                    import_results['available_models'] = loader.get_available_models()
                    
                    # 個別のモデルファイルを直接読み込んでテスト
                    import pickle
                    test_model_path = models_dir / 'n3_axis_lgb.pkl'
                    if test_model_path.exists():
                        try:
                            with open(test_model_path, 'rb') as f:
                                test_model = pickle.load(f)
                            import_results['direct_pickle_load'] = f"OK: type={type(test_model).__name__}"
                        except Exception as e:
                            import_results['direct_pickle_load'] = f"FAIL: {e}"
                except Exception as e:
                    import traceback
                    import_results['model_loader_init'] = f"FAIL: {e}"
                    import_results['model_loader_traceback'] = traceback.format_exc()
        except Exception as e:
            import_results['model_loader'] = f"FAIL: {e}"
        
        # past_results.csv 確認
        csv_path = project_root / 'data' / 'past_results.csv'
        info['past_results_exists'] = csv_path.exists()
        if csv_path.exists():
            import pandas as pd
            df = pd.read_csv(csv_path)
            info['past_results_rows'] = len(df)
            info['past_results_columns'] = list(df.columns)
        
        info['imports'] = import_results
        
        # レスポンス送信
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(info, indent=2, default=str).encode('utf-8'))

