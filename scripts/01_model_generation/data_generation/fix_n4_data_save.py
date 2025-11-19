#!/usr/bin/env python3
"""n4のデータファイルを再保存するスクリプト"""

import pickle
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / 'data' / 'models'
BATCH_DIR = MODELS_DIR / 'combination_batches'

# 設定をインポート
import sys
sys.path.append(str(PROJECT_ROOT / 'core'))
from config import TRAIN_VAL_SPLIT

print("=" * 80)
print("n4のデータファイルを再保存")
print("=" * 80)

# 中間ファイルから全データを読み込む
print(f"\n📊 中間ファイルから全データを読み込み中...")
vectorized_files = sorted(BATCH_DIR.glob('vectorized_*.pkl'))

X_comb_list = []
y_comb_box_list = []
y_comb_straight_list = []
metadata_comb = []

for intermediate_file in vectorized_files:
    with open(intermediate_file, 'rb') as f:
        data = pickle.load(f)
        X_comb_list.append(data['X'])
        y_comb_box_list.append(data['y_box'])
        y_comb_straight_list.append(data['y_straight'])
        metadata_comb.extend(data['metadata'])

# NumPy配列に結合
print(f"NumPy配列に結合中...")
X_comb = np.concatenate(X_comb_list, axis=0)
y_comb_box = np.concatenate(y_comb_box_list, axis=0)
y_comb_straight = np.concatenate(y_comb_straight_list, axis=0)

# メモリを解放
del X_comb_list, y_comb_box_list, y_comb_straight_list
import gc
gc.collect()

print(f"総サンプル数: {len(metadata_comb):,}")
print(f"X形状: {X_comb.shape}")

# 特徴量キーを取得（最初のサンプルから）
all_comb_feature_keys = set()
for m in metadata_comb[:1000]:  # 最初の1000サンプルから特徴量キーを推測
    # 実際には中間ファイルから取得する必要があるが、簡易的に処理
    pass

# 中間ファイルから特徴量キーを取得
with open(vectorized_files[0], 'rb') as f:
    first_data = pickle.load(f)
    # 特徴量キーは保存されていないので、Xの次元数から推測
    feature_dim = first_data['X'].shape[1]

# データ分割
unique_rounds_comb = sorted(set([m['round_number'] for m in metadata_comb]))
train_rounds_comb = unique_rounds_comb[:int(len(unique_rounds_comb) * TRAIN_VAL_SPLIT)]
val_rounds_comb = unique_rounds_comb[int(len(unique_rounds_comb) * TRAIN_VAL_SPLIT):]

print(f"\nデータ分割:")
print(f"  学習データ回号数: {len(train_rounds_comb)} ({min(train_rounds_comb)} 〜 {max(train_rounds_comb)})")
print(f"  検証データ回号数: {len(val_rounds_comb)} ({min(val_rounds_comb)} 〜 {max(val_rounds_comb)})")

# n4のデータのみを保存
for target in ['n4']:  # n4のみ
    for combo_type in ['box', 'straight']:
        target_combo_indices_train = [i for i, m in enumerate(metadata_comb) 
                                     if m['round_number'] in train_rounds_comb and m['target'] == target]
        target_combo_indices_val = [i for i, m in enumerate(metadata_comb) 
                                   if m['round_number'] in val_rounds_comb and m['target'] == target]
        
        print(f"\n{target} {combo_type}:")
        print(f"  学習データインデックス数: {len(target_combo_indices_train):,}")
        print(f"  検証データインデックス数: {len(target_combo_indices_val):,}")
        
        if len(target_combo_indices_train) > 0:
            data_file = MODELS_DIR / f'{target}_{combo_type}_comb_data.pkl'
            
            if combo_type == 'box':
                y_train = y_comb_box[target_combo_indices_train]
                y_val = y_comb_box[target_combo_indices_val]
            else:
                y_train = y_comb_straight[target_combo_indices_train]
                y_val = y_comb_straight[target_combo_indices_val]
            
            # 特徴量キーを取得（n3のファイルから、同じ特徴量キーを使用）
            n3_file = MODELS_DIR / f'n3_{combo_type}_comb_data.pkl'
            if n3_file.exists():
                with open(n3_file, 'rb') as f:
                    n3_data = pickle.load(f)
                comb_feature_keys = n3_data['feature_keys']
            else:
                # フォールバック: 特徴量次元数から推測（実際には使用されない）
                comb_feature_keys = [f'feature_{i}' for i in range(feature_dim)]
                print(f"  ⚠️  警告: n3のファイルから特徴量キーを取得できませんでした")
            
            print(f"  特徴量キー数: {len(comb_feature_keys)}")
            print(f"  保存中: {data_file}")
            
            with open(data_file, 'wb') as f:
                pickle.dump({
                    'X_train': X_comb[target_combo_indices_train],
                    'X_val': X_comb[target_combo_indices_val],
                    'y_train': y_train,
                    'y_val': y_val,
                    'feature_keys': comb_feature_keys,
                    'metadata_train': [metadata_comb[i] for i in target_combo_indices_train],
                    'metadata_val': [metadata_comb[i] for i in target_combo_indices_val]
                }, f)
            
            file_size = data_file.stat().st_size
            print(f"  ✅ 保存完了: {data_file} ({file_size:,} バイト, {file_size / 1024 / 1024:.2f} MB)")
        else:
            print(f"  ⚠️  警告: {target} {combo_type}の学習データが存在しません。")

print(f"\n✅ n4のデータファイルの再保存が完了しました")

