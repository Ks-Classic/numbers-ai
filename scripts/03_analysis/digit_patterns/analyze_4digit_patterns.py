#!/usr/bin/env python3
"""
既存のkeisen_master.jsonと新規のkeisen_master_new.jsonの4桁以上のパターンを調査
上位3位のみ（同率含む）になっているか確認
"""

import json
import pandas as pd
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# データを読み込む
df = pd.read_csv(DATA_DIR / "past_results.csv", na_values=['NULL', 'null', ''])

# 既存データ用
df_old = df[(df['round_number'] >= 1340) & (df['round_number'] <= 6391)].copy()
df_old['n3_winning'] = df_old['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df_old['n3_winning'] = df_old['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'nan' else x)
df_old = df_old[df_old['n3_winning'].astype(str).str.len() == 3]
df_old = df_old.sort_values('round_number')
df_old['prev_n3'] = df_old['n3_winning'].shift(1)
df_old['prev2_n3'] = df_old['n3_winning'].shift(2)
df_old = df_old.dropna(subset=['prev_n3', 'prev2_n3'])

# 新規データ用
df_new = df[(df['round_number'] >= 4801) & (df['round_number'] <= 6850)].copy()
df_new['n3_winning'] = df_new['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df_new['n3_winning'] = df_new['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'nan' else x)
df_new = df_new[df_new['n3_winning'].astype(str).str.len() == 3]
df_new = df_new.sort_values('round_number')
df_new['prev_n3'] = df_new['n3_winning'].shift(1)
df_new['prev2_n3'] = df_new['n3_winning'].shift(2)
df_new = df_new.dropna(subset=['prev_n3', 'prev2_n3'])

# keisen_master.jsonを読み込む
with open(DATA_DIR / "keisen_master.json", 'r', encoding='utf-8') as f:
    keisen_old = json.load(f)

with open(DATA_DIR / "keisen_master_new.json", 'r', encoding='utf-8') as f:
    keisen_new = json.load(f)

def analyze_patterns(keisen_data, df_data, label):
    """パターンを分析"""
    four_or_more_patterns = []
    
    for n_type in ['n3', 'n4']:
        for column in keisen_data[n_type].keys():
            for prev2 in keisen_data[n_type][column].keys():
                for prev in keisen_data[n_type][column][prev2].keys():
                    predictions = keisen_data[n_type][column][prev2][prev]
                    
                    if len(predictions) < 4:
                        continue
                    
                    # 該当パターンのデータを抽出
                    if n_type == 'n3':
                        column_index = {'百の位': 0, '十の位': 1, '一の位': 2}[column]
                        pattern_data = []
                        for _, row in df_data.iterrows():
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
                    
                    # 予測出目が上位3位のみを含んでいるか確認
                    predictions_set = set(predictions)
                    top3_set = set(top3_digits)
                    
                    # 上位3位のみを含んでいるか（同率を含む）
                    is_top3_only = predictions_set.issubset(top3_set)
                    
                    # 上位3位を全て含んでいるか
                    contains_all_top3 = top3_set.issubset(predictions_set)
                    
                    # 4位以降を含んでいるか
                    contains_4th_or_later = len(predictions_set & set(remaining_digits)) > 0 if len(sorted_digits) > 3 else False
                    
                    four_or_more_patterns.append({
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
                        'is_top3_only': is_top3_only,
                        'contains_all_top3': contains_all_top3,
                        'contains_4th_or_later': contains_4th_or_later,
                        'sorted_digits': sorted_digits
                    })
    
    return four_or_more_patterns

print('=' * 60)
print('既存のkeisen_master.jsonの4桁以上のパターン分析')
print('=' * 60)
print()

old_4plus = analyze_patterns(keisen_old, df_old, '既存')

print(f'4桁以上のパターン数: {len(old_4plus)}')
print()

# 上位3位のみを含んでいるか
top3_only_count = sum(1 for p in old_4plus if p['is_top3_only'])
contains_4th_count = sum(1 for p in old_4plus if p['contains_4th_or_later'])

print(f'上位3位のみを含む（同率含む）: {top3_only_count}パターン ({top3_only_count/len(old_4plus)*100:.1f}%)')
print(f'4位以降を含む: {contains_4th_count}パターン ({contains_4th_count/len(old_4plus)*100:.1f}%)')
print()

# 4位以降を含むパターンの例
if contains_4th_count > 0:
    print('4位以降を含むパターンの例（上位5件）:')
    for i, p in enumerate([p for p in old_4plus if p['contains_4th_or_later']][:5], 1):
        print(f'例{i}: {p["n_type"].upper()} {p["column"]} - 前々回={p["prev2"]}, 前回={p["prev"]}')
        print(f'  予測出目 ({p["digit_count"]}桁): {p["predictions"]}')
        print(f'  上位3位: {p["top3_digits"]}')
        print()
        print('  実データの出現回数（上位5位）:')
        for digit, count in p['sorted_digits'][:5]:
            mark = "✅" if digit in p['predictions'] else "❌"
            print(f'    数字{digit}: {count}回 {mark}')
        print()
        print('-' * 60)
        print()

# 上位3位のみを含むが4桁以上のパターン（同率の場合）
top3_only_4plus = [p for p in old_4plus if p['is_top3_only'] and p['digit_count'] >= 4]

print(f'上位3位のみを含むが4桁以上のパターン（同率）: {len(top3_only_4plus)}パターン')
print()

if len(top3_only_4plus) > 0:
    print('同率の例（上位5件）:')
    for i, p in enumerate(top3_only_4plus[:5], 1):
        print(f'例{i}: {p["n_type"].upper()} {p["column"]} - 前々回={p["prev2"]}, 前回={p["prev"]}')
        print(f'  予測出目 ({p["digit_count"]}桁): {p["predictions"]}')
        print(f'  上位3位: {p["top3_digits"]}')
        print(f'  上位3位の出現回数: {p["top3_counts"]}')
        print()
        print('  実データの出現回数（全数字）:')
        for digit, count in p['sorted_digits']:
            mark = "✅" if digit in p['predictions'] else "❌"
            print(f'    数字{digit}: {count}回 {mark}')
        print()
        print('-' * 60)
        print()

print('=' * 60)
print('新規のkeisen_master_new.jsonの4桁以上のパターン分析')
print('=' * 60)
print()

new_4plus = analyze_patterns(keisen_new, df_new, '新規')

print(f'4桁以上のパターン数: {len(new_4plus)}')
print()

# 上位3位のみを含んでいるか
top3_only_count_new = sum(1 for p in new_4plus if p['is_top3_only'])
contains_4th_count_new = sum(1 for p in new_4plus if p['contains_4th_or_later'])

print(f'上位3位のみを含む（同率含む）: {top3_only_count_new}パターン ({top3_only_count_new/len(new_4plus)*100:.1f}%)')
print(f'4位以降を含む: {contains_4th_count_new}パターン ({contains_4th_count_new/len(new_4plus)*100:.1f}%)')
print()

# 4位以降を含むパターンの例
if contains_4th_count_new > 0:
    print('4位以降を含むパターンの例（上位5件）:')
    for i, p in enumerate([p for p in new_4plus if p['contains_4th_or_later']][:5], 1):
        print(f'例{i}: {p["n_type"].upper()} {p["column"]} - 前々回={p["prev2"]}, 前回={p["prev"]}')
        print(f'  予測出目 ({p["digit_count"]}桁): {p["predictions"]}')
        print(f'  上位3位: {p["top3_digits"]}')
        print()
        print('  実データの出現回数（上位5位）:')
        for digit, count in p['sorted_digits'][:5]:
            mark = "✅" if digit in p['predictions'] else "❌"
            print(f'    数字{digit}: {count}回 {mark}')
        print()
        print('-' * 60)
        print()

# 上位3位のみを含むが4桁以上のパターン（同率の場合）
top3_only_4plus_new = [p for p in new_4plus if p['is_top3_only'] and p['digit_count'] >= 4]

print(f'上位3位のみを含むが4桁以上のパターン（同率）: {len(top3_only_4plus_new)}パターン')
print()

if len(top3_only_4plus_new) > 0:
    print('同率の例（上位5件）:')
    for i, p in enumerate(top3_only_4plus_new[:5], 1):
        print(f'例{i}: {p["n_type"].upper()} {p["column"]} - 前々回={p["prev2"]}, 前回={p["prev"]}')
        print(f'  予測出目 ({p["digit_count"]}桁): {p["predictions"]}')
        print(f'  上位3位: {p["top3_digits"]}')
        print(f'  上位3位の出現回数: {p["top3_counts"]}')
        print()
        print('  実データの出現回数（全数字）:')
        for digit, count in p['sorted_digits']:
            mark = "✅" if digit in p['predictions'] else "❌"
            print(f'    数字{digit}: {count}回 {mark}')
        print()
        print('-' * 60)
        print()

