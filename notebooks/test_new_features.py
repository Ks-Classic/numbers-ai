#!/usr/bin/env python3
"""
新規特徴量の統合テストスクリプト

新しく追加した特徴量が正しく計算されることを確認します。
"""

import sys
from pathlib import Path

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
DATA_DIR = PROJECT_ROOT / 'data'

# 設定ファイルをインポート
sys.path.append(str(PROJECT_ROOT / 'notebooks'))
from feature_extractor import extract_digit_features, get_rehearsal_positions
from chart_generator import generate_chart, load_keisen_master
from config import TRAIN_DATA_CSV

print("=" * 60)
print("新規特徴量の統合テスト")
print("=" * 60)

# データの読み込み
print("\n1. データの読み込み中...")
import pandas as pd
from config import TRAIN_DATA_CSV

train_csv_path = DATA_DIR / TRAIN_DATA_CSV
if train_csv_path.exists():
    train_df = pd.read_csv(train_csv_path)
else:
    print(f"エラー: {train_csv_path} が見つかりません")
    sys.exit(1)

train_df['n3_winning'] = train_df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
train_df['n4_winning'] = train_df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
keisen_master = load_keisen_master(DATA_DIR)
print("✓ データの読み込み完了")

# テスト用のデータを準備
test_round = train_df['round_number'].max()
test_target = 'n3'
test_pattern = 'A1'
test_digit = 5

print(f"\n2. テスト設定:")
print(f"   回号: {test_round}")
print(f"   対象: {test_target}")
print(f"   パターン: {test_pattern}")
print(f"   テスト数字: {test_digit}")

# 予測表を生成
print("\n3. 予測表を生成中...")
grid, rows, cols = generate_chart(
    train_df, keisen_master, test_round, test_pattern, test_target
)
print(f"✓ 予測表生成完了（{rows}行 × {cols}列）")

# リハーサル数字を取得
print("\n4. リハーサル数字を取得中...")
rehearsal_row = train_df[train_df['round_number'] == test_round - 1]
if len(rehearsal_row) > 0:
    rehearsal_digits = rehearsal_row['n3_winning'].iloc[0]
    rehearsal_positions = get_rehearsal_positions(grid, rows, cols, rehearsal_digits)
    print(f"✓ リハーサル数字: {rehearsal_digits}")
else:
    rehearsal_positions = None
    rehearsal_digits = None
    print("⚠ リハーサル数字が見つかりません（1回目）")

# 特徴量を抽出
print("\n5. 特徴量を抽出中...")
features = extract_digit_features(
    grid, rows, cols, test_digit, rehearsal_positions, rehearsal_digits
)
print(f"✓ 特徴量抽出完了")

# 特徴量の統計情報を表示
print("\n6. 特徴量の統計情報:")
print(f"   総特徴量数: {len(features)}")
print(f"   特徴量キー（ソート済み）: {len(sorted(features.keys()))}個")

# 新規追加された特徴量を確認
print("\n7. 新規追加された特徴量の確認:")

# 形状特徴量
shape_features = [
    'diagonal_line_length',
    'clustering_coefficient',
    'shape_complexity'
]

# 位置特徴量
position_features = [
    'quadrant_top_left',
    'quadrant_top_right',
    'quadrant_bottom_left',
    'quadrant_bottom_right',
    'edge_proximity'
]

# リハーサル数字関連特徴量
rehearsal_features = [
    'rehearsal_distance_bin_0_1',
    'rehearsal_distance_bin_1_2',
    'rehearsal_distance_bin_2_3',
    'rehearsal_distance_bin_3_plus',
    'rehearsal_angle',
    'rehearsal_digit_0_mean_distance',
    'rehearsal_digit_1_mean_distance',
    'rehearsal_digit_2_mean_distance',
    'rehearsal_digit_3_mean_distance'
]

print("\n  [形状特徴量]")
for feat in shape_features:
    if feat in features:
        print(f"    ✓ {feat}: {features[feat]}")
    else:
        print(f"    ✗ {feat}: 見つかりません")

print("\n  [位置特徴量]")
for feat in position_features:
    if feat in features:
        print(f"    ✓ {feat}: {features[feat]}")
    else:
        print(f"    ✗ {feat}: 見つかりません")

print("\n  [リハーサル数字関連特徴量]")
for feat in rehearsal_features:
    if feat in features:
        print(f"    ✓ {feat}: {features[feat]}")
    else:
        print(f"    ✗ {feat}: 見つかりません")

# リハーサルがない場合のテスト
print("\n8. リハーサル数字がない場合のテスト...")
features_no_rehearsal = extract_digit_features(
    grid, rows, cols, test_digit, None, None
)

# デフォルト値の確認
print("   リハーサル関連特徴量のデフォルト値:")
for feat in rehearsal_features:
    if feat in features_no_rehearsal:
        val = features_no_rehearsal[feat]
        if 'distance_bin' in feat:
            expected = 0.0
        elif 'angle' in feat:
            expected = 0.0
        elif 'mean_distance' in feat:
            expected = 999.0
        else:
            expected = None
        
        if expected is not None and abs(val - expected) < 0.001:
            print(f"    ✓ {feat}: {val} (期待値: {expected})")
        else:
            print(f"    ✗ {feat}: {val} (期待値: {expected})")
    else:
        print(f"    ✗ {feat}: 見つかりません")

# 特徴量数の比較
print("\n9. 特徴量数の比較:")
print(f"   リハーサルあり: {len(features)}次元")
print(f"   リハーサルなし: {len(features_no_rehearsal)}次元")
print(f"   差分: {len(features) - len(features_no_rehearsal)}次元（リハーサル関連のみ）")

# テスト結果のサマリー
print("\n" + "=" * 60)
print("テスト結果サマリー")
print("=" * 60)

all_new_features = shape_features + position_features + rehearsal_features
found_features = [f for f in all_new_features if f in features]
missing_features = [f for f in all_new_features if f not in features]

print(f"\n新規特徴量の検出状況:")
print(f"  ✓ 検出成功: {len(found_features)}/{len(all_new_features)}")
print(f"  ✗ 検出失敗: {len(missing_features)}/{len(all_new_features)}")

if missing_features:
    print(f"\n検出失敗した特徴量:")
    for feat in missing_features:
        print(f"    - {feat}")
else:
    print("\n✓ すべての新規特徴量が正しく検出されました！")

print("\n" + "=" * 60)
print("テスト完了")
print("=" * 60)

