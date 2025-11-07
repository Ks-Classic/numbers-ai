#!/usr/bin/env python3
"""
データ範囲の確認スクリプト
最新版から4801回までのデータと、1000回分のデータを比較します。
"""
import pandas as pd

# データ読み込み
df_all = pd.read_csv('data/past_results.csv')
df_all = df_all.sort_values('round_number', ascending=False).reset_index(drop=True)

# データクリーニング
df_all['n3_winning'] = df_all['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df_all['n4_winning'] = df_all['n4_winning'].astype(str).str.replace('.0', '', regex=False)

required_columns = ['round_number', 'draw_date', 'n3_winning', 'n4_winning']
df_clean = df_all.dropna(subset=required_columns)
df_clean = df_clean[df_clean['round_number'].between(1, 9999)]
df_clean = df_clean[df_clean['n3_winning'].str.match(r'^\d{3}$', na=False)]
df_clean = df_clean[df_clean['n4_winning'].str.match(r'^\d{4}$', na=False)]
df_clean = df_clean.sort_values('round_number', ascending=False).reset_index(drop=True)

# 最新回号を取得
BASE_ROUND = df_clean['round_number'].max()
print(f'📊 データ確認結果\n')
print(f'最新回号: 第{BASE_ROUND}回')
print(f'全データ件数（クリーニング後）: {len(df_clean):,}件')
print(f'データ範囲: 第{df_clean["round_number"].min()}回 〜 第{df_clean["round_number"].max()}回\n')

# 選択肢1: 1000回分（5849〜6849）
print('=' * 60)
print('選択肢1: 1000回分（直近1000回）')
print('=' * 60)
base_idx = df_clean[df_clean['round_number'] == BASE_ROUND].index[0]
df_1000 = df_clean.iloc[base_idx:base_idx+1000].copy()
print(f'回号範囲: 第{df_1000["round_number"].min()}回 〜 第{df_1000["round_number"].max()}回')
print(f'データ件数: {len(df_1000):,}件')

# リハーサル数字があるデータの確認
rehearsal_1000 = df_1000[(df_1000['n3_rehearsal'].notna())
                         & (df_1000['n4_rehearsal'].notna())
                         & (df_1000['n3_rehearsal'] != 'NULL')
                         & (df_1000['n4_rehearsal'] != 'NULL')]
print(f'リハーサル数字あり: {len(rehearsal_1000):,}件 ({len(rehearsal_1000)/len(df_1000)*100:.1f}%)')
print(f'リハーサル数字なし: {len(df_1000) - len(rehearsal_1000):,}件')

# 選択肢2: 最新版から4801回まで（リハーサル数字がある範囲）
print('\n' + '=' * 60)
print('選択肢2: 最新版から4801回まで（リハーサル数字がある範囲）')
print('=' * 60)
df_4801 = df_clean[df_clean['round_number'] >= 4801].copy()
print(f'回号範囲: 第{df_4801["round_number"].min()}回 〜 第{df_4801["round_number"].max()}回')
print(f'データ件数: {len(df_4801):,}件')

# リハーサル数字があるデータの確認
rehearsal_4801 = df_4801[(df_4801['n3_rehearsal'].notna())
                         & (df_4801['n4_rehearsal'].notna())
                         & (df_4801['n3_rehearsal'] != 'NULL')
                         & (df_4801['n4_rehearsal'] != 'NULL')]
print(f'リハーサル数字あり: {len(rehearsal_4801):,}件 ({len(rehearsal_4801)/len(df_4801)*100:.1f}%)')
print(f'リハーサル数字なし: {len(df_4801) - len(rehearsal_4801):,}件')

# 比較
print('\n' + '=' * 60)
print('比較')
print('=' * 60)
print(f'データ件数の差: {len(df_4801) - len(df_1000):,}件（選択肢2の方が{len(df_4801) - len(df_1000):,}件多い）')
print(f'リハーサル数字ありデータの差: {len(rehearsal_4801) - len(rehearsal_1000):,}件')

# 4801回のデータ確認
print('\n' + '=' * 60)
print('4801回のデータ確認')
print('=' * 60)
row_4801 = df_clean[df_clean['round_number'] == 4801]
if len(row_4801) > 0:
    print(row_4801[['round_number', 'draw_date', 'n3_winning', 'n4_winning', 'n3_rehearsal', 'n4_rehearsal']])
else:
    print('4801回のデータが見つかりませんでした')

# 4800回のデータ確認（リハーサル数字があるかどうか）
row_4800 = df_clean[df_clean['round_number'] == 4800]
if len(row_4800) > 0:
    print('\n4800回のデータ確認:')
    print(row_4800[['round_number', 'draw_date', 'n3_winning', 'n4_winning', 'n3_rehearsal', 'n4_rehearsal']])
