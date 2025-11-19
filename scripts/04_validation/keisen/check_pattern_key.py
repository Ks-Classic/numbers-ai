#!/usr/bin/env python3
"""
検証ロジックの詳細確認 - pattern_keyの生成を確認
"""

import pandas as pd
from collections import defaultdict

# データ読み込み
df = pd.read_csv('data/past_results.csv', na_values=['NULL', 'null', ''])
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

print('=' * 60)
print('pattern_keyの生成を確認')
print('=' * 60)

# 前々回=0、前回=1のパターンを抽出
pattern_data = []
for idx, row in df.iterrows():
    prev2_digit = int(str(row['prev2_n3'])[0])  # 百の位
    prev_digit = int(str(row['prev_n3'])[0])    # 百の位
    winning_digit = int(str(row['n3_winning'])[0])  # 百の位
    
    if prev2_digit == 0 and prev_digit == 1:
        pattern_data.append({
            'round': row['round_number'],
            'prev2_n3': row['prev2_n3'],
            'prev_n3': row['prev_n3'],
            'n3_winning': row['n3_winning'],
            'prev2_digit': prev2_digit,
            'prev_digit': prev_digit,
            'winning_digit': winning_digit
        })

print(f'前々回=0、前回=1のパターンのデータ数: {len(pattern_data)}件')
print()

# count_pattern_frequency関数と同じロジックでpattern_keyを生成
pattern_counts = defaultdict(int)
digit_counts = defaultdict(lambda: defaultdict(int))

for _, row in df.iterrows():
    prev = row['prev_n3']  # 前回
    prev2 = row['prev2_n3']  # 前々回
    winning = row['n3_winning']
    
    # 各桁を抽出
    prev_digits = [int(str(prev)[i]) for i in range(3)]
    prev2_digits = [int(str(prev2)[i]) for i in range(3)]
    winning_digits = [int(str(winning)[i]) for i in range(3)]
    
    # 百の位のみ処理
    i = 0  # 百の位
    column = "百の位"
    prev_digit = str(prev_digits[i])  # 前回の百の位
    prev2_digit = str(prev2_digits[i])  # 前々回の百の位
    winning_digit = winning_digits[i]
    
    # pattern_keyを生成
    pattern_key = (column, prev_digit, prev2_digit)
    
    # 前々回=0、前回=1のパターンのみカウント
    if prev2_digit == '0' and prev_digit == '1':
        pattern_counts[pattern_key] += 1
        digit_counts[pattern_key][winning_digit] += 1

print('count_pattern_frequency関数で生成されたpattern_key:')
for key, count in pattern_counts.items():
    print(f'  pattern_key: {key} (column={key[0]}, prev={key[1]}, prev2={key[2]})')
    print(f'  サンプル数: {count}')
    print(f'  各数字の出現回数:')
    for digit in sorted(digit_counts[key].keys()):
        print(f'    数字{digit}: {digit_counts[key][digit]}回')
    print()

print('=' * 60)
print('検証ロジックの確認')
print('=' * 60)
print('pattern_key = (column, prev_digit, prev2_digit)')
print('  prev_digit: 前回の該当桁')
print('  prev2_digit: 前々回の該当桁')
print()
print('つまり、前々回=0、前回=1のパターンは:')
print('  pattern_key = ("百の位", "1", "0")')
print('  → (column, 前回=1, 前々回=0)')
print()
print('しかし、keisen_master.jsonの構造は:')
print('  keisen["n3"]["百の位"][前回][前々回]')
print('  前回=1、前々回=0のパターンは:')
print('    keisen["n3"]["百の位"]["1"]["0"]')
print()
print('検証スクリプトでは:')
print('  pattern_key = (column, prev_str, prev2_str)')
print('  prev_str: 前回')
print('  prev2_str: 前々回')
print('  前回=1、前々回=0のパターンは:')
print('    pattern_key = ("百の位", "1", "0")')
print()
print('→ これは一致しているはずですが、実際の検証結果と異なります')

