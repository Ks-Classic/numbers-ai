#!/usr/bin/env python3
"""
特徴量エンジニアリングと学習データ生成スクリプト（簡易版）

注意: 1000回分のデータ処理には時間がかかります（数時間の可能性）。
     本番実行はJupyter Notebookで行うことを推奨します。
     このスクリプトは設定確認と小規模テスト用です。
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
from itertools import product
warnings.filterwarnings('ignore')

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / 'data'

# 設定ファイルをインポート
import sys
sys.path.append(str(PROJECT_ROOT / 'notebooks'))
from config import TRAIN_SIZE, TRAIN_DATA_CSV, MAX_COMBINATIONS_PER_DIGIT

# モジュールをインポート
from chart_generator import (
    load_keisen_master,
    generate_chart,
    Pattern,
    Target
)
from feature_extractor import (
    extract_digit_features,
    extract_combination_features,
    add_pattern_id_features,
    features_to_vector,
    get_rehearsal_positions
)

print(f"プロジェクトルート: {PROJECT_ROOT}")
print(f"データディレクトリ: {DATA_DIR}")
print(f"\n学習設定:")
print(f"  学習範囲: {TRAIN_SIZE}回分")
print(f"  データファイル: {TRAIN_DATA_CSV}")

# データの読み込み
train_csv_path = DATA_DIR / TRAIN_DATA_CSV

if train_csv_path.exists():
    train_df = pd.read_csv(train_csv_path)
    print(f"\n学習用データセット: {len(train_df)}回分")
else:
    print(f"エラー: {train_csv_path} が見つかりません")
    print("先に01_data_preparationを実行してください")
    sys.exit(1)

# 当選番号を文字列型に変換
train_df['n3_winning'] = train_df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
train_df['n4_winning'] = train_df['n4_winning'].astype(str).str.replace('.0', '', regex=False)

print(f"回号範囲: {train_df['round_number'].min()} 〜 {train_df['round_number'].max()}")

# 罫線マスターデータの読み込み
keisen_master = load_keisen_master(DATA_DIR)
print("\n罫線マスターデータの読み込み完了")

# テスト: 特徴量抽出の動作確認（最初の1回のみ）
test_round = train_df['round_number'].max()
test_target: Target = 'n3'
test_pattern: Pattern = 'A1'

print(f"\nテスト: 特徴量抽出の動作確認")
print(f"テスト回号: {test_round}, パターン: {test_pattern}, 対象: {test_target}")

grid, rows, cols = generate_chart(
    train_df, keisen_master, test_round, test_pattern, test_target
)

rehearsal_row = train_df[train_df['round_number'] == test_round - 1]
if len(rehearsal_row) > 0:
    rehearsal_digits = rehearsal_row['n3_winning'].iloc[0] if test_target == 'n3' else rehearsal_row['n4_winning'].iloc[0]
    rehearsal_positions = get_rehearsal_positions(grid, rows, cols, rehearsal_digits)
else:
    rehearsal_positions = None

test_digit = 5
features = extract_digit_features(
    grid, rows, cols, test_digit, rehearsal_positions
)
features = add_pattern_id_features(features, test_pattern)

print(f"テスト数字: {test_digit}")
print(f"抽出された特徴量数: {len(features)}")
print(f"特徴量の例（最初の10個）:")
for i, (key, value) in enumerate(list(features.items())[:10]):
    print(f"  {key}: {value}")

print("\n✓ 特徴量抽出のテストが完了しました")
print("\n⚠️  注意: 全データの特徴量抽出と学習データ生成は時間がかかります。")
print("   本番実行はJupyter Notebook (03_feature_engineering.ipynb) で行ってください。")
print(f"   推定処理時間: {TRAIN_SIZE}回分 × 4パターン × 2対象 = 約{TRAIN_SIZE * 4 * 2}回の予測表生成")

