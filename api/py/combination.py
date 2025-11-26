"""
Vercel Python関数: 組み合わせ予測

/api/py/combination エンドポイントとして動作します。
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
        extract_combination_features,
        add_pattern_id_features,
        add_keisen_pattern_features,
        features_to_vector,
        get_rehearsal_positions
    )
    import pandas as pd
    import numpy as np
    IMPORTS_OK = True
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    IMPORTS_OK = False

# グローバル変数
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
            df = pd.read_csv(csv_path)
            df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
            df['n4_winning'] = df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
            df['n3_winning'] = df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' else x)
            df['n4_winning'] = df['n4_winning'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' else x)
    
    if keisen_master is None:
        keisen_master = load_keisen_master(DATA_DIR)


def predict_combination_logic(data):
    """組み合わせ予測のロジック"""
    import io

    round_number = int(data.get('round_number'))
    target = data.get('target', 'n3')
    combo_type = data.get('combo_type', 'box')
    best_pattern = data.get('best_pattern', 'A1')
    top_axis_digits = data.get('top_axis_digits', [])
    rehearsal_digits = data.get('rehearsal_digits')
    max_combinations = int(data.get('max_combinations', 100))
    csv_content = data.get('csv_content')

    # データ読み込み
    current_df = None
    
    if csv_content:
        try:
            current_df = pd.read_csv(io.StringIO(csv_content))
            # 前処理
            current_df['n3_winning'] = current_df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
            current_df['n4_winning'] = current_df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
            current_df['n3_winning'] = current_df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' else x)
            current_df['n4_winning'] = current_df['n4_winning'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' else x)
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
    
    # 予測表を生成
    grid, rows, cols = generate_chart(current_df, keisen_master, round_number, best_pattern, target)
    
    rehearsal_positions = None
    if rehearsal_digits:
        rehearsal_positions = get_rehearsal_positions(grid, rows, cols, rehearsal_digits)
    
    # 組み合わせを生成
    # ボックス: ソートされた組み合わせ（順序無視）
    # ストレート: ボックス候補の順列（全ての並び順）
    from itertools import permutations
    
    # まずボックス候補を生成（ストレートでも同じベース候補を使う）
    box_combinations_set = set()
    for axis_digit in top_axis_digits[:5]:
        other_digits = [d for d in range(10) if d != axis_digit]
        
        if target == 'n3':
            for i, d1 in enumerate(other_digits):
                for d2 in other_digits[i+1:]:
                    digits = [axis_digit, d1, d2]
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
        else:  # n4
            for i, d1 in enumerate(other_digits):
                for j, d2 in enumerate(other_digits[i+1:]):
                    for d3 in other_digits[i+j+2:]:
                        digits = [axis_digit, d1, d2, d3]
                        combo = ''.join(map(str, sorted(digits)))
                        box_combinations_set.add(combo)
        
        if len(box_combinations_set) >= max_combinations:
            break
    
    # ボックスならそのまま、ストレートなら順列を展開
    if combo_type == 'box':
        combinations = list(box_combinations_set)[:max_combinations]
    else:
        # ストレート: ボックス候補の順列を生成
        straight_combinations_set = set()
        for box_combo in box_combinations_set:
            digits = [int(d) for d in box_combo]
            for perm in permutations(digits):
                straight_combo = ''.join(map(str, perm))
                straight_combinations_set.add(straight_combo)
                if len(straight_combinations_set) >= max_combinations * 6:  # 順列は多いので上限を増やす
                    break
            if len(straight_combinations_set) >= max_combinations * 6:
                break
        combinations = list(straight_combinations_set)[:max_combinations]
    
    # モデル確認
    model_name = f"{target}_{combo_type}_comb"
    if model_name not in model_loader.get_available_models():
        return {'success': True, 'combinations': []}
    
    # 前回・前々回の当選番号を取得
    previous_winning = None
    previous_previous_winning = None
    previous_row = current_df[current_df['round_number'] == round_number - 1]
    previous_previous_row = current_df[current_df['round_number'] == round_number - 2]
    
    if len(previous_row) > 0:
        previous_winning = str(previous_row[f'{target}_winning'].iloc[0]).replace('.0', '')
        if target == 'n3' and len(previous_winning) < 3:
            previous_winning = previous_winning.zfill(3)
        elif target == 'n4' and len(previous_winning) < 4:
            previous_winning = previous_winning.zfill(4)
    
    if len(previous_previous_row) > 0:
        previous_previous_winning = str(previous_previous_row[f'{target}_winning'].iloc[0]).replace('.0', '')
        if target == 'n3' and len(previous_previous_winning) < 3:
            previous_previous_winning = previous_previous_winning.zfill(3)
        elif target == 'n4' and len(previous_previous_winning) < 4:
            previous_previous_winning = previous_previous_winning.zfill(4)
    
    # 特徴量キーを取得（モデルが期待する順序）
    model_name = f"{target}_{combo_type}_comb"
    feature_keys = model_loader.feature_keys.get(model_name, [])
    
    if feature_keys:
        print(f"[INFO] モデル {model_name} の特徴量キー数: {len(feature_keys)}")
    
    # 特徴量を抽出して予測
    combo_scores = []
    for combo in combinations[:max_combinations]:
        features = extract_combination_features(grid, rows, cols, combo, rehearsal_positions)
        features = add_pattern_id_features(features, best_pattern)
        
        if previous_winning and previous_previous_winning:
            features = add_keisen_pattern_features(
                features, previous_winning, previous_previous_winning, target
            )
        
        # 特徴量キーに基づいてベクトル化（モデルが期待する順序で）
        if feature_keys:
            feature_vector = features_to_vector(features, feature_keys)
        else:
            feature_vector = features_to_vector(features)
        
        try:
            raw_score = model_loader.predict_combination(target, combo_type, feature_vector.reshape(1, -1))[0]
            
            # デバッグ: 最初の数件のraw_scoreを出力
            if len(combo_scores) < 3:
                print(f"[DEBUG] combo={combo}, raw_score={raw_score}, feature_dim={len(feature_vector)}")
            
            # raw_scoreをそのまま保存（後で正規化）
            combo_scores.append({
                'combination': combo,
                'raw_score': raw_score
            })
        except ValueError as e:
            if "モデルが見つかりません" in str(e):
                print(f"[WARN] モデルが見つかりません: {model_name}")
                break
            raise
    
    # raw_scoreを正規化してスコア化（相対的な差を反映）
    if combo_scores:
        raw_scores = [c['raw_score'] for c in combo_scores]
        min_raw = min(raw_scores)
        max_raw = max(raw_scores)
        score_range = max_raw - min_raw
        
        if score_range > 0:
            # 正規化: 最小を100、最大を999にマッピング
            for c in combo_scores:
                normalized = (c['raw_score'] - min_raw) / score_range
                c['score'] = int(100 + normalized * 899)  # 100-999の範囲
        else:
            # 全て同じスコアの場合
            for c in combo_scores:
                c['score'] = 500
        
        # raw_scoreを削除（レスポンスに含めない）
        for c in combo_scores:
            del c['raw_score']
    
    combo_scores.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'success': True,
        'combinations': combo_scores
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
            
            result = predict_combination_logic(data)
            
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
