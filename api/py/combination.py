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
    import os
    import csv  # pandasの代わりにcsvを使用
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
    
    # 予測表を生成（NULL補完機能付き）
    try:
        grid, rows, cols = generate_chart(current_df, keisen_master, round_number, best_pattern, target)
    except Exception as chart_error:
        # ChartGenerationErrorで、当選番号が未登録の場合 - 自動的にWebから取得して再試行
        error_msg = str(chart_error)
        if '当選番号が未登録です' in error_msg or 'NULL' in error_msg:
            print(f"[INFO] 当選番号が未登録のため、Webから最新データを取得します: {error_msg}")
            
            # fetch_data.pyのfetch_and_update関数を呼び出し
            try:
                # Vercel環境でもインポートできるようにパスを明示的に追加
                import sys
                from pathlib import Path
                current_file_dir = Path(__file__).resolve().parent
                if str(current_file_dir) not in sys.path:
                    sys.path.insert(0, str(current_file_dir))
                
                # 同じディレクトリのfetch_data.pyをインポート
                from fetch_data import fetch_and_update
                
                fetch_result = fetch_and_update(round_number)
                
                if fetch_result.get('success') and fetch_result.get('updated'):
                    print(f"[INFO] データ更新成功: {fetch_result.get('message')}")
                    
                    # 更新されたCSVで再度データを読み込み
                    if fetch_result.get('csv_content'):
                        try:
                            current_df = []
                            reader = csv.DictReader(fetch_result['csv_content'].splitlines())
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
                            
                            # 再試行
                            print("[INFO] 更新されたデータで予測表を再生成します")
                            grid, rows, cols = generate_chart(current_df, keisen_master, round_number, best_pattern, target)
                            print("[INFO] 予測表の再生成に成功しました")
                        except Exception as retry_error:
                            return {
                                'success': False, 
                                'error': f'データ更新後の予測表生成に失敗: {retry_error}'
                            }
                    else:
                        return {
                            'success': False,
                            'error': f'データ更新に成功しましたが、CSVコンテンツが取得できませんでした'
                        }
                else:
                    # Webにもデータがない場合
                    return {
                        'success': False,
                        'error': f'予測エラー: {error_msg}\n\n公式サイトにも当選番号が未発表です。当選番号が発表されてからお試しください。'
                    }
            except Exception as fetch_error:
                print(f"[ERROR] データ自動取得エラー: {fetch_error}")
                return {
                    'success': False,
                    'error': f'予測エラー: {error_msg}\n\n自動データ取得にも失敗しました: {fetch_error}'
                }
        else:
            # その他のエラーはそのまま再送出
            raise
    
    rehearsal_positions = None
    if rehearsal_digits:
        rehearsal_positions = get_rehearsal_positions(grid, rows, cols, rehearsal_digits)
    
    # 組み合わせを生成
    # ボックス: ソートされた組み合わせ（順序無視）
    # ストレート: ボックス候補の順列（全ての並び順）
    from itertools import permutations, combinations as itertools_combinations
    
    # まずボックス候補を生成（ストレートでも同じベース候補を使う）
    # ダブル（同じ数字が2つ以上被る）ケースも含める
    from itertools import combinations_with_replacement
    
    box_combinations_set = set()
    all_digits = list(range(10))
    
    for axis_digit in top_axis_digits[:5]:
        if target == 'n3':
            # N3: 軸数字 + 他の2桁（ダブル含む）
            # パターン1: 軸数字が1つ + 異なる2つの数字（従来通り）
            for combo_pair in itertools_combinations(all_digits, 2):
                if axis_digit not in combo_pair:
                    digits = [axis_digit] + list(combo_pair)
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
            
            # パターン2: 軸数字が2つ（ダブル）+ 異なる1つの数字
            for other in all_digits:
                if other != axis_digit:
                    digits = [axis_digit, axis_digit, other]
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
            
            # パターン3: 軸数字 + 同じ数字2つ（他のダブル）
            for other in all_digits:
                if other != axis_digit:
                    digits = [axis_digit, other, other]
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
            
            # パターン4: ゾロ目（軸数字が3つ）
            combo = ''.join([str(axis_digit)] * 3)
            box_combinations_set.add(combo)
            
        else:  # n4
            # N4: 軸数字 + 他の3桁（ダブル含む）
            # パターン1: 軸数字が1つ + 異なる3つの数字（従来通り）
            for combo_triple in itertools_combinations(all_digits, 3):
                if axis_digit not in combo_triple:
                    digits = [axis_digit] + list(combo_triple)
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
            
            # パターン2: 軸数字が2つ（ダブル）+ 異なる2つの数字
            for combo_pair in itertools_combinations(all_digits, 2):
                if axis_digit not in combo_pair:
                    digits = [axis_digit, axis_digit] + list(combo_pair)
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
            
            # パターン3: 軸数字 + 別の数字が2つ（ダブル）+ さらに別の数字1つ
            for d1 in all_digits:
                if d1 == axis_digit:
                    continue
                for d2 in all_digits:
                    if d2 == axis_digit or d2 == d1:
                        continue
                    digits = [axis_digit, d1, d1, d2]
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
            
            # パターン4: 軸数字が3つ（トリプル）+ 異なる1つの数字
            for other in all_digits:
                if other != axis_digit:
                    digits = [axis_digit, axis_digit, axis_digit, other]
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
            
            # パターン5: 軸数字が2つ + 別の数字が2つ（ダブルダブル）
            for other in all_digits:
                if other != axis_digit:
                    digits = [axis_digit, axis_digit, other, other]
                    combo = ''.join(map(str, sorted(digits)))
                    box_combinations_set.add(combo)
            
            # パターン6: ゾロ目（軸数字が4つ）
            combo = ''.join([str(axis_digit)] * 4)
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
    # 前回・前々回の当選番号を取得
    previous_winning = None
    previous_previous_winning = None
    
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
    
    # スコア順にソート
    combo_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 重複排除（同じ番号は最初の1つだけを残す）
    seen_combinations = set()
    unique_combo_scores = []
    for c in combo_scores:
        if c['combination'] not in seen_combinations:
            seen_combinations.add(c['combination'])
            unique_combo_scores.append(c)
    
    return {
        'success': True,
        'combinations': unique_combo_scores
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
