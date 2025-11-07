#!/usr/bin/env python3
import pandas as pd

df_all = pd.read_csv('data/past_results.csv')
df_all = df_all.sort_values('round_number', ascending=False).reset_index(drop=True)

# データクリーニングを再現
df_all['n3_winning'] = df_all['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df_all['n4_winning'] = df_all['n4_winning'].astype(str).str.replace('.0', '', regex=False)

required_columns = ['round_number', 'draw_date', 'n3_winning', 'n4_winning']
df_clean = df_all.dropna(subset=required_columns)
df_clean = df_clean[df_clean['round_number'].between(1, 9999)]
df_clean = df_clean[df_clean['n3_winning'].str.match(r'^\d{3}$', na=False)]
df_clean = df_clean[df_clean['n4_winning'].str.match(r'^\d{4}$', na=False)]
df_clean = df_clean.sort_values('round_number', ascending=False).reset_index(drop=True)

# 6847回を確認
row_6847 = df_clean[df_clean['round_number'] == 6847]
print('6847回のデータ（クリーニング後）:')
if len(row_6847) > 0:
    print(row_6847[['round_number', 'draw_date', 'n3_winning', 'n4_winning']])
    print(f'n3_winning型: {type(row_6847.iloc[0]["n3_winning"])}')
    print(f'n3_winning値: {repr(row_6847.iloc[0]["n3_winning"])}')
    print(f'n4_winning値: {repr(row_6847.iloc[0]["n4_winning"])}')
else:
    print('6847回がクリーニング後に除外されました')

# 学習データの範囲を確認
BASE_ROUND = df_clean['round_number'].max()
base_idx = df_clean[df_clean['round_number'] == BASE_ROUND].index[0]
TRAIN_SIZE = 1000
train_df = df_clean.iloc[base_idx:base_idx+TRAIN_SIZE].copy()

print(f'\n学習データの範囲: {train_df["round_number"].min()} 〜 {train_df["round_number"].max()}')
print(f'6847回の存在: {6847 in train_df["round_number"].values}')

# データクリーニング前後の数を比較
print(f'\nクリーニング前: {len(df_all)}行')
print(f'クリーニング後: {len(df_clean)}行')
print(f'除外された行数: {len(df_all) - len(df_clean)}行')

