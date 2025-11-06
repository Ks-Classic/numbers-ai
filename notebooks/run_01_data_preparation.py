#!/usr/bin/env python3
"""
データ前処理スクリプト（01_data_preparation.ipynbの実行版）

このスクリプトは、01_data_preparation.ipynbの内容を実行します。
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# 設定ファイルをインポート
import sys
PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
sys.path.append(str(PROJECT_ROOT / 'notebooks'))
from config import TRAIN_SIZE, BASE_ROUND_AUTO, BASE_ROUND, MIN_ROUND, TRAIN_DATA_CSV

# プロジェクトルートのパスを設定
DATA_DIR = PROJECT_ROOT / 'data'

print(f"プロジェクトルート: {PROJECT_ROOT}")
print(f"データディレクトリ: {DATA_DIR}")
print(f"\n学習設定:")
if TRAIN_SIZE is not None:
    print(f"  学習範囲: {TRAIN_SIZE}回分")
elif MIN_ROUND is not None:
    print(f"  最小回号: {MIN_ROUND}回から最新回まで")
else:
    print(f"  学習範囲: 全データ")
print(f"  基準回号自動取得: {BASE_ROUND_AUTO}")

# CSVデータの読み込み
csv_path = DATA_DIR / 'past_results.csv'

if not csv_path.exists():
    raise FileNotFoundError(f"データファイルが見つかりません: {csv_path}")

df = pd.read_csv(csv_path)

# 当選番号を文字列型に変換（数値型で読み込まれる可能性があるため）
df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
df['n4_winning'] = df['n4_winning'].astype(str).str.replace('.0', '', regex=False)

# 先頭0を補完（数値型として読み込まれた場合、先頭0が失われるため）
df['n3_winning'] = df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' else x)
df['n4_winning'] = df['n4_winning'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' else x)

# リハーサル数字を文字列型に変換（数値型で読み込まれる可能性があるため）
# NULL値の場合はそのまま維持（NaNは文字列変換時にも保持される）
if 'n3_rehearsal' in df.columns:
    df['n3_rehearsal'] = df['n3_rehearsal'].astype(str).str.replace('.0', '', regex=False)
    # NULL値やNaNの場合はそのまま、有効な値の場合のみ先頭0を補完
    df['n3_rehearsal'] = df['n3_rehearsal'].apply(
        lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' and str(x) != 'nan' and str(x) != '' else x
    )
    # 'nan'文字列をNaNに戻す（NULL値として扱う）
    df['n3_rehearsal'] = df['n3_rehearsal'].replace('nan', pd.NA).replace('NULL', pd.NA).replace('', pd.NA)

if 'n4_rehearsal' in df.columns:
    df['n4_rehearsal'] = df['n4_rehearsal'].astype(str).str.replace('.0', '', regex=False)
    # NULL値やNaNの場合はそのまま、有効な値の場合のみ先頭0を補完
    df['n4_rehearsal'] = df['n4_rehearsal'].apply(
        lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' and str(x) != 'nan' and str(x) != '' else x
    )
    # 'nan'文字列をNaNに戻す（NULL値として扱う）
    df['n4_rehearsal'] = df['n4_rehearsal'].replace('nan', pd.NA).replace('NULL', pd.NA).replace('', pd.NA)

print(f"\nデータ行数: {len(df)}")
print(f"回号の範囲: {df['round_number'].min()} 〜 {df['round_number'].max()}")
if 'n3_rehearsal' in df.columns:
    print(f"N3リハーサル: {df['n3_rehearsal'].notna().sum()}件 / {len(df)}件")
if 'n4_rehearsal' in df.columns:
    print(f"N4リハーサル: {df['n4_rehearsal'].notna().sum()}件 / {len(df)}件")

# データクリーニング
required_columns = ['round_number', 'draw_date', 'n3_winning', 'n4_winning']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise ValueError(f"必須カラムが見つかりません: {missing_columns}")

df = df.dropna(subset=required_columns)
df = df[df['round_number'].between(1, 9999)]
df = df[df['n3_winning'].str.match(r'^\d{3}$', na=False)]
df = df[df['n4_winning'].str.match(r'^\d{4}$', na=False)]
df = df.sort_values('round_number', ascending=False).reset_index(drop=True)

print(f"クリーニング後のデータ行数: {len(df)}")

# 基準回号の確認
if BASE_ROUND_AUTO:
    BASE_ROUND = df['round_number'].max()
else:
    if BASE_ROUND is None:
        raise ValueError("BASE_ROUND_AUTOがFalseの場合、BASE_ROUNDを設定してください")

base_row = df[df['round_number'] == BASE_ROUND]
if len(base_row) == 0:
    raise ValueError(f"基準回号 {BASE_ROUND} が見つかりません")

BASE_DATE = base_row.iloc[0]['draw_date']

print(f"\n基準回号: {BASE_ROUND}")
print(f"基準日: {BASE_DATE}")

# 学習用データセットの準備
base_idx = df[df['round_number'] == BASE_ROUND].index[0]

if TRAIN_SIZE is not None:
    # TRAIN_SIZEが指定されている場合: 基準回号からTRAIN_SIZE回分
    train_df = df.iloc[base_idx:base_idx+TRAIN_SIZE].copy()
elif MIN_ROUND is not None:
    # MIN_ROUNDが指定されている場合: MIN_ROUNDから基準回号まで
    min_idx_list = df[df['round_number'] == MIN_ROUND].index
    if len(min_idx_list) == 0:
        raise ValueError(f"最小回号 {MIN_ROUND} が見つかりません")
    min_idx = min_idx_list[0]
    # dfは降順でソートされているため、base_idx（最大回号）はインデックス0付近、min_idx（最小回号）は後ろの方
    # そのため、base_idxからmin_idx+1までの範囲を取得する必要がある
    if base_idx < min_idx:
        train_df = df.iloc[base_idx:min_idx+1].copy()
    else:
        # 念のため、逆の場合も対応（この場合は通常発生しない）
        train_df = df.iloc[min_idx:base_idx+1].copy()
else:
    # 両方Noneの場合: 全データ
    train_df = df.iloc[:base_idx+1].copy()

train_df = train_df.sort_values('round_number', ascending=True).reset_index(drop=True)

print(f"\n学習用データセット: {len(train_df)}回分")
print(f"回号範囲: {train_df['round_number'].min()} 〜 {train_df['round_number'].max()}")

# データセットの保存
# CSV保存前に、リハーサル数字のNaN値を空文字列に置き換え、小数点を削除
train_df_save = train_df.copy()
if 'n3_rehearsal' in train_df_save.columns:
    # NaN値を空文字列に置き換え
    train_df_save['n3_rehearsal'] = train_df_save['n3_rehearsal'].fillna('')
    # 文字列型に変換して小数点を削除
    train_df_save['n3_rehearsal'] = train_df_save['n3_rehearsal'].astype(str).str.replace('.0', '', regex=False)
    # 'nan'文字列を空文字列に置き換え
    train_df_save['n3_rehearsal'] = train_df_save['n3_rehearsal'].replace('nan', '')

if 'n4_rehearsal' in train_df_save.columns:
    # NaN値を空文字列に置き換え
    train_df_save['n4_rehearsal'] = train_df_save['n4_rehearsal'].fillna('')
    # 文字列型に変換して小数点を削除
    train_df_save['n4_rehearsal'] = train_df_save['n4_rehearsal'].astype(str).str.replace('.0', '', regex=False)
    # 'nan'文字列を空文字列に置き換え
    train_df_save['n4_rehearsal'] = train_df_save['n4_rehearsal'].replace('nan', '')

# CSV保存（NaN値は空文字列として保存）
train_csv_path = DATA_DIR / TRAIN_DATA_CSV
train_df_save.to_csv(train_csv_path, index=False, na_rep='')
print(f"\n学習用データセットを保存しました: {train_csv_path}")
print(f"ファイルサイズ: {train_csv_path.stat().st_size / 1024:.2f} KB")

# 保存されたデータの確認（小数点が付いていないか確認）
saved_df = pd.read_csv(train_csv_path)
if 'n3_rehearsal' in saved_df.columns:
    sample_rows = saved_df[saved_df['n3_rehearsal'].notna() & (saved_df['n3_rehearsal'] != '')]
    if len(sample_rows) > 0:
        sample_rehearsal = sample_rows['n3_rehearsal'].iloc[0]
        print(f"\n保存後のN3リハーサル数字サンプル: {sample_rehearsal}")
        print(f"  型: {type(sample_rehearsal)}")
        if '.' in str(sample_rehearsal):
            print(f"  ⚠️ 警告: 小数点が含まれています！")

print("\n✓ データ前処理が完了しました")

