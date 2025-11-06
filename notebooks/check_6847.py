#!/usr/bin/env python3
import pandas as pd
import re

df = pd.read_csv('data/past_results.csv')
row_6847 = df[df['round_number'] == 6847]

print('6847回の生データ:')
print(row_6847[['round_number', 'draw_date', 'n3_winning', 'n4_winning']])

# 文字列型に変換
n3_val = str(row_6847.iloc[0]['n3_winning']).replace('.0', '')
n4_val = str(row_6847.iloc[0]['n4_winning']).replace('.0', '')

print(f'\nn3_winning変換後: {repr(n3_val)}')
print(f'n4_winning変換後: {repr(n4_val)}')

# 正規表現チェック
n3_match = re.match(r'^\d{3}$', n3_val)
n4_match = re.match(r'^\d{4}$', n4_val)

print(f'\nn3_winning正規表現マッチ: {n3_match is not None}')
print(f'n4_winning正規表現マッチ: {n4_match is not None}')

if n4_match is None:
    print(f'\n問題: n4_winningが4桁の正規表現にマッチしません')
    print(f'  値: {repr(n4_val)}')
    print(f'  長さ: {len(n4_val)}')
    print(f'  文字コード: {[ord(c) for c in n4_val]}')

