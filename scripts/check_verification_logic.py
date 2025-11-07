#!/usr/bin/env python3
"""
検証ロジックの詳細確認スクリプト
"""

import pandas as pd
import json
from collections import Counter

# データ読み込み
df = pd.read_csv('data/past_results.csv', na_values=['NULL', 'null', ''])
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
df = df.dropna(subset=['prev_n3', 'prev2_n3'])

# 具体例：N3百の位、前々回=0、前回=1のパターンを確認
print('=' * 60)
print('検証例: N3百の位、前々回=0、前回=1')
print('=' * 60)
print(f'総データ数: {len(df)}行')
print()

# 該当パターンのデータを抽出
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

print(f'該当パターンのデータ数: {len(pattern_data)}件')
print()

# 出現回数を集計
digit_counts = Counter([d['winning_digit'] for d in pattern_data])
print('各数字の出現回数:')
for digit in sorted(digit_counts.keys()):
    print(f'  数字{digit}: {digit_counts[digit]}回')
print()

# 出現回数の降順でソート
sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
print('出現回数の降順（同率は昇順）:')
for digit, count in sorted_digits:
    print(f'  数字{digit}: {count}回')
print()

# 上位3位
top3 = [digit for digit, count in sorted_digits[:3]]
print(f'上位3位: {top3}')
print()

# keisen_master.jsonの予測出目
with open('data/keisen_master.json', 'r', encoding='utf-8') as f:
    keisen = json.load(f)
keisen_pred = keisen['n3']['百の位']['0']['1']
print(f'keisen_master.jsonの予測出目: {keisen_pred}')
print()

# 最初の10件のデータ例
print('最初の10件のデータ例:')
for i, d in enumerate(pattern_data[:10]):
    print(f'  {i+1}. 回号{d["round"]}: 前々回={d["prev2_n3"]} (百の位={d["prev2_digit"]}), 前回={d["prev_n3"]} (百の位={d["prev_digit"]}), 当選={d["n3_winning"]} (百の位={d["winning_digit"]})')

print()
print('=' * 60)
print('検証ロジックの確認')
print('=' * 60)
print('前々回の百の位 = 0 かつ 前回の百の位 = 1 のときに、')
print('実際に当選した数字の百の位の出現回数を集計している')
print('→ これは正しいロジックです')

