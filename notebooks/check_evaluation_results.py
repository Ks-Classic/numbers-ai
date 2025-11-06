#!/usr/bin/env python3
"""
評価結果確認CLIツール

保存された評価結果を表示します。

使用方法:
    python check_evaluation_results.py                    # 現在の評価結果を表示
    python check_evaluation_results.py --file path/to/file  # 指定ファイルを表示
    python check_evaluation_results.py --all               # すべての評価結果ファイルを表示
"""

import argparse
import pickle
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

# プロジェクトルートのパスを設定
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()

DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'


def load_evaluation_results(file_path: Path) -> Optional[Dict]:
    """評価結果ファイルを読み込む"""
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        print(f"エラー: ファイルの読み込みに失敗しました: {file_path}")
        print(f"  エラー内容: {e}")
        return None


def print_evaluation_results(data: Dict, file_name: str):
    """評価結果を表示する"""
    print("\n" + "="*80)
    print(f"評価結果: {file_name}")
    print("="*80)
    
    # モデルバージョン情報があれば表示
    if 'model_version' in data:
        print(f"\nモデルバージョン: {data['model_version']}")
    
    # 軸数字予測モデルの評価結果
    if 'axis_results' in data:
        print("\n" + "-"*80)
        print("軸数字予測モデルの評価結果")
        print("-"*80)
        
        axis_results = data['axis_results']
        if isinstance(axis_results, list) and len(axis_results) > 0:
            df = pd.DataFrame(axis_results)
            print("\n評価指標の一覧:")
            print(df.to_string(index=False))
            
            print("\n各評価指標の平均値:")
            print(f"  AUC-ROC: {df['auc_roc'].mean():.4f}")
            print(f"  Precision: {df['precision'].mean():.4f}")
            print(f"  Recall: {df['recall'].mean():.4f}")
            print(f"  F1-Score: {df['f1_score'].mean():.4f}")
            print(f"  Top-5 Accuracy: {df['top_5_accuracy'].mean():.4f}")
            
            print("\n目標値との比較:")
            print(f"  AUC-ROC目標: 0.65以上")
            for _, row in df.iterrows():
                status = "✅" if row['auc_roc'] >= 0.65 else "❌"
                print(f"    {row['model_name']}: {row['auc_roc']:.4f} {status}")
    
    # 組み合わせ予測モデルの評価結果
    if 'comb_results' in data:
        print("\n" + "-"*80)
        print("組み合わせ予測モデルの評価結果")
        print("-"*80)
        
        comb_results = data['comb_results']
        if isinstance(comb_results, list) and len(comb_results) > 0:
            df = pd.DataFrame(comb_results)
            print("\n評価指標の一覧:")
            print(df.to_string(index=False))
            
            print("\n各評価指標の平均値:")
            print(f"  AUC-ROC: {df['auc_roc'].mean():.4f}")
            print(f"  Precision: {df['precision'].mean():.4f}")
            print(f"  Recall: {df['recall'].mean():.4f}")
            print(f"  F1-Score: {df['f1_score'].mean():.4f}")
            print(f"  Top-5 Accuracy: {df['top_5_accuracy'].mean():.4f}")
            
            print("\n目標値との比較:")
            print(f"  AUC-ROC目標: 0.65以上")
            for _, row in df.iterrows():
                status = "✅" if row['auc_roc'] >= 0.65 else "❌"
                print(f"    {row['model_name']}: {row['auc_roc']:.4f} {status}")
    
    # 全結果の統合
    if 'all_results' in data:
        print("\n" + "-"*80)
        print("全モデルの評価結果サマリー")
        print("-"*80)
        
        all_results = data['all_results']
        if isinstance(all_results, list) and len(all_results) > 0:
            df = pd.DataFrame(all_results)
            print("\n評価指標の一覧:")
            print(df.to_string(index=False))
            
            print("\n各評価指標の平均値:")
            print(f"  AUC-ROC: {df['auc_roc'].mean():.4f}")
            print(f"  Precision: {df['precision'].mean():.4f}")
            print(f"  Recall: {df['recall'].mean():.4f}")
            print(f"  F1-Score: {df['f1_score'].mean():.4f}")
            print(f"  Top-5 Accuracy: {df['top_5_accuracy'].mean():.4f}")
            
            print("\n目標値との比較:")
            print(f"  AUC-ROC目標: 0.65以上")
            for _, row in df.iterrows():
                status = "✅" if row['auc_roc'] >= 0.65 else "❌"
                print(f"    {row['model_name']}: {row['auc_roc']:.4f} {status}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='モデル評価結果確認CLIツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python check_evaluation_results.py                    # 現在の評価結果を表示
  python check_evaluation_results.py --file path/to/file  # 指定ファイルを表示
  python check_evaluation_results.py --all               # すべての評価結果ファイルを表示
        """
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='評価結果ファイルのパス（指定しない場合はデフォルトファイルを表示）'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='すべての評価結果ファイルを表示'
    )
    
    args = parser.parse_args()
    
    # 評価結果ファイルのパスを決定
    if args.all:
        # すべての評価結果ファイルを表示
        eval_files = list(MODELS_DIR.glob('evaluation_results*.pkl'))
        if not eval_files:
            print(f"エラー: 評価結果ファイルが見つかりません: {MODELS_DIR}")
            sys.exit(1)
        
        print(f"見つかった評価結果ファイル: {len(eval_files)}件")
        for eval_file in sorted(eval_files):
            data = load_evaluation_results(eval_file)
            if data:
                print_evaluation_results(data, eval_file.name)
                print("\n")
    elif args.file:
        # 指定されたファイルを表示
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = MODELS_DIR / file_path
        
        data = load_evaluation_results(file_path)
        if data:
            print_evaluation_results(data, file_path.name)
    else:
        # デフォルトファイルを表示
        default_files = [
            MODELS_DIR / 'evaluation_results.pkl',
            MODELS_DIR / 'evaluation_results_axis.pkl'
        ]
        
        found = False
        for eval_file in default_files:
            if eval_file.exists():
                data = load_evaluation_results(eval_file)
                if data:
                    print_evaluation_results(data, eval_file.name)
                    found = True
        
        if not found:
            print(f"エラー: 評価結果ファイルが見つかりません: {MODELS_DIR}")
            print(f"  期待されるファイル:")
            for f in default_files:
                print(f"    - {f.name}")
            sys.exit(1)


if __name__ == '__main__':
    main()

