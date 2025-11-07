#!/usr/bin/env python3
"""
新しく生成されたkeisen_master_new.jsonの1つのパターンについて
ルールがどのように適用されているか確認
"""

import json
import pandas as pd
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# 新しく生成されたkeisen_master_new.jsonを確認
with open(DATA_DIR / "keisen_master_new.json", 'r', encoding='utf-8') as f:
    keisen_new = json.load(f)

# データを読み込む
df = pd.read_csv(DATA_DIR / "past_results.csv", na_values=['NULL', 'null', ''])
df = df[(df['round_number'] >= 4801) & (df['round_number'] <= 6850)]
df = df.dropna(subset=['n3_winning', 'n4_winning'])
df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df['n3_winning'] = df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'nan' else x)
df = df[df['n3_winning'].astype(str).str.len() == 3]
df = df.sort_values('round_number')

# 前回・前々回を抽出
df['prev_n3'] = df['n3_winning'].shift(1)
df['prev2_n3'] = df['n3_winning'].shift(2)
df = df.dropna(subset=['prev_n3', 'prev2_n3'])

# 既存のkeisen_master.jsonで3桁のパターンを確認
with open(DATA_DIR / "keisen_master.json", 'r', encoding='utf-8') as f:
    keisen_old = json.load(f)

print('=' * 60)
print('既存のkeisen_master.jsonの3桁パターンと新規データの比較')
print('=' * 60)
print()

# 例: N3 百の位 - 前々回=0, 前回=0
column = '百の位'
prev2 = '0'
prev = '0'

old_predictions = keisen_old['n3'][column][prev2][prev]
new_predictions = keisen_new['n3'][column][prev2][prev]

print(f'パターン: N3 {column} - 前々回={prev2}, 前回={prev}')
print(f'既存のkeisen_master.jsonの予測出目: {old_predictions} ({len(old_predictions)}桁)')
print(f'新規のkeisen_master_new.jsonの予測出目: {new_predictions} ({len(new_predictions)}桁)')
print()

# 実データでの出現回数を確認
pattern_data = []
for _, row in df.iterrows():
    prev2_digit = int(str(row['prev2_n3'])[0])
    prev_digit = int(str(row['prev_n3'])[0])
    winning_digit = int(str(row['n3_winning'])[0])
    
    if prev2_digit == int(prev2) and prev_digit == int(prev):
        pattern_data.append(winning_digit)

if len(pattern_data) > 0:
    digit_counts = Counter(pattern_data)
    sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
    
    print(f'サンプル数: {len(pattern_data)}回')
    print()
    print('実データの出現回数（全数字）:')
    for digit, count in sorted_digits:
        old_mark = "✅" if digit in old_predictions else "❌"
        new_mark = "✅" if digit in new_predictions else "❌"
        print(f'  数字{digit}: {count}回 (既存: {old_mark}, 新規: {new_mark})')
    print()
    
    # 既存の予測出目のルール確認
    old_prediction_counts = [digit_counts.get(d, 0) for d in old_predictions]
    old_min_count = min(old_prediction_counts) if old_prediction_counts else 0
    old_excluded = [d for d, _ in sorted_digits if d not in old_predictions]
    old_max_excluded_count = max([digit_counts.get(d, 0) for d in old_excluded]) if old_excluded else 0
    
    print('既存のkeisen_master.jsonのルール確認:')
    print(f'  予測出目の最小出現回数: {old_min_count}回')
    print(f'  除外された数字の最大出現回数: {old_max_excluded_count}回')
    print(f'  {old_min_count} >= {old_max_excluded_count}: {"✅" if old_min_count >= old_max_excluded_count else "❌"}')
    print()
    
    # 新規の予測出目のルール確認
    new_prediction_counts = [digit_counts.get(d, 0) for d in new_predictions]
    new_min_count = min(new_prediction_counts) if new_prediction_counts else 0
    new_excluded = [d for d, _ in sorted_digits if d not in new_predictions]
    new_max_excluded_count = max([digit_counts.get(d, 0) for d in new_excluded]) if new_excluded else 0
    
    print('新規のkeisen_master_new.jsonのルール確認:')
    print(f'  予測出目の最小出現回数: {new_min_count}回')
    print(f'  除外された数字の最大出現回数: {new_max_excluded_count}回')
    print(f'  {new_min_count} >= {new_max_excluded_count}: {"✅" if new_min_count >= new_max_excluded_count else "❌"}')
    print()
    
    # ルール適用の過程をシミュレート
    print('ルール適用の過程（新規データの生成方法）:')
    predictions = []
    for i, (digit, count) in enumerate(sorted_digits):
        if i == 0:
            predictions.append(digit)
            print(f'  ステップ{i+1}: 数字{digit}を追加（出現回数: {count}回）')
        else:
            included_counts = [digit_counts.get(d, 0) for d in predictions]
            min_included_count = min(included_counts) if included_counts else 0
            excluded_digits = [d for d, _ in sorted_digits if d not in predictions]
            excluded_counts = [digit_counts.get(d, 0) for d in excluded_digits]
            max_excluded_count = max(excluded_counts) if excluded_counts else 0
            
            new_min_included_count = min(min_included_count, count)
            remaining_excluded = [d for d in excluded_digits if d != digit]
            remaining_excluded_counts = [digit_counts.get(d, 0) for d in remaining_excluded]
            new_max_excluded_count = max(remaining_excluded_counts) if remaining_excluded_counts else 0
            
            if new_min_included_count >= new_max_excluded_count:
                predictions.append(digit)
                print(f'  ステップ{i+1}: 数字{digit}を追加（出現回数: {count}回, 最小出現回数: {new_min_included_count}回 >= 除外最大出現回数: {new_max_excluded_count}回）✅')
            else:
                print(f'  ステップ{i+1}: 数字{digit}を追加しない（出現回数: {count}回, 最小出現回数: {new_min_included_count}回 < 除外最大出現回数: {new_max_excluded_count}回）❌')
                break
    
    print()
    print(f'生成された予測出目: {predictions} ({len(predictions)}桁)')
    print(f'実際の新規データ: {new_predictions} ({len(new_predictions)}桁)')
    print(f'一致: {"✅" if predictions == new_predictions else "❌"}')

