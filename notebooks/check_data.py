#!/usr/bin/env python3
"""データファイルの確認スクリプト"""
import pickle
from pathlib import Path

data_file = Path('../data/models/n3_axis_data.pkl')
if data_file.exists():
    with open(data_file, 'rb') as f:
        data = pickle.load(f)
    
    print('データ形状:')
    print(f"  X_train: {data['X_train'].shape}")
    print(f"  X_val: {data['X_val'].shape}")
    print('\n回号範囲:')
    train_rounds = [m['round_number'] for m in data['metadata_train']]
    val_rounds = [m['round_number'] for m in data['metadata_val']]
    print(f"  学習データ: {min(train_rounds)} 〜 {max(train_rounds)}")
    print(f"  検証データ: {min(val_rounds)} 〜 {max(val_rounds)}")
    print('\nサンプル数:')
    print(f"  学習データ: {len(data['metadata_train'])} サンプル")
    print(f"  検証データ: {len(data['metadata_val'])} サンプル")
    print('\n特徴量キー数:', len(data['feature_keys']))
else:
    print(f"ファイルが見つかりません: {data_file}")
