#!/usr/bin/env python3
"""
既存のkeisen_master.jsonの3桁パターンがどのように選定されているか確認
"""

import json
import pandas as pd
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# keisen_master.jsonを読み込む
with open(DATA_DIR / "keisen_master.json", 'r', encoding='utf-8') as f:
    keisen = json.load(f)

# 3桁のパターンを探す
three_digit_predictions = []
for n_type in ['n3', 'n4']:
    for column in keisen[n_type].keys():
        for prev2 in keisen[n_type][column].keys():
            for prev in keisen[n_type][column][prev2].keys():
                predictions = keisen[n_type][column][prev2][prev]
                if len(predictions) == 3:
                    three_digit_predictions.append({
                        'n_type': n_type,
                        'column': column,
                        'prev2': prev2,
                        'prev': prev,
                        'predictions': predictions
                    })

print(f'3桁のパターン数: {len(three_digit_predictions)}')
print()

# データを読み込んで、これらのパターンがどのようなルールで選ばれているか分析
df = pd.read_csv(DATA_DIR / "past_results.csv", na_values=['NULL', 'null', ''])
df = df[(df['round_number'] >= 1340) & (df['round_number'] <= 6391)]
df = df.dropna(subset=['n3_winning', 'n4_winning'])
df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df['n4_winning'] = df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
df['n3_winning'] = df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'nan' else x)
df['n4_winning'] = df['n4_winning'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'nan' else x)
df = df[df['n3_winning'].astype(str).str.len() == 3]
df = df[df['n4_winning'].astype(str).str.len() == 4]
df = df.sort_values('round_number')

# 前回・前々回を抽出
df['prev_n3'] = df['n3_winning'].shift(1)
df['prev2_n3'] = df['n3_winning'].shift(2)
df['prev_n4'] = df['n4_winning'].shift(1)
df['prev2_n4'] = df['n4_winning'].shift(2)
df = df.dropna(subset=['prev_n3', 'prev2_n3', 'prev_n4', 'prev2_n4'])

print('=' * 60)
print('3桁パターンの分析（上位10件）')
print('=' * 60)
print()

# 各パターンについて、実データでの出現回数を確認
for i, item in enumerate(three_digit_predictions[:10], 1):
    n_type = item['n_type']
    column = item['column']
    prev2 = int(item['prev2'])
    prev = int(item['prev'])
    predictions = item['predictions']
    
    # 該当パターンのデータを抽出
    if n_type == 'n3':
        prev_col = 'prev_n3'
        prev2_col = 'prev2_n3'
        winning_col = 'n3_winning'
        column_index = {'百の位': 0, '十の位': 1, '一の位': 2}[column]
    else:
        prev_col = 'prev_n4'
        prev2_col = 'prev2_n4'
        winning_col = 'n4_winning'
        column_index = {'千の位': 0, '百の位': 1, '十の位': 2, '一の位': 3}[column]
    
    pattern_data = []
    for _, row in df.iterrows():
        prev2_digit = int(str(row[prev2_col])[column_index])
        prev_digit = int(str(row[prev_col])[column_index])
        winning_digit = int(str(row[winning_col])[column_index])
        
        if prev2_digit == prev2 and prev_digit == prev:
            pattern_data.append(winning_digit)
    
    if len(pattern_data) == 0:
        continue
    
    # 出現回数を集計
    digit_counts = Counter(pattern_data)
    
    # 出現回数の降順でソート
    sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
    
    # 予測出目の数字の出現回数を取得
    prediction_counts = [digit_counts.get(d, 0) for d in predictions]
    
    # 最小出現回数と最大出現回数を計算
    min_count = min(prediction_counts) if prediction_counts else 0
    max_count = max(prediction_counts) if prediction_counts else 0
    
    # 予測出目に含まれていない数字の最大出現回数
    excluded_digits = [d for d, _ in sorted_digits if d not in predictions]
    max_excluded_count = max([digit_counts.get(d, 0) for d in excluded_digits]) if excluded_digits else 0
    
    print(f'例{i}: {n_type.upper()} {column} - 前々回={prev2}, 前回={prev}')
    print(f'  予測出目 (3桁): {predictions}')
    print(f'  サンプル数: {len(pattern_data)}回')
    print(f'  予測出目の出現回数: {prediction_counts}')
    print(f'  最小出現回数: {min_count}回')
    print(f'  最大出現回数: {max_count}回')
    print(f'  除外された数字の最大出現回数: {max_excluded_count}回')
    print(f'  最小出現回数 >= 除外最大出現回数: {"✅" if min_count >= max_excluded_count else "❌"}')
    print()
    print('  実データの出現回数（上位5位）:')
    for digit, count in sorted_digits[:5]:
        mark = "✅" if digit in predictions else "❌"
        print(f'    数字{digit}: {count}回 {mark}')
    print()
    print('-' * 60)
    print()

