#!/usr/bin/env python3
"""
既存のkeisen_master.jsonの3桁と4桁以上のパターンを分析
どういう条件で3桁になり、どういう条件で4桁以上になるかを確認
"""

import json
import pandas as pd
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# keisen_master.jsonを読み込む
with open(DATA_DIR / "keisen_master.json", 'r', encoding='utf-8') as f:
    keisen = json.load(f)

# データを読み込む
df = pd.read_csv(DATA_DIR / "past_results.csv", na_values=['NULL', 'null', ''])
df = df[(df['round_number'] >= 1340) & (df['round_number'] <= 6391)]
df = df.dropna(subset=['n3_winning', 'n4_winning'])
df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df['n3_winning'] = df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'nan' else x)
df = df[df['n3_winning'].astype(str).str.len() == 3]
df = df.sort_values('round_number')

# 前回・前々回を抽出
df['prev_n3'] = df['n3_winning'].shift(1)
df['prev2_n3'] = df['n3_winning'].shift(2)
df = df.dropna(subset=['prev_n3', 'prev2_n3'])

# 3桁と4桁以上のパターンを分類
three_digit_patterns = []
four_or_more_patterns = []

for n_type in ['n3', 'n4']:
    for column in keisen[n_type].keys():
        for prev2 in keisen[n_type][column].keys():
            for prev in keisen[n_type][column][prev2].keys():
                predictions = keisen[n_type][column][prev2][prev]
                if len(predictions) == 3:
                    three_digit_patterns.append({
                        'n_type': n_type,
                        'column': column,
                        'prev2': int(prev2),
                        'prev': int(prev),
                        'predictions': predictions
                    })
                elif len(predictions) >= 4:
                    four_or_more_patterns.append({
                        'n_type': n_type,
                        'column': column,
                        'prev2': int(prev2),
                        'prev': int(prev),
                        'predictions': predictions,
                        'digit_count': len(predictions)
                    })

print('=' * 60)
print('既存のkeisen_master.jsonのパターン分類')
print('=' * 60)
print()
print(f'3桁のパターン数: {len(three_digit_patterns)}')
print(f'4桁以上のパターン数: {len(four_or_more_patterns)}')
print()

# 3桁パターンの分析
print('=' * 60)
print('3桁パターンの分析（上位10件）')
print('=' * 60)
print()

three_digit_analysis = []

for item in three_digit_patterns[:10]:
    n_type = item['n_type']
    column = item['column']
    prev2 = item['prev2']
    prev = item['prev']
    predictions = item['predictions']
    
    # 該当パターンのデータを抽出
    if n_type == 'n3':
        column_index = {'百の位': 0, '十の位': 1, '一の位': 2}[column]
        pattern_data = []
        for _, row in df.iterrows():
            prev2_digit = int(str(row['prev2_n3'])[column_index])
            prev_digit = int(str(row['prev_n3'])[column_index])
            winning_digit = int(str(row['n3_winning'])[column_index])
            
            if prev2_digit == prev2 and prev_digit == prev:
                pattern_data.append(winning_digit)
    
    if len(pattern_data) == 0:
        continue
    
    digit_counts = Counter(pattern_data)
    sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
    
    prediction_counts = [digit_counts.get(d, 0) for d in predictions]
    min_count = min(prediction_counts) if prediction_counts else 0
    excluded = [d for d, _ in sorted_digits if d not in predictions]
    max_excluded_count = max([digit_counts.get(d, 0) for d in excluded]) if excluded else 0
    
    # 上位3位の出現回数
    top3_counts = [count for _, count in sorted_digits[:3]]
    top3_min_count = min(top3_counts) if top3_counts else 0
    
    # 4位以降の最大出現回数
    if len(sorted_digits) > 3:
        remaining_max_count = max([count for _, count in sorted_digits[3:]])
    else:
        remaining_max_count = 0
    
    three_digit_analysis.append({
        'item': item,
        'sample_size': len(pattern_data),
        'min_count': min_count,
        'max_excluded_count': max_excluded_count,
        'top3_min_count': top3_min_count,
        'remaining_max_count': remaining_max_count,
        'sorted_digits': sorted_digits
    })
    
    print(f'例{len(three_digit_analysis)}: {n_type.upper()} {column} - 前々回={prev2}, 前回={prev}')
    print(f'  予測出目 (3桁): {predictions}')
    print(f'  サンプル数: {len(pattern_data)}回')
    print(f'  予測出目の最小出現回数: {min_count}回')
    print(f'  除外された数字の最大出現回数: {max_excluded_count}回')
    print(f'  ルール確認: {min_count} >= {max_excluded_count}: {"✅" if min_count >= max_excluded_count else "❌"}')
    print()
    print(f'  上位3位の最小出現回数: {top3_min_count}回')
    print(f'  4位以降の最大出現回数: {remaining_max_count}回')
    print(f'  上位3位の最小 >= 4位以降の最大: {top3_min_count} >= {remaining_max_count}: {"✅" if top3_min_count >= remaining_max_count else "❌"}')
    print()
    print('  実データの出現回数（上位5位）:')
    for digit, count in sorted_digits[:5]:
        mark = "✅" if digit in predictions else "❌"
        print(f'    数字{digit}: {count}回 {mark}')
    print()
    print('-' * 60)
    print()

# 4桁以上のパターンの分析
print('=' * 60)
print('4桁以上のパターンの分析（上位10件）')
print('=' * 60)
print()

four_or_more_analysis = []

for item in sorted(four_or_more_patterns, key=lambda x: x['digit_count'], reverse=True)[:10]:
    n_type = item['n_type']
    column = item['column']
    prev2 = item['prev2']
    prev = item['prev']
    predictions = item['predictions']
    digit_count = item['digit_count']
    
    # 該当パターンのデータを抽出
    if n_type == 'n3':
        column_index = {'百の位': 0, '十の位': 1, '一の位': 2}[column]
        pattern_data = []
        for _, row in df.iterrows():
            prev2_digit = int(str(row['prev2_n3'])[column_index])
            prev_digit = int(str(row['prev_n3'])[column_index])
            winning_digit = int(str(row['n3_winning'])[column_index])
            
            if prev2_digit == prev2 and prev_digit == prev:
                pattern_data.append(winning_digit)
    
    if len(pattern_data) == 0:
        continue
    
    digit_counts = Counter(pattern_data)
    sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
    
    prediction_counts = [digit_counts.get(d, 0) for d in predictions]
    min_count = min(prediction_counts) if prediction_counts else 0
    excluded = [d for d, _ in sorted_digits if d not in predictions]
    max_excluded_count = max([digit_counts.get(d, 0) for d in excluded]) if excluded else 0
    
    # 上位3位の出現回数
    top3_counts = [count for _, count in sorted_digits[:3]]
    top3_min_count = min(top3_counts) if top3_counts else 0
    
    # 4位以降の最大出現回数
    if len(sorted_digits) > 3:
        remaining_max_count = max([count for _, count in sorted_digits[3:]])
    else:
        remaining_max_count = 0
    
    four_or_more_analysis.append({
        'item': item,
        'sample_size': len(pattern_data),
        'min_count': min_count,
        'max_excluded_count': max_excluded_count,
        'top3_min_count': top3_min_count,
        'remaining_max_count': remaining_max_count,
        'sorted_digits': sorted_digits
    })
    
    print(f'例{len(four_or_more_analysis)}: {n_type.upper()} {column} - 前々回={prev2}, 前回={prev}')
    print(f'  予測出目 ({digit_count}桁): {predictions}')
    print(f'  サンプル数: {len(pattern_data)}回')
    print(f'  予測出目の最小出現回数: {min_count}回')
    print(f'  除外された数字の最大出現回数: {max_excluded_count}回')
    print(f'  ルール確認: {min_count} >= {max_excluded_count}: {"✅" if min_count >= max_excluded_count else "❌"}')
    print()
    print(f'  上位3位の最小出現回数: {top3_min_count}回')
    print(f'  4位以降の最大出現回数: {remaining_max_count}回')
    print(f'  上位3位の最小 >= 4位以降の最大: {top3_min_count} >= {remaining_max_count}: {"✅" if top3_min_count >= remaining_max_count else "❌"}')
    print()
    print('  実データの出現回数（全数字）:')
    for digit, count in sorted_digits:
        mark = "✅" if digit in predictions else "❌"
        print(f'    数字{digit}: {count}回 {mark}')
    print()
    print('-' * 60)
    print()

# ルールの違いを分析
print('=' * 60)
print('3桁と4桁以上のパターンのルールの違い')
print('=' * 60)
print()

# 3桁パターンの特徴
three_digit_top3_rule_match = sum(1 for a in three_digit_analysis if a['top3_min_count'] >= a['remaining_max_count'])
three_digit_rule_match = sum(1 for a in three_digit_analysis if a['min_count'] >= a['max_excluded_count'])

print('3桁パターンの特徴:')
print(f'  分析したパターン数: {len(three_digit_analysis)}')
print(f'  上位3位の最小 >= 4位以降の最大 を満たす: {three_digit_top3_rule_match}パターン ({three_digit_top3_rule_match/len(three_digit_analysis)*100:.1f}%)')
print(f'  予測出目の最小 >= 除外最大 を満たす: {three_digit_rule_match}パターン ({three_digit_rule_match/len(three_digit_analysis)*100:.1f}%)')
print()

# 4桁以上のパターンの特徴
four_or_more_top3_rule_match = sum(1 for a in four_or_more_analysis if a['top3_min_count'] >= a['remaining_max_count'])
four_or_more_rule_match = sum(1 for a in four_or_more_analysis if a['min_count'] >= a['max_excluded_count'])

print('4桁以上のパターンの特徴:')
print(f'  分析したパターン数: {len(four_or_more_analysis)}')
print(f'  上位3位の最小 >= 4位以降の最大 を満たす: {four_or_more_top3_rule_match}パターン ({four_or_more_top3_rule_match/len(four_or_more_analysis)*100:.1f}%)')
print(f'  予測出目の最小 >= 除外最大 を満たす: {four_or_more_rule_match}パターン ({four_or_more_rule_match/len(four_or_more_analysis)*100:.1f}%)')
print()

# ルールの推測
print('=' * 60)
print('ルールの推測')
print('=' * 60)
print()
print('3桁パターンの場合:')
print('  上位3位の最小出現回数 >= 4位以降の最大出現回数 の条件を満たす場合、')
print('  上位3位のみを予測出目とする')
print()
print('4桁以上のパターンの場合:')
print('  上位3位の最小出現回数 < 4位以降の最大出現回数 の条件の場合、')
print('  予測出目の最小出現回数 >= 除外された数字の最大出現回数 のルールを適用して、')
print('  条件を満たす数字を全て含める')
print()

