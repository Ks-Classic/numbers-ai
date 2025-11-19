#!/usr/bin/env python3
"""特徴量データファイルの内容を確認するスクリプト"""

import pickle
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / 'data' / 'models'

# データファイルを確認
for target in ['n3', 'n4']:
    data_file = MODELS_DIR / f'{target}_axis_data.pkl'
    
    if not data_file.exists():
        print(f"❌ {data_file} が見つかりません")
        continue
    
    print(f"\n=== {target.upper()} 軸数字予測データ ===")
    
    with open(data_file, 'rb') as f:
        data = pickle.load(f)
    
    # データ形状
    if 'X_train' in data:
        print(f"学習データ形状: {data['X_train'].shape}")
        print(f"検証データ形状: {data['X_val'].shape}")
        print(f"特徴量次元数: {data['X_train'].shape[1]}")
    
    # 特徴量キー
    feature_keys = data.get('feature_keys', [])
    if feature_keys:
        print(f"特徴量キー数: {len(feature_keys)}")
        
        # 新しい特徴量が含まれているか確認
        has_weekday = any('weekday' in key for key in feature_keys)
        has_reliability = any('winning_digits' in key or 'all_winning' in key for key in feature_keys)
        has_keisen = any('keisen_pattern' in key for key in feature_keys)
        
        print(f"  weekday特徴量: {'✅' if has_weekday else '❌'}")
        print(f"  予測表信頼性特徴量: {'✅' if has_reliability else '❌'}")
        print(f"  罫線パターンID特徴量: {'✅' if has_keisen else '❌'}")
        
        # 特徴量キーの一部を表示
        print(f"\n特徴量キー（最初の20個）:")
        for i, key in enumerate(feature_keys[:20]):
            print(f"  {i+1}. {key}")
        if len(feature_keys) > 20:
            print(f"  ... (残り{len(feature_keys) - 20}個)")
    else:
        print("⚠️  特徴量キーが保存されていません")

