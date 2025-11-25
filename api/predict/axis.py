"""
Vercel Python関数: 軸数字予測

/api/predict/axis エンドポイントとして動作します。
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT / 'core'))

# 【重要】Vercel環境(x86_64)用の共有ライブラリを強制ロード
import ctypes
lib_path = PROJECT_ROOT / 'api' / 'lib' / 'libgomp.so.1'
if lib_path.exists():
    try:
        # RTLD_GLOBALモードでロードして、LightGBMからも見えるようにする
        ctypes.CDLL(str(lib_path), mode=ctypes.RTLD_GLOBAL)
        print(f"Successfully loaded {lib_path} with RTLD_GLOBAL")
    except Exception as e:
        print(f"Failed to load {lib_path}: {e}")

# デバッグ: パスと環境確認
print(f"Python Path: {sys.path}")
try:
    import numpy
    print(f"NumPy found at: {numpy.__file__}")
except ImportError as e:
    print(f"NumPy import failed: {e}")

from model_loader import load_model_loader
from chart_generator import load_keisen_master, generate_chart, ChartGenerationError
from feature_extractor import (
    extract_digit_features,
    add_pattern_id_features,
    add_keisen_pattern_features,
    features_to_vector,
    get_rehearsal_positions
)
import pandas as pd
import numpy as np

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
            df = pd.read_csv(csv_path)
            # 当選番号を文字列型に変換
            df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
            df['n4_winning'] = df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
            # 先頭0を補完
            df['n3_winning'] = df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' else x)
            df['n4_winning'] = df['n4_winning'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' else x)
    
    if keisen_master is None:
        keisen_master = load_keisen_master(DATA_DIR)


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Vercel Python関数のハンドラー
    
    Args:
        event: イベントデータ（Vercelの形式）
            - body: str (JSON文字列)
        context: コンテキスト（未使用）
    
    Returns:
        レスポンスデータ
    """
    try:
        # データとモデルを読み込む
        load_data_and_models()
        
        if model_loader is None:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'モデルが読み込まれていません'})
            }
        
        if df is None or keisen_master is None:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'データが読み込まれていません'})
            }
        
        # リクエストデータを取得
        body = event.get('body', '{}')
        if isinstance(body, str):
            data = json.loads(body)
        else:
            data = body
        
        round_number = int(data.get('round_number'))
        target = data.get('target', 'n3')
        rehearsal_digits = data.get('rehearsal_digits')
        
        patterns = ['A1', 'A2', 'B1', 'B2']
        pattern_results = {}
        pattern_max_scores = {}
        
        # 各パターンで予測を実行
        for pattern in patterns:
            try:
                # 予測表を生成
                grid, rows, cols = generate_chart(
                    df, keisen_master, round_number, pattern, target
                )
                
                # リハーサル位置を取得
                rehearsal_positions = None
                if rehearsal_digits:
                    rehearsal_positions = get_rehearsal_positions(
                        grid, rows, cols, rehearsal_digits
                    )
                
                # 前回・前々回の当選番号を取得（罫線パターン特徴量用）
                previous_winning = None
                previous_previous_winning = None
                previous_row = df[df['round_number'] == round_number - 1]
                previous_previous_row = df[df['round_number'] == round_number - 2]
                
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
                
                # 各数字（0-9）の特徴量を抽出して予測
                digit_scores = []
                for digit in range(10):
                    features = extract_digit_features(
                        grid, rows, cols, digit, rehearsal_positions
                    )
                    features = add_pattern_id_features(features, pattern)
                    
                    # 罫線パターンID特徴量を追加
                    if previous_winning and previous_previous_winning:
                        features = add_keisen_pattern_features(
                            features, previous_winning, previous_previous_winning, target
                        )
                    
                    feature_vector = features_to_vector(features)
                    
                    # 予測確率を取得
                    proba = model_loader.predict_axis(
                        target, feature_vector.reshape(1, -1)
                    )[0]
                    
                    # スコア算出（確率 × 1000）
                    score = proba * 1000
                    digit_scores.append({
                        'digit': digit,
                        'score': float(score),
                        'pattern': pattern
                    })
                
                # スコア順にソート（降順）
                digit_scores.sort(key=lambda x: x['score'], reverse=True)
                pattern_results[pattern] = digit_scores
                
                # パターンの最高スコアを記録
                if digit_scores:
                    pattern_max_scores[pattern] = max(s['score'] for s in digit_scores)
            
            except Exception as e:
                print(f"エラー: パターン{pattern}の予測に失敗しました: {e}")
                pattern_results[pattern] = []
        
        # 最良パターンを特定（最高スコアが最も高いパターン）
        if pattern_max_scores:
            best_pattern = max(pattern_max_scores.items(), key=lambda x: x[1])[0]
        else:
            best_pattern = 'A1'
        
        # 全パターン統合の軸数字ランキング
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
        
        axis_candidates = sorted(
            all_axis_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'best_pattern': best_pattern,
                'pattern_scores': {p: pattern_max_scores.get(p, 0.0) for p in patterns},
                'axis_candidates': axis_candidates
            })
        }
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'予測エラー: {error_msg}'})
        }

