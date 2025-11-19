#!/usr/bin/env python3
"""チェックポイントファイルの進捗を確認するスクリプト"""
import pickle
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CHECKPOINT_FILE = PROJECT_ROOT / 'data' / 'models' / 'combination_checkpoint.pkl'

if CHECKPOINT_FILE.exists():
    with open(CHECKPOINT_FILE, 'rb') as f:
        data = pickle.load(f)
    
    processed_rounds = data.get('processed_rounds', set())
    comb_samples = data.get('comb_samples', [])
    last_round = data.get('last_round', 'N/A')
    timestamp = data.get('timestamp', 'N/A')
    
    print(f"処理済み回号数: {len(processed_rounds)}")
    print(f"サンプル数: {len(comb_samples)}")
    print(f"最終処理回号: {last_round}")
    print(f"タイムスタンプ: {timestamp}")
    
    if processed_rounds:
        sorted_rounds = sorted(processed_rounds)
        print(f"最小回号: {min(sorted_rounds)}")
        print(f"最大回号: {max(sorted_rounds)}")
else:
    print("チェックポイントファイルが存在しません")

