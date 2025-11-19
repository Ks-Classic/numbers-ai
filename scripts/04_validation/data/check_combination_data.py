#!/usr/bin/env python3
"""
組み合わせ予測データファイルの確認スクリプト

N3とN4の組み合わせ予測データファイル（*_box_comb_data.pkl, *_straight_comb_data.pkl）の
内容を確認し、データサイズ、サンプル数、ラベル分布、パターン分布などを表示します。
N3とN4の比較も行います。
"""

import pickle
import numpy as np
from pathlib import Path
from collections import Counter
import sys

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / 'data' / 'models'

def check_combination_data_file(target: str, combo_type: str) -> dict:
    """組み合わせ予測データファイルを確認
    
    Args:
        target: 'n3' または 'n4'
        combo_type: 'box' または 'straight'
    
    Returns:
        確認結果の辞書
    """
    file = MODELS_DIR / f'{target}_{combo_type}_comb_data.pkl'
    
    if not file.exists():
        return {
            'exists': False,
            'file': file
        }
    
    try:
        with open(file, 'rb') as f:
            data = pickle.load(f)
        
        X_train = data['X_train']
        X_val = data['X_val']
        y_train = data['y_train']
        y_val = data['y_val']
        
        total_samples = X_train.shape[0] + X_val.shape[0]
        
        # ラベル分布
        train_pos = np.sum(y_train == 1)
        train_neg = np.sum(y_train == 0)
        val_pos = np.sum(y_val == 1)
        val_neg = np.sum(y_val == 0)
        
        # 回号範囲とパターン分布
        train_rounds = []
        val_rounds = []
        train_patterns = []
        val_patterns = []
        
        if 'metadata_train' in data and len(data['metadata_train']) > 0:
            train_rounds = [m['round_number'] for m in data['metadata_train']]
            train_patterns = [m['pattern'] for m in data['metadata_train']]
        
        if 'metadata_val' in data and len(data['metadata_val']) > 0:
            val_rounds = [m['round_number'] for m in data['metadata_val']]
            val_patterns = [m['pattern'] for m in data['metadata_val']]
        
        # ファイルサイズ
        file_size_mb = file.stat().st_size / (1024 * 1024)
        
        return {
            'exists': True,
            'file': file,
            'file_size_mb': file_size_mb,
            'X_train_shape': X_train.shape,
            'X_val_shape': X_val.shape,
            'total_samples': total_samples,
            'feature_dim': len(data.get('feature_keys', [])),
            'train_samples': X_train.shape[0],
            'val_samples': X_val.shape[0],
            'train_pos': train_pos,
            'train_neg': train_neg,
            'train_pos_ratio': train_pos / len(y_train) * 100 if len(y_train) > 0 else 0,
            'val_pos': val_pos,
            'val_neg': val_neg,
            'val_pos_ratio': val_pos / len(y_val) * 100 if len(y_val) > 0 else 0,
            'train_rounds': train_rounds,
            'val_rounds': val_rounds,
            'train_patterns': train_patterns,
            'val_patterns': val_patterns,
            'unique_rounds': len(set(train_rounds + val_rounds)) if train_rounds or val_rounds else 0,
            'pattern_distribution': dict(Counter(train_patterns + val_patterns)) if train_patterns or val_patterns else {}
        }
    except Exception as e:
        return {
            'exists': True,
            'file': file,
            'error': str(e)
        }


def print_data_info(target: str, combo_type: str, info: dict):
    """データ情報を表示"""
    print(f"\n{'='*60}")
    print(f"{target.upper()} {combo_type.upper()} 組み合わせ予測データ")
    print(f"{'='*60}")
    
    if not info.get('exists', False):
        print(f"❌ ファイルが見つかりません: {info['file']}")
        return
    
    if 'error' in info:
        print(f"❌ エラー: {info['error']}")
        return
    
    print(f"📁 ファイル: {info['file']}")
    print(f"📦 ファイルサイズ: {info['file_size_mb']:.2f} MB")
    print(f"\n📊 データ形状:")
    print(f"  X_train: {info['X_train_shape']}")
    print(f"  X_val: {info['X_val_shape']}")
    print(f"  特徴量次元数: {info['feature_dim']}")
    
    print(f"\n📈 サンプル数:")
    print(f"  学習データ: {info['train_samples']:,} サンプル")
    print(f"  検証データ: {info['val_samples']:,} サンプル")
    print(f"  合計: {info['total_samples']:,} サンプル")
    
    if info['unique_rounds'] > 0:
        print(f"  処理回号数: {info['unique_rounds']} 回号")
        print(f"  1回号あたり平均: {info['total_samples'] / info['unique_rounds']:.1f} サンプル")
    
    print(f"\n🏷️  ラベル分布（学習データ）:")
    print(f"  0（当選なし）: {info['train_neg']:,} ({100 - info['train_pos_ratio']:.2f}%)")
    print(f"  1（当選あり）: {info['train_pos']:,} ({info['train_pos_ratio']:.2f}%)")
    
    print(f"\n🏷️  ラベル分布（検証データ）:")
    print(f"  0（当選なし）: {info['val_neg']:,} ({100 - info['val_pos_ratio']:.2f}%)")
    print(f"  1（当選あり）: {info['val_pos']:,} ({info['val_pos_ratio']:.2f}%)")
    
    if info['train_rounds']:
        print(f"\n📅 回号範囲:")
        print(f"  学習データ: {min(info['train_rounds'])} 〜 {max(info['train_rounds'])}")
        if info['val_rounds']:
            print(f"  検証データ: {min(info['val_rounds'])} 〜 {max(info['val_rounds'])}")
    
    if info['pattern_distribution']:
        print(f"\n🔀 パターン分布:")
        for pattern, count in sorted(info['pattern_distribution'].items()):
            ratio = count / info['total_samples'] * 100
            print(f"  {pattern}: {count:,} サンプル ({ratio:.1f}%)")


def compare_n3_n4():
    """N3とN4のデータを比較"""
    print(f"\n{'='*60}")
    print("N3とN4の比較")
    print(f"{'='*60}")
    
    n3_box = check_combination_data_file('n3', 'box')
    n3_straight = check_combination_data_file('n3', 'straight')
    n4_box = check_combination_data_file('n4', 'box')
    n4_straight = check_combination_data_file('n4', 'straight')
    
    if not all([n3_box.get('exists'), n3_straight.get('exists'), 
                n4_box.get('exists'), n4_straight.get('exists')]):
        print("⚠️  一部のファイルが見つかりません。比較をスキップします。")
        return
    
    if any('error' in info for info in [n3_box, n3_straight, n4_box, n4_straight]):
        print("⚠️  一部のファイルでエラーが発生しました。比較をスキップします。")
        return
    
    # サンプル数の比較
    n3_total = n3_box['total_samples'] + n3_straight['total_samples']
    n4_total = n4_box['total_samples'] + n4_straight['total_samples']
    
    print(f"\n📊 総サンプル数の比較:")
    print(f"  N3（box + straight）: {n3_total:,} サンプル")
    print(f"  N4（box + straight）: {n4_total:,} サンプル")
    print(f"  比率: {n4_total / n3_total:.2f}倍" if n3_total > 0 else "  比率: 計算不可")
    
    # ファイルサイズの比較
    n3_size = n3_box['file_size_mb'] + n3_straight['file_size_mb']
    n4_size = n4_box['file_size_mb'] + n4_straight['file_size_mb']
    
    print(f"\n💾 ファイルサイズの比較:")
    print(f"  N3（box + straight）: {n3_size:.2f} MB")
    print(f"  N4（box + straight）: {n4_size:.2f} MB")
    print(f"  比率: {n4_size / n3_size:.2f}倍" if n3_size > 0 else "  比率: 計算不可")
    
    # 1回号あたりの平均サンプル数
    n3_rounds = n3_box['unique_rounds']
    n4_rounds = n4_box['unique_rounds']
    
    if n3_rounds > 0 and n4_rounds > 0:
        n3_avg = n3_total / n3_rounds
        n4_avg = n4_total / n4_rounds
        
        print(f"\n📈 1回号あたりの平均サンプル数:")
        print(f"  N3: {n3_avg:.1f} サンプル/回号")
        print(f"  N4: {n4_avg:.1f} サンプル/回号")
        print(f"  比率: {n4_avg / n3_avg:.2f}倍" if n3_avg > 0 else "  比率: 計算不可")
    
    # ラベル分布の比較
    print(f"\n🏷️  ラベル分布の比較（学習データ）:")
    n3_pos_ratio = (n3_box['train_pos'] + n3_straight['train_pos']) / (n3_box['train_samples'] + n3_straight['train_samples']) * 100
    n4_pos_ratio = (n4_box['train_pos'] + n4_straight['train_pos']) / (n4_box['train_samples'] + n4_straight['train_samples']) * 100
    
    print(f"  N3正例率: {n3_pos_ratio:.2f}%")
    print(f"  N4正例率: {n4_pos_ratio:.2f}%")
    
    # 期待値との比較
    print(f"\n✅ 期待値との比較:")
    print(f"  理論値（1回号 × 2パターン × 200個）: 400個/回号")
    if n3_rounds > 0:
        print(f"  N3実際値: {n3_avg:.1f}個/回号")
        print(f"  N3差異: {abs(n3_avg - 400) / 400 * 100:.1f}%")
    if n4_rounds > 0:
        print(f"  N4実際値: {n4_avg:.1f}個/回号")
        print(f"  N4差異: {abs(n4_avg - 400) / 400 * 100:.1f}%")
    
    # 警告
    if n4_total / n3_total > 10:
        print(f"\n⚠️  警告: N4のサンプル数がN3の10倍以上です。")
        print(f"   N4の組み合わせ生成ロジックに問題がある可能性があります。")
    elif n4_total / n3_total < 0.5:
        print(f"\n⚠️  警告: N4のサンプル数がN3の半分以下です。")
        print(f"   N4のデータ生成に問題がある可能性があります。")
    else:
        print(f"\n✅ N3とN4のサンプル数の比率は正常範囲内です。")


def main():
    """メイン処理"""
    print("="*60)
    print("組み合わせ予測データファイルの確認")
    print("="*60)
    print(f"モデルディレクトリ: {MODELS_DIR}")
    
    if not MODELS_DIR.exists():
        print(f"❌ エラー: モデルディレクトリが見つかりません: {MODELS_DIR}")
        sys.exit(1)
    
    # 各データファイルを確認
    for target in ['n3', 'n4']:
        for combo_type in ['box', 'straight']:
            info = check_combination_data_file(target, combo_type)
            print_data_info(target, combo_type, info)
    
    # N3とN4の比較
    compare_n3_n4()
    
    print(f"\n{'='*60}")
    print("確認完了")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()

