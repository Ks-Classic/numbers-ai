#!/usr/bin/env python3
"""組み合わせ予測データファイルの内容を確認するスクリプト"""

import pickle
import numpy as np
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / 'data' / 'models'

print("=" * 80)
print("組み合わせ予測データファイルの確認")
print("=" * 80)

for target in ['n3', 'n4']:
    for combo_type in ['box', 'straight']:
        data_file = MODELS_DIR / f'{target}_{combo_type}_comb_data.pkl'
        
        print(f"\n{'='*80}")
        print(f"{target.upper()} {combo_type.upper()} 組み合わせ予測データ")
        print(f"{'='*80}")
        
        if not data_file.exists():
            print(f"❌ ファイルが存在しません: {data_file}")
            continue
        
        file_size = data_file.stat().st_size
        print(f"ファイルサイズ: {file_size:,} バイト ({file_size / 1024 / 1024:.2f} MB)")
        
        if file_size == 0:
            print(f"⚠️  ファイルが空です（0バイト）")
            continue
        
        try:
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
            
            # データ形状
            if 'X_train' in data:
                print(f"\n📊 データ形状:")
                print(f"  学習データ: {data['X_train'].shape}")
                print(f"  検証データ: {data['X_val'].shape}")
                print(f"  特徴量次元数: {data['X_train'].shape[1]}")
            
            # ラベル分布
            if 'y_train' in data and 'y_val' in data:
                y_train = data['y_train']
                y_val = data['y_val']
                
                train_pos = np.sum(y_train == 1)
                train_neg = np.sum(y_train == 0)
                val_pos = np.sum(y_val == 1)
                val_neg = np.sum(y_val == 0)
                
                print(f"\n📈 ラベル分布:")
                print(f"  学習データ:")
                print(f"    正例 (1): {train_pos:,} ({train_pos/len(y_train)*100:.2f}%)")
                print(f"    負例 (0): {train_neg:,} ({train_neg/len(y_train)*100:.2f}%)")
                print(f"  検証データ:")
                print(f"    正例 (1): {val_pos:,} ({val_pos/len(y_val)*100:.2f}%)")
                print(f"    負例 (0): {val_neg:,} ({val_neg/len(y_val)*100:.2f}%)")
            
            # メタデータの統計
            if 'metadata_train' in data:
                metadata_train = data['metadata_train']
                if len(metadata_train) > 0:
                    targets = [m.get('target', 'N/A') for m in metadata_train]
                    patterns = [m.get('pattern', 'N/A') for m in metadata_train]
                    rounds = [m.get('round_number', 0) for m in metadata_train]
                    
                    print(f"\n📝 メタデータ（学習データ）:")
                    print(f"  サンプル数: {len(metadata_train):,}")
                    print(f"  回号範囲: {min(rounds)} 〜 {max(rounds)}")
                    print(f"  target分布: {dict(Counter(targets))}")
                    print(f"  pattern分布: {dict(Counter(patterns))}")
                else:
                    print(f"\n⚠️  メタデータ（学習データ）が空です")
            
        except Exception as e:
            print(f"❌ ファイルの読み込みに失敗しました: {e}")
            import traceback
            traceback.print_exc()

print(f"\n{'='*80}")
print("確認完了")
print(f"{'='*80}\n")

