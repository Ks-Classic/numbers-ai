#!/usr/bin/env python3
"""
既存のkeisen_master.jsonの4桁以上のパターンで、4位以降を含む理由を詳しく調査
同率の扱いを確認
"""

import json
import pandas as pd
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# データを読み込む
df = pd.read_csv(DATA_DIR / "past_results.csv", na_values=['NULL', 'null', ''])
df_old = df[(df['round_number'] >= 1340) & (df['round_number'] <= 6391)].copy()
df_old['n3_winning'] = df_old['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df_old['n3_winning'] = df_old['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'nan' else x)
df_old = df_old[df_old['n3_winning'].astype(str).str.len() == 3]
df_old = df_old.sort_values('round_number')
df_old['prev_n3'] = df_old['n3_winning'].shift(1)
df_old['prev2_n3'] = df_old['n3_winning'].shift(2)
df_old = df_old.dropna(subset=['prev_n3', 'prev2_n3'])

# keisen_master.jsonを読み込む
with open(DATA_DIR / "keisen_master.json", 'r', encoding='utf-8') as f:
    keisen_old = json.load(f)

print('=' * 60)
print('既存のkeisen_master.jsonの4桁以上のパターン詳細分析')
print('=' * 60)
print()

# 4桁以上のパターンを詳しく分析
four_or_more_examples = []

for n_type in ['n3']:
    for column in keisen_old[n_type].keys():
        for prev2 in keisen_old[n_type][column].keys():
            for prev in keisen_old[n_type][column][prev2].keys():
                predictions = keisen_old[n_type][column][prev2][prev]
                
                if len(predictions) < 4:
                    continue
                
                # 該当パターンのデータを抽出
                column_index = {'百の位': 0, '十の位': 1, '一の位': 2}[column]
                pattern_data = []
                for _, row in df_old.iterrows():
                    prev2_str = str(row['prev2_n3'])
                    prev_str = str(row['prev_n3'])
                    winning_str = str(row['n3_winning'])
                    
                    if pd.isna(row['prev2_n3']) or pd.isna(row['prev_n3']) or pd.isna(row['n3_winning']):
                        continue
                    
                    if len(prev2_str) < column_index + 1 or len(prev_str) < column_index + 1 or len(winning_str) < column_index + 1:
                        continue
                    
                    try:
                        prev2_digit = int(prev2_str[column_index])
                        prev_digit = int(prev_str[column_index])
                        winning_digit = int(winning_str[column_index])
                        
                        if prev2_digit == int(prev2) and prev_digit == int(prev):
                            pattern_data.append(winning_digit)
                    except (ValueError, IndexError):
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
                
                # 予測出目に含まれる4位以降の数字
                predictions_set = set(predictions)
                top3_set = set(top3_digits)
                fourth_or_later_in_predictions = [d for d in predictions if d not in top3_set]
                
                # 4位以降の数字の出現回数
                fourth_or_later_counts = [(d, digit_counts.get(d, 0)) for d in fourth_or_later_in_predictions]
                
                # 上位3位の最小出現回数と4位以降の最大出現回数を比較
                rule1_satisfied = top3_min_count > remaining_max_count
                rule1_equal = top3_min_count == remaining_max_count
                
                four_or_more_examples.append({
                    'n_type': n_type,
                    'column': column,
                    'prev2': int(prev2),
                    'prev': int(prev),
                    'predictions': predictions,
                    'digit_count': len(predictions),
                    'sample_size': len(pattern_data),
                    'top3_digits': top3_digits,
                    'top3_counts': top3_counts,
                    'top3_min_count': top3_min_count,
                    'remaining_max_count': remaining_max_count,
                    'rule1_satisfied': rule1_satisfied,
                    'rule1_equal': rule1_equal,
                    'fourth_or_later_in_predictions': fourth_or_later_in_predictions,
                    'fourth_or_later_counts': fourth_or_later_counts,
                    'sorted_digits': sorted_digits
                })

print(f'4桁以上のパターン数: {len(four_or_more_examples)}')
print()

# ルール1を満たすが4位以降を含むパターン
rule1_satisfied_but_has_4th = [p for p in four_or_more_examples if p['rule1_satisfied'] and len(p['fourth_or_later_in_predictions']) > 0]

print(f'ルール1を満たす（上位3位の最小 > 4位以降の最大）が4位以降を含む: {len(rule1_satisfied_but_has_4th)}パターン')
print()

if len(rule1_satisfied_but_has_4th) > 0:
    print('例（ルール1を満たすが4位以降を含む）:')
    for i, p in enumerate(rule1_satisfied_but_has_4th[:5], 1):
        print(f'例{i}: {p["n_type"].upper()} {p["column"]} - 前々回={p["prev2"]}, 前回={p["prev"]}')
        print(f'  予測出目 ({p["digit_count"]}桁): {p["predictions"]}')
        print(f'  上位3位: {p["top3_digits"]} (出現回数: {p["top3_counts"]})')
        print(f'  上位3位の最小出現回数: {p["top3_min_count"]}回')
        print(f'  4位以降の最大出現回数: {p["remaining_max_count"]}回')
        print(f'  ルール1: {p["top3_min_count"]} > {p["remaining_max_count"]}: ✅')
        print(f'  予測出目に含まれる4位以降の数字: {p["fourth_or_later_in_predictions"]}')
        print(f'  4位以降の数字の出現回数: {p["fourth_or_later_counts"]}')
        print()
        print('  実データの出現回数（全数字）:')
        for digit, count in p['sorted_digits']:
            mark = "✅" if digit in p['predictions'] else "❌"
            rank = "1-3位" if digit in p['top3_digits'] else "4位以降"
            print(f'    数字{digit}: {count}回 {mark} ({rank})')
        print()
        print('-' * 60)
        print()

# ルール1が同率の場合
rule1_equal_cases = [p for p in four_or_more_examples if p['rule1_equal']]

print(f'ルール1が同率（上位3位の最小 = 4位以降の最大）: {len(rule1_equal_cases)}パターン')
print()

if len(rule1_equal_cases) > 0:
    print('例（ルール1が同率）:')
    for i, p in enumerate(rule1_equal_cases[:5], 1):
        print(f'例{i}: {p["n_type"].upper()} {p["column"]} - 前々回={p["prev2"]}, 前回={p["prev"]}')
        print(f'  予測出目 ({p["digit_count"]}桁): {p["predictions"]}')
        print(f'  上位3位: {p["top3_digits"]} (出現回数: {p["top3_counts"]})')
        print(f'  上位3位の最小出現回数: {p["top3_min_count"]}回')
        print(f'  4位以降の最大出現回数: {p["remaining_max_count"]}回')
        print(f'  ルール1: {p["top3_min_count"]} = {p["remaining_max_count"]}: 同率')
        print(f'  予測出目に含まれる4位以降の数字: {p["fourth_or_later_in_predictions"]}')
        print(f'  4位以降の数字の出現回数: {p["fourth_or_later_counts"]}')
        print()
        print('  実データの出現回数（全数字）:')
        for digit, count in p['sorted_digits']:
            mark = "✅" if digit in p['predictions'] else "❌"
            rank = "1-3位" if digit in p['top3_digits'] else "4位以降"
            print(f'    数字{digit}: {count}回 {mark} ({rank})')
        print()
        print('-' * 60)
        print()

