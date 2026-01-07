"""
Vercel Python関数: 軸数字予測

/api/py/axis エンドポイントとして動作します。
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'core'))

# 【重要】Vercel環境(x86_64)用の共有ライブラリを強制ロード
import ctypes

# カレントディレクトリにあるlibgomp.so.1を探す
current_dir = Path(__file__).resolve().parent
lib_path = current_dir / 'libgomp.so.1'

if lib_path.exists():
    try:
        ctypes.CDLL(str(lib_path), mode=ctypes.RTLD_GLOBAL)
        print(f"[INFO] Successfully loaded {lib_path}")
    except Exception as e:
        print(f"[WARN] Failed to load {lib_path}: {e}")

# モジュールインポート
try:
    from model_loader import load_model_loader
    from chart_generator import load_keisen_master, generate_chart
    from feature_extractor import (
        extract_digit_features,
        add_pattern_id_features,
        add_keisen_pattern_features,
        features_to_vector,
        get_rehearsal_positions
    )
    # モジュールのインポート
    import os
    import csv  # pandasの代わりにcsvを使用
    
    # 共通モジュールのインポート
    import lightgbm as lgb
    import numpy as np
    IMPORTS_OK = True
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    IMPORTS_OK = False

# グローバル変数（モデルとデータ）
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'
model_loader = None
df = None
keisen_master = None


def load_data_and_models():
    """モデルとデータを読み込む"""
    global model_loader, df, keisen_master
    
    if model_loader is None:
        model_loader = load_model_loader(MODELS_DIR)
    
    if df is None:
        csv_path = DATA_DIR / 'past_results.csv'
        if csv_path.exists():
            data_list = []
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 前処理
                        n3 = str(row.get('n3_winning', '')).replace('.0', '')
                        n4 = str(row.get('n4_winning', '')).replace('.0', '')
                        
                        if n3 and n3.upper() not in ('NULL', 'NAN', 'NONE'):
                            row['n3_winning'] = n3.zfill(3)
                        else:
                             row['n3_winning'] = None
                        
                        if n4 and n4.upper() not in ('NULL', 'NAN', 'NONE'):
                            row['n4_winning'] = n4.zfill(4)
                        else:
                            row['n4_winning'] = None
                            
                        data_list.append(row)
                df = data_list
            except Exception as e:
                print(f"[ERROR] CSV読み込み失敗: {e}")
                df = []
    
    if keisen_master is None:
        keisen_master = load_keisen_master(DATA_DIR)


def predict_axis_logic(data):
    """軸数字予測のロジック"""
    import io

    round_number = int(data.get('round_number'))
    target = data.get('target', 'n3')
    rehearsal_digits = data.get('rehearsal_digits')
    csv_content = data.get('csv_content')

    # データ読み込み
    current_df = None
    
    if csv_content:
        try:
            current_df = []
            # CSV文字列をパース
            reader = csv.DictReader(csv_content.splitlines())
            for row in reader:
                # 前処理
                n3 = str(row.get('n3_winning', '')).replace('.0', '')
                n4 = str(row.get('n4_winning', '')).replace('.0', '')
                
                if n3 and n3.upper() not in ('NULL', 'NAN', 'NONE'):
                    row['n3_winning'] = n3.zfill(3)
                else:
                    row['n3_winning'] = None
                
                if n4 and n4.upper() not in ('NULL', 'NAN', 'NONE'):
                    row['n4_winning'] = n4.zfill(4)
                else:
                    row['n4_winning'] = None
                    
                current_df.append(row)
        except Exception as e:
            return {'success': False, 'error': f'CSVデータの解析に失敗: {e}'}
    else:
        # 通常のデータ読み込み
        load_data_and_models()
        if df is None:
            return {'success': False, 'error': 'データが読み込まれていません'}
        current_df = df

    # モデル読み込み（データとは独立）
    if model_loader is None:
        load_data_and_models() # モデルだけロードするために呼ぶ（dfはロード済みならスキップされる）
    
    if model_loader is None:
        return {'success': False, 'error': 'モデルが読み込まれていません'}
    
    if keisen_master is None:
        load_data_and_models()
        
    if keisen_master is None:
        return {'success': False, 'error': '罫線マスターが読み込まれていません'}
    
    # 以下、dfの代わりにcurrent_dfを使用
    patterns = ['A1', 'A2', 'B1', 'B2']
    pattern_results = {}
    pattern_max_scores = {}
    
    for pattern in patterns:
        try:
            grid, rows, cols = generate_chart(current_df, keisen_master, round_number, pattern, target)
            
            rehearsal_positions = None
            if rehearsal_digits:
                rehearsal_positions = get_rehearsal_positions(grid, rows, cols, rehearsal_digits)
            
            previous_winning = None
            # リストから検索するヘルパー
            def to_int(val):
                try: return int(float(str(val)))
                except: return -1

            target_prev = round_number - 1
            target_prev_prev = round_number - 2
            
            # リストフィルタリング
            previous_row = next((r for r in current_df if to_int(r.get('round_number')) == target_prev), None)
            previous_previous_row = next((r for r in current_df if to_int(r.get('round_number')) == target_prev_prev), None)
            
            if previous_row:
                previous_winning = str(previous_row.get(f'{target}_winning') or '').replace('.0', '')
                if target == 'n3' and len(previous_winning) < 3:
                    previous_winning = previous_winning.zfill(3)
                elif target == 'n4' and len(previous_winning) < 4:
                    previous_winning = previous_winning.zfill(4)
            
            if previous_previous_row:
                previous_previous_winning = str(previous_previous_row.get(f'{target}_winning') or '').replace('.0', '')
                if target == 'n3' and len(previous_previous_winning) < 3:
                    previous_previous_winning = previous_previous_winning.zfill(3)
                elif target == 'n4' and len(previous_previous_winning) < 4:
                    previous_previous_winning = previous_previous_winning.zfill(4)
            
            # 特徴量キーを取得（モデルが期待する順序）
            model_name = f"{target}_axis"
            feature_keys = model_loader.feature_keys.get(model_name, [])
            
            digit_scores = []
            for digit in range(10):
                features = extract_digit_features(grid, rows, cols, digit, rehearsal_positions)
                features = add_pattern_id_features(features, pattern)
                
                if previous_winning and previous_previous_winning:
                    features = add_keisen_pattern_features(
                        features, previous_winning, previous_previous_winning, target
                    )
                
                # 特徴量キーに基づいてベクトル化（モデルが期待する順序で）
                if feature_keys:
                    feature_vector = features_to_vector(features, feature_keys)
                else:
                    feature_vector = features_to_vector(features)
                raw_score = model_loader.predict_axis(target, feature_vector.reshape(1, -1))[0]
                
                # raw_scoreをそのまま保存（後で正規化）
                digit_scores.append({
                    'digit': digit,
                    'raw_score': raw_score,
                    'pattern': pattern
                })
            
            # raw_scoreを正規化してスコア化（相対的な差を反映）
            if digit_scores:
                raw_scores = [d['raw_score'] for d in digit_scores]
                min_raw = min(raw_scores)
                max_raw = max(raw_scores)
                score_range = max_raw - min_raw
                
                if score_range > 0:
                    # 正規化: 最小を100、最大を999にマッピング
                    for d in digit_scores:
                        normalized = (d['raw_score'] - min_raw) / score_range
                        d['score'] = int(100 + normalized * 899)  # 100-999の範囲
                else:
                    # 全て同じスコアの場合
                    for d in digit_scores:
                        d['score'] = 500
                
                # raw_scoreを削除
                for d in digit_scores:
                    del d['raw_score']
            
            digit_scores.sort(key=lambda x: x['score'], reverse=True)
            pattern_results[pattern] = digit_scores
            
            if digit_scores:
                pattern_max_scores[pattern] = max(s['score'] for s in digit_scores)
        
        except Exception as e:
            print(f"[ERROR] パターン{pattern}の予測に失敗: {e}")
            pattern_results[pattern] = []
    
    if pattern_max_scores:
        best_pattern = max(pattern_max_scores.items(), key=lambda x: x[1])[0]
    else:
        best_pattern = 'A1'
    
    all_axis_scores = {}
    for pattern, digit_scores in pattern_results.items():
        for item in digit_scores:
            digit = item['digit']
            score = item['score']
            if digit not in all_axis_scores or score > all_axis_scores[digit]['score']:
                all_axis_scores[digit] = {
                    'digit': digit,
                    'score': score,
                    'pattern': pattern
                }
    
    axis_candidates = sorted(all_axis_scores.values(), key=lambda x: x['score'], reverse=True)
    
    return {
        'success': True,
        'best_pattern': best_pattern,
        'pattern_scores': {p: pattern_max_scores.get(p, 0.0) for p in patterns},
        'axis_candidates': axis_candidates
    }


class handler(BaseHTTPRequestHandler):
    """Vercel Python Serverless Function Handler"""
    
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """POST リクエスト処理"""
        try:
            if not IMPORTS_OK:
                self._send_error(500, 'サーバー初期化エラー: モジュールのインポートに失敗しました')
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            result = predict_axis_logic(data)
            
            if result.get('success'):
                self._send_json(200, result)
            else:
                self._send_error(500, result.get('error', '予測エラー'))
        
        except json.JSONDecodeError as e:
            self._send_error(400, f'無効なJSON: {e}')
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._send_error(500, f'予測エラー: {e}')
    
    def _send_json(self, status_code, data):
        """JSONレスポンスを送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, status_code, message):
        """エラーレスポンスを送信"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'success': False, 'error': message}).encode('utf-8'))
