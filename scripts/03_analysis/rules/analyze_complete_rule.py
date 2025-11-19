#!/usr/bin/env python3
"""
既存のkeisen_master.jsonのルールを最終的に明確化
3桁と4桁以上のパターンの選定ルールを完全に理解する
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

# 3桁と4桁以上のパターンを比較
three_digit_examples = []
four_or_more_examples = []

for n_type in ['n3', 'n4']:
    for column in keisen[n_type].keys():
        for prev2 in keisen[n_type][column].keys():
            for prev in keisen[n_type][column][prev2].keys():
                predictions = keisen[n_type][column][prev2][prev]
                
                if len(predictions) == 0:
                    continue
                
                # 該当パターンのデータを抽出
                if n_type == 'n3':
                    column_index = {'百の位': 0, '十の位': 1, '一の位': 2}[column]
                    pattern_data = []
                    for _, row in df.iterrows():
                        prev2_digit = int(str(row['prev2_n3'])[column_index])
                        prev_digit = int(str(row['prev_n3'])[column_index])
                        winning_digit = int(str(row['n3_winning'])[column_index])
                        
                        if prev2_digit == int(prev2) and prev_digit == int(prev):
                            pattern_data.append(winning_digit)
                else:
                    continue
                
                if len(pattern_data) == 0:
                    continue
                
                digit_counts = Counter(pattern_data)
                sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
                
                # 上位3位の情報
                top3_digits = [d for d, _ in sorted_digits[:3]]
                top3_counts = [count for _, count in sorted_digits[:3]]
                top3_min_count = min(top3_counts) if top3_counts else 0
                
                # 4位以降の情報
                if len(sorted_digits) > 3:
                    remaining_digits = [d for d, _ in sorted_digits[3:]]
                    remaining_counts = [count for _, count in sorted_digits[3:]]
                    remaining_max_count = max(remaining_counts) if remaining_counts else 0
                else:
                    remaining_max_count = 0
                
                # 予測出目の情報
                prediction_counts = [digit_counts.get(d, 0) for d in predictions]
                min_prediction_count = min(prediction_counts) if prediction_counts else 0
                excluded_digits = [d for d, _ in sorted_digits if d not in predictions]
                max_excluded_count = max([digit_counts.get(d, 0) for d in excluded_digits]) if excluded_digits else 0
                
                # ルール1: 上位3位の最小 >= 4位以降の最大
                rule1_satisfied = top3_min_count >= remaining_max_count
                
                # ルール2: 予測出目の最小 >= 除外最大
                rule2_satisfied = min_prediction_count >= max_excluded_count
                
                info = {
                    'n_type': n_type,
                    'column': column,
                    'prev2': int(prev2),
                    'prev': int(prev),
                    'predictions': predictions,
                    'digit_count': len(predictions),
                    'sample_size': len(pattern_data),
                    'top3_digits': top3_digits,
                    'top3_min_count': top3_min_count,
                    'remaining_max_count': remaining_max_count,
                    'rule1_satisfied': rule1_satisfied,
                    'min_prediction_count': min_prediction_count,
                    'max_excluded_count': max_excluded_count,
                    'rule2_satisfied': rule2_satisfied,
                    'sorted_digits': sorted_digits
                }
                
                if len(predictions) == 3:
                    three_digit_examples.append(info)
                elif len(predictions) >= 4:
                    four_or_more_examples.append(info)

print('=' * 60)
print('3桁と4桁以上のパターンの違いを明確化')
print('=' * 60)
print()

# 3桁パターンで、ルール1を満たすが上位3位と一致しない例
print('【3桁パターン】ルール1を満たすが上位3位と一致しない例:')
print()

three_digit_not_top3 = [p for p in three_digit_examples if p['predictions'] != p['top3_digits'] and p['rule1_satisfied']]

for i, p in enumerate(three_digit_not_top3[:3], 1):
    print(f'例{i}: {p["n_type"].upper()} {p["column"]} - 前々回={p["prev2"]}, 前回={p["prev"]}')
    print(f'  予測出目 (3桁): {p["predictions"]}')
    print(f'  上位3位: {p["top3_digits"]}')
    print(f'  上位3位の最小出現回数: {p["top3_min_count"]}回')
    print(f'  4位以降の最大出現回数: {p["remaining_max_count"]}回')
    print(f'  ルール1: {p["top3_min_count"]} >= {p["remaining_max_count"]}: ✅')
    print()
    print('  実データの出現回数（上位5位）:')
    for digit, count in p['sorted_digits'][:5]:
        mark = "✅" if digit in p['predictions'] else "❌"
        print(f'    数字{digit}: {count}回 {mark}')
    print()
    print('-' * 60)
    print()

# 4桁以上のパターンで、ルール1を満たす例
print('【4桁以上のパターン】ルール1を満たす例（同率の場合）:')
print()

four_or_more_rule1 = [p for p in four_or_more_examples if p['rule1_satisfied']]

for i, p in enumerate(four_or_more_rule1[:5], 1):
    print(f'例{i}: {p["n_type"].upper()} {p["column"]} - 前々回={p["prev2"]}, 前回={p["prev"]}')
    print(f'  予測出目 ({p["digit_count"]}桁): {p["predictions"]}')
    print(f'  上位3位: {p["top3_digits"]}')
    print(f'  上位3位の最小出現回数: {p["top3_min_count"]}回')
    print(f'  4位以降の最大出現回数: {p["remaining_max_count"]}回')
    print(f'  ルール1: {p["top3_min_count"]} >= {p["remaining_max_count"]}: ✅')
    print(f'  予測出目の最小出現回数: {p["min_prediction_count"]}回')
    print(f'  除外最大出現回数: {p["max_excluded_count"]}回')
    print(f'  ルール2: {p["min_prediction_count"]} >= {p["max_excluded_count"]}: {"✅" if p["rule2_satisfied"] else "❌"}')
    print()
    print('  実データの出現回数（全数字）:')
    for digit, count in p['sorted_digits']:
        mark = "✅" if digit in p['predictions'] else "❌"
        print(f'    数字{digit}: {count}回 {mark}')
    print()
    print('-' * 60)
    print()

# ルールの最終的な理解
print('=' * 60)
print('最終的なルールの理解')
print('=' * 60)
print()
print('【ルールの適用順序】')
print()
print('1. まず、上位3位の最小出現回数 >= 4位以降の最大出現回数 をチェック')
print('   - この条件を満たし、かつ上位3位の最小 > 4位以降の最大 の場合:')
print('     → 上位3位のみを予測出目とする（3桁）')
print()
print('2. 上位3位の最小出現回数 = 4位以降の最大出現回数 の場合（同率）:')
print('   → ルール2を適用: 予測出目の最小出現回数 >= 除外された数字の最大出現回数')
print('   → この条件を満たす数字を全て含める（4桁以上）')
print()
print('3. 上位3位の最小出現回数 < 4位以降の最大出現回数 の場合:')
print('   → ルール2を適用: 予測出目の最小出現回数 >= 除外された数字の最大出現回数')
print('   → この条件を満たす数字を全て含める（4桁以上）')
print()

