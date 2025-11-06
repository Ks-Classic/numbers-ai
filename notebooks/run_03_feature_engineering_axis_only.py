#!/usr/bin/env python3
"""
特徴量エンジニアリングと学習データ生成スクリプト（完全版）

軸数字予測と組み合わせ予測の両方の学習データを生成し、保存します。
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
from itertools import product
import time
from tqdm import tqdm
import pickle
from sklearn.model_selection import train_test_split
warnings.filterwarnings('ignore')

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# 設定ファイルをインポート
import sys
sys.path.append(str(PROJECT_ROOT / 'notebooks'))
from config import TRAIN_SIZE, TRAIN_DATA_CSV, MAX_COMBINATIONS_PER_DIGIT

# モジュールをインポート
from chart_generator import (
    load_keisen_master,
    generate_chart,
    Pattern,
    Target
)
from feature_extractor import (
    extract_digit_features,
    extract_combination_features,
    add_pattern_id_features,
    features_to_vector,
    get_rehearsal_positions
)

print(f"プロジェクトルート: {PROJECT_ROOT}")
print(f"データディレクトリ: {DATA_DIR}")
print(f"\n学習設定:")
print(f"  学習範囲: {TRAIN_SIZE}回分")
print(f"  データファイル: {TRAIN_DATA_CSV}")

# データの読み込み
train_csv_path = DATA_DIR / TRAIN_DATA_CSV

if train_csv_path.exists():
    train_df = pd.read_csv(train_csv_path)
    print(f"\n学習用データセット: {len(train_df)}回分")
else:
    print(f"エラー: {train_csv_path} が見つかりません")
    print("先に01_data_preparationを実行してください")
    sys.exit(1)

# 当選番号を文字列型に変換
train_df['n3_winning'] = train_df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
train_df['n4_winning'] = train_df['n4_winning'].astype(str).str.replace('.0', '', regex=False)

# 先頭0を補完
train_df['n3_winning'] = train_df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' else x)
train_df['n4_winning'] = train_df['n4_winning'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' else x)

# リハーサル数字を文字列型に変換し、先頭0を補完
train_df['n3_rehearsal'] = train_df['n3_rehearsal'].astype(str).str.replace('.0', '', regex=False)
train_df['n4_rehearsal'] = train_df['n4_rehearsal'].astype(str).str.replace('.0', '', regex=False)
train_df['n3_rehearsal'] = train_df['n3_rehearsal'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' and str(x) != 'nan' else None)
train_df['n4_rehearsal'] = train_df['n4_rehearsal'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' and str(x) != 'nan' else None)

print(f"回号範囲: {train_df['round_number'].min()} 〜 {train_df['round_number'].max()}")

# 罫線マスターデータの読み込み
keisen_master = load_keisen_master(DATA_DIR)
print("\n罫線マスターデータの読み込み完了")

# パターンと対象の定義
patterns: List[Pattern] = ['A1', 'A2', 'B1', 'B2']
targets: List[Target] = ['n3', 'n4']

print(f"\n{'='*60}")
print("軸数字予測モデルの学習データを生成中...")
print(f"{'='*60}")

# 軸数字予測モデルの学習データ生成
axis_samples = []
total_iterations = len(train_df) * len(targets) * len(patterns)
start_time = time.time()

with tqdm(total=total_iterations, desc="軸数字予測データ生成") as pbar:
    for _, row in train_df.iterrows():
        round_number = row['round_number']
        
        # N3/N4のリハーサル数字の共通部分を計算（一度だけ計算）
        n3_rehearsal = row.get('n3_rehearsal')
        n4_rehearsal = row.get('n4_rehearsal')
        
        # リハーサル数字を正規化
        if pd.notna(n3_rehearsal) and n3_rehearsal != 'NULL' and str(n3_rehearsal) != 'nan':
            n3_rehearsal_str = str(n3_rehearsal).replace('.0', '').zfill(3)
        else:
            n3_rehearsal_str = None
        
        if pd.notna(n4_rehearsal) and n4_rehearsal != 'NULL' and str(n4_rehearsal) != 'nan':
            n4_rehearsal_str = str(n4_rehearsal).replace('.0', '').zfill(4)
        else:
            n4_rehearsal_str = None
        
        # N3/N4リハーサル数字の共通部分を計算
        from feature_extractor import calculate_n3_n4_rehearsal_common_digits
        n3_n4_common_digits = calculate_n3_n4_rehearsal_common_digits(
            n3_rehearsal_str, n4_rehearsal_str
        ) if (n3_rehearsal_str and n4_rehearsal_str) else None
        
        for target in targets:
            # リハーサル数字を取得（CSVファイルのn3_rehearsal/n4_rehearsalカラムから直接取得）
            rehearsal_digits = row[f'{target}_rehearsal']
            if pd.isna(rehearsal_digits) or rehearsal_digits == 'NULL' or str(rehearsal_digits) == 'nan':
                rehearsal_digits = None
            else:
                rehearsal_digits = str(rehearsal_digits).replace('.0', '')
                # 先頭0が失われている場合は補完
                if target == 'n3' and len(rehearsal_digits) < 3:
                    rehearsal_digits = rehearsal_digits.zfill(3)
                elif target == 'n4' and len(rehearsal_digits) < 4:
                    rehearsal_digits = rehearsal_digits.zfill(4)
            
            for pattern in patterns:
                try:
                    # 予測表を生成
                    grid, rows, cols = generate_chart(
                        train_df, keisen_master, round_number, pattern, target
                    )
                    
                    # リハーサル位置を取得
                    if rehearsal_digits:
                        rehearsal_positions = get_rehearsal_positions(
                            grid, rows, cols, rehearsal_digits
                        )
                    else:
                        rehearsal_positions = None
                    
                    # 各数字（0-9）のサンプルを生成
                    for digit in range(10):
                        # 特徴量を抽出
                        features = extract_digit_features(
                            grid, rows, cols, digit, rehearsal_positions, rehearsal_digits,
                            n3_n4_common_rehearsal_digits=n3_n4_common_digits
                        )
                        
                        # パターンIDを追加
                        features = add_pattern_id_features(features, pattern)
                        
                        # ラベルを生成（当選番号に含まれたか）
                        winning = str(row[f'{target}_winning']).replace('.0', '')
                        label = 1 if str(digit) in winning else 0
                        
                        axis_samples.append({
                            'round_number': round_number,
                            'target': target,
                            'pattern': pattern,
                            'digit': digit,
                            'features': features,
                            'label': label
                        })
                    
                except Exception as e:
                    # エラーは無視して続行（欠番データなどの場合）
                    pass
                
                pbar.update(1)

elapsed_time = time.time() - start_time
print(f"\n生成されたサンプル数: {len(axis_samples)}")
print(f"処理時間: {elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分)")

# ラベルの分布を確認
labels = [s['label'] for s in axis_samples]
print(f"\nラベルの分布:")
print(f"  0（含まれない）: {labels.count(0)} ({labels.count(0)/len(labels)*100:.1f}%)")
print(f"  1（含まれる）: {labels.count(1)} ({labels.count(1)/len(labels)*100:.1f}%)")

# 軸数字予測データのベクトル化
print(f"\n{'='*60}")
print("軸数字予測データをベクトル化中...")
print(f"{'='*60}")

# 選択された特徴量を読み込む（重要度に基づいて選択された特徴量のみを使用）
selected_features_path = PROJECT_ROOT / 'docs' / 'report' / 'selected_features.json'
if selected_features_path.exists():
    import json
    with open(selected_features_path, 'r', encoding='utf-8') as f:
        selected_features_data = json.load(f)
        selected_feature_keys = selected_features_data.get('selected_features', [])
    print(f"選択された特徴量数: {len(selected_feature_keys)}")
    print(f"削除された特徴量数: {selected_features_data.get('removed_count', 0)}")
else:
    # 選択された特徴量ファイルがない場合は、すべての特徴量を使用
    selected_feature_keys = sorted(axis_samples[0]['features'].keys())
    print(f"選択された特徴量ファイルが見つかりません。すべての特徴量を使用します。")

# 特徴量キーを選択されたものに限定
feature_keys = [key for key in sorted(axis_samples[0]['features'].keys()) if key in selected_feature_keys]
print(f"特徴量の次元数: {len(feature_keys)}")

X_axis = []
y_axis = []
metadata_axis = []

for sample in tqdm(axis_samples, desc="ベクトル化"):
    # 選択された特徴量のみを使用してベクトル化
    filtered_features = {k: v for k, v in sample['features'].items() if k in feature_keys}
    feature_vector = features_to_vector(filtered_features, feature_keys=feature_keys)
    X_axis.append(feature_vector)
    y_axis.append(sample['label'])
    metadata_axis.append({
        'round_number': sample['round_number'],
        'target': sample['target'],
        'pattern': sample['pattern'],
        'digit': sample['digit']
    })

X_axis = np.array(X_axis)
y_axis = np.array(y_axis)

print(f"\n特徴量行列の形状: {X_axis.shape}")
print(f"ラベルベクトルの形状: {y_axis.shape}")

# データセットの分割と保存
print(f"\n{'='*60}")
print("データセットの分割と保存...")
print(f"{'='*60}")

unique_rounds = sorted(set([m['round_number'] for m in metadata_axis]))
train_rounds = unique_rounds[:int(len(unique_rounds) * 0.8)]
val_rounds = unique_rounds[int(len(unique_rounds) * 0.8):]

train_indices_axis = [i for i, m in enumerate(metadata_axis) if m['round_number'] in train_rounds]
val_indices_axis = [i for i, m in enumerate(metadata_axis) if m['round_number'] in val_rounds]

X_axis_train = X_axis[train_indices_axis]
X_axis_val = X_axis[val_indices_axis]
y_axis_train = y_axis[train_indices_axis]
y_axis_val = y_axis[val_indices_axis]

print(f"軸数字予測データ:")
print(f"  学習データ: {X_axis_train.shape[0]}サンプル")
print(f"  検証データ: {X_axis_val.shape[0]}サンプル")

# 軸数字予測データの保存（N3/N4で分ける）
for target in ['n3', 'n4']:
    target_indices_train = [i for i, m in enumerate(metadata_axis) 
                           if m['round_number'] in train_rounds and m['target'] == target]
    target_indices_val = [i for i, m in enumerate(metadata_axis) 
                         if m['round_number'] in val_rounds and m['target'] == target]
    
    if len(target_indices_train) > 0:
        data_file = MODELS_DIR / f'{target}_axis_data.pkl'
        with open(data_file, 'wb') as f:
            pickle.dump({
                'X_train': X_axis[target_indices_train],
                'X_val': X_axis[target_indices_val],
                'y_train': y_axis[target_indices_train],
                'y_val': y_axis[target_indices_val],
                'feature_keys': feature_keys,
                'metadata_train': [metadata_axis[i] for i in target_indices_train],
                'metadata_val': [metadata_axis[i] for i in target_indices_val]
            }, f)
        print(f"保存完了: {data_file}")

print(f"\n✅ 軸数字予測データの生成と保存が完了しました")
print(f"\n⚠️  組み合わせ予測データの生成は時間がかかります。")
print(f"   続行する場合は、Jupyter Notebook (03_feature_engineering.ipynb) で実行することを推奨します。")

