#!/usr/bin/env python3
"""
keisen_master_new.jsonの桁数分布を分析
なぜ3桁が少ないのか確認
"""

import json
import pandas as pd
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# keisen_master_new.jsonを読み込む
with open(DATA_DIR / "keisen_master_new.json", 'r', encoding='utf-8') as f:
    keisen_new = json.load(f)

# 桁数分布を確認
digit_count_distribution = Counter()
total_patterns = 0
non_empty_patterns = 0

for n_type in ['n3', 'n4']:
    for column in keisen_new[n_type].keys():
        for prev2 in keisen_new[n_type][column].keys():
            for prev in keisen_new[n_type][column][prev2].keys():
                predictions = keisen_new[n_type][column][prev2][prev]
                total_patterns += 1
                if len(predictions) > 0:
                    non_empty_patterns += 1
                    digit_count_distribution[len(predictions)] += 1

print('=' * 60)
print('keisen_master_new.jsonの桁数分布')
print('=' * 60)
print()
print(f'総パターン数: {total_patterns}')
print(f'空でないパターン数: {non_empty_patterns}')
print()
print('予測出目の桁数分布:')
for digit_count in sorted(digit_count_distribution.keys()):
    count = digit_count_distribution[digit_count]
    percentage = count / non_empty_patterns * 100 if non_empty_patterns > 0 else 0
    print(f'  {digit_count}桁: {count}パターン ({percentage:.1f}%)')
print()

# データを読み込んで、実際の出現回数を確認
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

print('=' * 60)
print('実際のデータでの分析（N3 百の位の例）')
print('=' * 60)
print()

# 3桁のパターンと10桁のパターンを比較
three_digit_patterns = []
ten_digit_patterns = []

for prev2 in range(10):
    for prev in range(10):
        prev2_str = str(prev2)
        prev_str = str(prev)
        predictions = keisen_new['n3']['百の位'][prev2_str][prev_str]
        
        if len(predictions) == 3:
            three_digit_patterns.append((prev2, prev, predictions))
        elif len(predictions) == 10:
            ten_digit_patterns.append((prev2, prev, predictions))

print(f'3桁のパターン数: {len(three_digit_patterns)}')
print(f'10桁のパターン数: {len(ten_digit_patterns)}')
print()

# 3桁のパターンの例を分析
if len(three_digit_patterns) > 0:
    print('3桁パターンの例（上位3件）:')
    for i, (prev2, prev, predictions) in enumerate(three_digit_patterns[:3], 1):
        # 実データでの出現回数を確認
        pattern_data = []
        for _, row in df.iterrows():
            prev2_digit = int(str(row['prev2_n3'])[0])
            prev_digit = int(str(row['prev_n3'])[0])
            winning_digit = int(str(row['n3_winning'])[0])
            
            if prev2_digit == prev2 and prev_digit == prev:
                pattern_data.append(winning_digit)
        
        if len(pattern_data) > 0:
            from collections import Counter
            digit_counts = Counter(pattern_data)
            sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
            
            prediction_counts = [digit_counts.get(d, 0) for d in predictions]
            min_count = min(prediction_counts) if prediction_counts else 0
            excluded = [d for d, _ in sorted_digits if d not in predictions]
            max_excluded_count = max([digit_counts.get(d, 0) for d in excluded]) if excluded else 0
            
            print(f'例{i}: 前々回={prev2}, 前回={prev}')
            print(f'  予測出目: {predictions} ({len(predictions)}桁)')
            print(f'  サンプル数: {len(pattern_data)}回')
            print(f'  予測出目の最小出現回数: {min_count}回')
            print(f'  除外された数字の最大出現回数: {max_excluded_count}回')
            print(f'  ルール確認: {min_count} >= {max_excluded_count}: {"✅" if min_count >= max_excluded_count else "❌"}')
            print()
            print('  実データの出現回数（上位5位）:')
            for digit, count in sorted_digits[:5]:
                mark = "✅" if digit in predictions else "❌"
                print(f'    数字{digit}: {count}回 {mark}')
            print()
            print('-' * 60)
            print()

# 10桁のパターンの例を分析
if len(ten_digit_patterns) > 0:
    print('10桁パターンの例（上位3件）:')
    for i, (prev2, prev, predictions) in enumerate(ten_digit_patterns[:3], 1):
        # 実データでの出現回数を確認
        pattern_data = []
        for _, row in df.iterrows():
            prev2_digit = int(str(row['prev2_n3'])[0])
            prev_digit = int(str(row['prev_n3'])[0])
            winning_digit = int(str(row['n3_winning'])[0])
            
            if prev2_digit == prev2 and prev_digit == prev:
                pattern_data.append(winning_digit)
        
        if len(pattern_data) > 0:
            from collections import Counter
            digit_counts = Counter(pattern_data)
            sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
            
            prediction_counts = [digit_counts.get(d, 0) for d in predictions]
            min_count = min(prediction_counts) if prediction_counts else 0
            excluded = [d for d, _ in sorted_digits if d not in predictions]
            max_excluded_count = max([digit_counts.get(d, 0) for d in excluded]) if excluded else 0
            
            print(f'例{i}: 前々回={prev2}, 前回={prev}')
            print(f'  予測出目: {predictions} ({len(predictions)}桁)')
            print(f'  サンプル数: {len(pattern_data)}回')
            print(f'  予測出目の最小出現回数: {min_count}回')
            print(f'  除外された数字の最大出現回数: {max_excluded_count}回')
            print(f'  ルール確認: {min_count} >= {max_excluded_count}: {"✅" if min_count >= max_excluded_count else "❌"}')
            print()
            print('  実データの出現回数（全数字）:')
            for digit, count in sorted_digits:
                mark = "✅" if digit in predictions else "❌"
                print(f'    数字{digit}: {count}回 {mark}')
            print()
            print('-' * 60)
            print()

# 上位3位に絞った場合の比較
print('=' * 60)
print('上位3位に絞った場合との比較')
print('=' * 60)
print()

# 例: N3 百の位 - 前々回=0, 前回=0
prev2 = 0
prev = 0
predictions = keisen_new['n3']['百の位']['0']['0']

pattern_data = []
for _, row in df.iterrows():
    prev2_digit = int(str(row['prev2_n3'])[0])
    prev_digit = int(str(row['prev_n3'])[0])
    winning_digit = int(str(row['n3_winning'])[0])
    
    if prev2_digit == prev2 and prev_digit == prev:
        pattern_data.append(winning_digit)

if len(pattern_data) > 0:
    from collections import Counter
    digit_counts = Counter(pattern_data)
    sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
    
    top3 = [digit for digit, _ in sorted_digits[:3]]
    
    print(f'パターン: N3 百の位 - 前々回={prev2}, 前回={prev}')
    print(f'現在の予測出目: {predictions} ({len(predictions)}桁)')
    print(f'上位3位に絞った場合: {top3} (3桁)')
    print(f'サンプル数: {len(pattern_data)}回')
    print()
    print('実データの出現回数（上位5位）:')
    for digit, count in sorted_digits[:5]:
        current_mark = "✅" if digit in predictions else "❌"
        top3_mark = "✅" if digit in top3 else "❌"
        print(f'  数字{digit}: {count}回 (現在: {current_mark}, 上位3位: {top3_mark})')
    print()

