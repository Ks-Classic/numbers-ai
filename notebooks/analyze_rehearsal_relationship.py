#!/usr/bin/env python3
"""
リハーサル数字と当選番号の関係性分析スクリプト
"""
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
MODELS_DIR = PROJECT_ROOT / 'data' / 'models'
REPORT_DIR = PROJECT_ROOT / 'docs' / 'report'

print("学習データを読み込み中...")

results = {}

for target in ['n3', 'n4']:
    data_file = MODELS_DIR / f'{target}_axis_data.pkl'
    if not data_file.exists():
        print(f"警告: {data_file} が見つかりません")
        continue
    
    with open(data_file, 'rb') as f:
        data = pickle.load(f)
    
    X_train = data['X_train']
    y_train = data['y_train']
    X_val = data['X_val']
    y_val = data['y_val']
    feature_keys = data['feature_keys']
    
    # 全データを結合
    X_all = np.vstack([X_train, X_val])
    y_all = np.hstack([y_train, y_val])
    
    # 特徴量キーから関係性特徴量のインデックスを取得
    rehearsal_distance_idx = feature_keys.index('rehearsal_distance')
    overlap_count_idx = feature_keys.index('overlap_count')
    inverse_ratio_idx = feature_keys.index('inverse_ratio')
    
    # 関係性特徴量を抽出
    rehearsal_distances = X_all[:, rehearsal_distance_idx]
    overlap_counts = X_all[:, overlap_count_idx]
    inverse_ratios = X_all[:, inverse_ratio_idx]
    
    # 当選（label=1）と非当選（label=0）に分ける
    # リハーサル数字が存在する場合のみ（999.0でない場合）
    valid_mask = rehearsal_distances != 999.0
    
    if valid_mask.sum() == 0:
        print(f"警告: {target}のデータでリハーサル数字が存在するサンプルがありません")
        continue
    
    rehearsal_distances_valid = rehearsal_distances[valid_mask]
    overlap_counts_valid = overlap_counts[valid_mask]
    inverse_ratios_valid = inverse_ratios[valid_mask]
    y_valid = y_all[valid_mask]
    
    # 統計量を計算
    won_mask = y_valid == 1
    lost_mask = y_valid == 0
    
    stats = {
        'target': target,
        'total_samples': int(len(y_valid)),
        'won_samples': int(won_mask.sum()),
        'lost_samples': int(lost_mask.sum()),
        'rehearsal_distance': {
            'all_mean': float(np.mean(rehearsal_distances_valid)),
            'all_std': float(np.std(rehearsal_distances_valid)),
            'all_median': float(np.median(rehearsal_distances_valid)),
            'won_mean': float(np.mean(rehearsal_distances_valid[won_mask])) if won_mask.sum() > 0 else None,
            'won_std': float(np.std(rehearsal_distances_valid[won_mask])) if won_mask.sum() > 0 else None,
            'won_median': float(np.median(rehearsal_distances_valid[won_mask])) if won_mask.sum() > 0 else None,
            'lost_mean': float(np.mean(rehearsal_distances_valid[lost_mask])) if lost_mask.sum() > 0 else None,
            'lost_std': float(np.std(rehearsal_distances_valid[lost_mask])) if lost_mask.sum() > 0 else None,
            'lost_median': float(np.median(rehearsal_distances_valid[lost_mask])) if lost_mask.sum() > 0 else None,
        },
        'overlap_count': {
            'all_mean': float(np.mean(overlap_counts_valid)),
            'all_std': float(np.std(overlap_counts_valid)),
            'all_median': float(np.median(overlap_counts_valid)),
            'won_mean': float(np.mean(overlap_counts_valid[won_mask])) if won_mask.sum() > 0 else None,
            'won_std': float(np.std(overlap_counts_valid[won_mask])) if won_mask.sum() > 0 else None,
            'won_median': float(np.median(overlap_counts_valid[won_mask])) if won_mask.sum() > 0 else None,
            'lost_mean': float(np.mean(overlap_counts_valid[lost_mask])) if lost_mask.sum() > 0 else None,
            'lost_std': float(np.std(overlap_counts_valid[lost_mask])) if lost_mask.sum() > 0 else None,
            'lost_median': float(np.median(overlap_counts_valid[lost_mask])) if lost_mask.sum() > 0 else None,
        },
        'inverse_ratio': {
            'all_mean': float(np.mean(inverse_ratios_valid)),
            'all_std': float(np.std(inverse_ratios_valid)),
            'all_median': float(np.median(inverse_ratios_valid)),
            'won_mean': float(np.mean(inverse_ratios_valid[won_mask])) if won_mask.sum() > 0 else None,
            'won_std': float(np.std(inverse_ratios_valid[won_mask])) if won_mask.sum() > 0 else None,
            'won_median': float(np.median(inverse_ratios_valid[won_mask])) if won_mask.sum() > 0 else None,
            'lost_mean': float(np.mean(inverse_ratios_valid[lost_mask])) if lost_mask.sum() > 0 else None,
            'lost_std': float(np.std(inverse_ratios_valid[lost_mask])) if lost_mask.sum() > 0 else None,
            'lost_median': float(np.median(inverse_ratios_valid[lost_mask])) if lost_mask.sum() > 0 else None,
        }
    }
    
    results[target] = stats
    
    print(f"\n{target.upper()}の分析結果:")
    print(f"  有効サンプル数: {stats['total_samples']}")
    print(f"  当選サンプル数: {stats['won_samples']}")
    print(f"  非当選サンプル数: {stats['lost_samples']}")

# 結果を保存
import json
output_file = PROJECT_ROOT / 'docs' / 'report' / 'rehearsal_analysis_stats.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n統計情報を保存しました: {output_file}")
print("分析完了")

