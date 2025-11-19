#!/usr/bin/env python3
"""N4データの生成状況を確認するスクリプト"""

import pickle
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / 'data' / 'models'
BATCH_DIR = MODELS_DIR / 'combination_batches'

print("=" * 80)
print("N4データの生成状況確認")
print("=" * 80)

# チェックポイントファイルを確認
checkpoint_file = MODELS_DIR / 'combination_checkpoint.pkl'
if checkpoint_file.exists():
    print(f"\n📂 チェックポイントファイルを確認中...")
    try:
        with open(checkpoint_file, 'rb') as f:
            checkpoint_data = pickle.load(f)
        processed_rounds = checkpoint_data.get('processed_rounds', set())
        batch_files = checkpoint_data.get('batch_files', [])
        print(f"  処理済み回号数: {len(processed_rounds)}")
        print(f"  バッチファイル数: {len(batch_files)}")
    except Exception as e:
        print(f"  ⚠️  チェックポイントの読み込みに失敗: {e}")

# バッチファイルからtarget分布を確認
print(f"\n📦 バッチファイル内のtarget分布を確認中...")
batch_files = sorted(BATCH_DIR.glob('batch_*.pkl'))
if batch_files:
    # 最初の3ファイルを確認
    for batch_file in batch_files[:3]:
        try:
            with open(batch_file, 'rb') as f:
                samples = pickle.load(f)
            targets = [s.get('target', 'N/A') for s in samples]
            target_counts = Counter(targets)
            print(f"  {batch_file.name}: {dict(target_counts)} (総サンプル数: {len(samples):,})")
        except Exception as e:
            print(f"  {batch_file.name}: エラー - {e}")
    
    # 全バッチファイルからtarget分布を集計
    all_targets = []
    for batch_file in batch_files:
        try:
            with open(batch_file, 'rb') as f:
                samples = pickle.load(f)
            all_targets.extend([s.get('target', 'N/A') for s in samples])
        except:
            pass
    
    if all_targets:
        total_counts = Counter(all_targets)
        print(f"\n  全バッチファイル合計:")
        for target, count in sorted(total_counts.items()):
            print(f"    {target}: {count:,}サンプル")
else:
    print("  ⚠️  バッチファイルが見つかりません")

# 中間ファイル（vectorized）を確認
print(f"\n📊 中間ファイル（vectorized）を確認中...")
vectorized_files = sorted(BATCH_DIR.glob('vectorized_*.pkl'))
if vectorized_files:
    print(f"  中間ファイル数: {len(vectorized_files)}")
    # 最初のファイルを確認
    try:
        with open(vectorized_files[0], 'rb') as f:
            data = pickle.load(f)
        print(f"  {vectorized_files[0].name}:")
        print(f"    X形状: {data['X'].shape}")
        print(f"    metadata数: {len(data['metadata'])}")
        if len(data['metadata']) > 0:
            targets = [m.get('target', 'N/A') for m in data['metadata']]
            target_counts = Counter(targets)
            print(f"    target分布: {dict(target_counts)}")
    except Exception as e:
        print(f"  ⚠️  中間ファイルの読み込みに失敗: {e}")
else:
    print("  ⚠️  中間ファイルが見つかりません")

print(f"\n{'='*80}")
print("確認完了")
print(f"{'='*80}\n")

