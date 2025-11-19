#!/usr/bin/env python3
"""メタデータからn4のインデックス抽出を確認するスクリプト"""

import pickle
import numpy as np
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / 'data' / 'models'
BATCH_DIR = MODELS_DIR / 'combination_batches'

print("=" * 80)
print("メタデータからn4のインデックス抽出を確認")
print("=" * 80)

# 中間ファイルからメタデータを読み込む
vectorized_files = sorted(BATCH_DIR.glob('vectorized_*.pkl'))
if not vectorized_files:
    print("⚠️  中間ファイルが見つかりません")
    exit(1)

print(f"\n📊 中間ファイルからメタデータを読み込み中...")
metadata_comb = []
for intermediate_file in vectorized_files:
    with open(intermediate_file, 'rb') as f:
        data = pickle.load(f)
        metadata_comb.extend(data['metadata'])

print(f"総メタデータ数: {len(metadata_comb):,}")

# target分布を確認
target_counts = Counter([m.get('target', 'N/A') for m in metadata_comb])
print(f"\ntarget分布:")
for target, count in sorted(target_counts.items()):
    print(f"  {target}: {count:,}サンプル")

# 回号範囲を確認
rounds = [m.get('round_number', 0) for m in metadata_comb]
unique_rounds = sorted(set(rounds))
print(f"\n回号範囲: {min(rounds)} 〜 {max(rounds)} ({len(unique_rounds)}回号)")

# データ分割の設定を確認（config.pyから）
import sys
sys.path.append(str(PROJECT_ROOT / 'core'))
from config import TRAIN_VAL_SPLIT

train_rounds_comb = unique_rounds[:int(len(unique_rounds) * TRAIN_VAL_SPLIT)]
val_rounds_comb = unique_rounds[int(len(unique_rounds) * TRAIN_VAL_SPLIT):]

print(f"\nデータ分割設定:")
print(f"  TRAIN_VAL_SPLIT: {TRAIN_VAL_SPLIT}")
print(f"  学習データ回号数: {len(train_rounds_comb)} ({min(train_rounds_comb)} 〜 {max(train_rounds_comb)})")
print(f"  検証データ回号数: {len(val_rounds_comb)} ({min(val_rounds_comb)} 〜 {max(val_rounds_comb)})")

# n4のインデックスを抽出
for target in ['n3', 'n4']:
    for combo_type in ['box', 'straight']:
        target_combo_indices_train = [i for i, m in enumerate(metadata_comb) 
                                     if m['round_number'] in train_rounds_comb and m['target'] == target]
        target_combo_indices_val = [i for i, m in enumerate(metadata_comb) 
                                   if m['round_number'] in val_rounds_comb and m['target'] == target]
        
        print(f"\n{target} {combo_type}:")
        print(f"  学習データインデックス数: {len(target_combo_indices_train):,}")
        print(f"  検証データインデックス数: {len(target_combo_indices_val):,}")
        
        if len(target_combo_indices_train) > 0:
            # サンプルメタデータを表示
            sample_meta = metadata_comb[target_combo_indices_train[0]]
            print(f"  サンプルメタデータ: {sample_meta}")
        else:
            print(f"  ⚠️  学習データが存在しません")
            # n4のメタデータが存在するか確認
            n4_metadata = [m for m in metadata_comb if m.get('target') == target]
            print(f"  n4のメタデータ総数: {len(n4_metadata):,}")
            if len(n4_metadata) > 0:
                n4_rounds = set([m.get('round_number', 0) for m in n4_metadata])
                print(f"  n4の回号範囲: {min(n4_rounds)} 〜 {max(n4_rounds)}")
                print(f"  train_rounds_combとの重複: {len(n4_rounds & set(train_rounds_comb))}回号")

print(f"\n{'='*80}")
print("確認完了")
print(f"{'='*80}\n")

