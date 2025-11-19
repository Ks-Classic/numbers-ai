"""
Vercel Python関数: 組み合わせ予測

/api/predict/combination エンドポイントとして動作します。
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT / 'core'))

from model_loader import load_model_loader
from chart_generator import load_keisen_master, generate_chart, ChartGenerationError
from feature_extractor import (
    extract_combination_features,
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
        model_loader = load_model_loader(MODELS_DIR, use_lightgbm=True)
    
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
        combo_type = data.get('combo_type', 'box')
        best_pattern = data.get('best_pattern', 'A1')
        top_axis_digits = data.get('top_axis_digits', [])
        rehearsal_digits = data.get('rehearsal_digits')
        max_combinations = int(data.get('max_combinations', 100))
        
        # 予測表を生成
        grid, rows, cols = generate_chart(
            df, keisen_master, round_number, best_pattern, target
        )
        
        # リハーサル位置を取得
        rehearsal_positions = None
        if rehearsal_digits:
            rehearsal_positions = get_rehearsal_positions(
                grid, rows, cols, rehearsal_digits
            )
        
        # 組み合わせを生成（軸数字を含む組み合わせを優先）
        digit_count = 3 if target == 'n3' else 4
        combinations = []
        
        # 軸数字を含む組み合わせを生成
        for axis_digit in top_axis_digits[:5]:  # 上位5つの軸数字を使用
            other_digits = [d for d in range(10) if d != axis_digit]
            
            if target == 'n3':
                # N3: 軸数字 + 他の2数字
                for i, d1 in enumerate(other_digits):
                    for d2 in other_digits[i+1:]:
                        combo = ''.join(map(str, sorted([axis_digit, d1, d2])))
                        if combo not in combinations:
                            combinations.append(combo)
            else:
                # N4: 軸数字 + 他の3数字
                for i, d1 in enumerate(other_digits):
                    for j, d2 in enumerate(other_digits[i+1:]):
                        for d3 in other_digits[i+j+2:]:
                            combo = ''.join(map(str, sorted([axis_digit, d1, d2, d3])))
                            if combo not in combinations:
                                combinations.append(combo)
            
            if len(combinations) >= max_combinations:
                break
        
        # モデルが存在するか確認
        model_name = f"{target}_{combo_type}_comb"
        if model_name not in model_loader.get_available_models():
            # モデルが見つからない場合は空の結果を返す（エラーではなくスキップ）
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({'combinations': []})
            }
        
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
        
        # 特徴量を抽出して予測
        combo_scores = []
        for combo in combinations[:max_combinations]:
            features = extract_combination_features(
                grid, rows, cols, combo, rehearsal_positions
            )
            features = add_pattern_id_features(features, best_pattern)
            
            # 罫線パターンID特徴量を追加
            if previous_winning and previous_previous_winning:
                features = add_keisen_pattern_features(
                    features, previous_winning, previous_previous_winning, target
                )
            
            feature_vector = features_to_vector(features)
            
            try:
                # 予測確率を取得
                proba = model_loader.predict_combination(
                    target, combo_type, feature_vector.reshape(1, -1)
                )[0]
                
                # スコア算出（確率 × 1000）
                score = proba * 1000
                combo_scores.append({
                    'combination': combo,
                    'score': float(score)
                })
            except ValueError as e:
                # モデル関連のエラーの場合はスキップ
                if "モデルが見つかりません" in str(e):
                    break
                raise
        
        # スコア順にソート（降順）
        combo_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'combinations': combo_scores
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

