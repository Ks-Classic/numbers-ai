#!/usr/bin/env python3
"""
既存のkeisen_master.jsonの予測出目が4桁以上のパターンを分析
それらの選定ルールを特定する
"""

import json
import pandas as pd
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# keisen_master.jsonを読み込む
with open(DATA_DIR / "keisen_master.json", 'r', encoding='utf-8') as f:
    keisen = json.load(f)

# 予測出目が4桁以上のパターンを探す
long_predictions = []
for n_type in ['n3', 'n4']:
    for column in keisen[n_type].keys():
        for prev2 in keisen[n_type][column].keys():
            for prev in keisen[n_type][column][prev2].keys():
                predictions = keisen[n_type][column][prev2][prev]
                if len(predictions) >= 4:
                    long_predictions.append({
                        'n_type': n_type,
                        'column': column,
                        'prev2': prev2,
                        'prev': prev,
                        'predictions': predictions,
                        'count': len(predictions)
                    })

print(f'予測出目が4桁以上のパターン数: {len(long_predictions)}')
print()

# データを読み込んで、これらのパターンがどのようなルールで選ばれているか分析
df = pd.read_csv(DATA_DIR / "past_results.csv", na_values=['NULL', 'null', ''])
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
df['prev_n4'] = df['n4_winning'].shift(1)
df['prev2_n4'] = df['n4_winning'].shift(2)
df = df.dropna(subset=['prev_n3', 'prev2_n3', 'prev_n4', 'prev2_n4'])

print('=' * 60)
print('予測出目が4桁以上のパターンの分析')
print('=' * 60)
print()

# 各パターンについて、実データでの出現回数を確認
analysis_results = []

for item in sorted(long_predictions, key=lambda x: x['count'], reverse=True):
    n_type = item['n_type']
    column = item['column']
    prev2 = int(item['prev2'])
    prev = int(item['prev'])
    predictions = item['predictions']
    
    # 該当パターンのデータを抽出
    if n_type == 'n3':
        prev_col = 'prev_n3'
        prev2_col = 'prev2_n3'
        winning_col = 'n3_winning'
        column_index = {'百の位': 0, '十の位': 1, '一の位': 2}[column]
    else:
        prev_col = 'prev_n4'
        prev2_col = 'prev2_n4'
        winning_col = 'n4_winning'
        column_index = {'千の位': 0, '百の位': 1, '十の位': 2, '一の位': 3}[column]
    
    pattern_data = []
    for _, row in df.iterrows():
        prev2_digit = int(str(row[prev2_col])[column_index])
        prev_digit = int(str(row[prev_col])[column_index])
        winning_digit = int(str(row[winning_col])[column_index])
        
        if prev2_digit == prev2 and prev_digit == prev:
            pattern_data.append(winning_digit)
    
    if len(pattern_data) == 0:
        continue
    
    # 出現回数を集計
    digit_counts = Counter(pattern_data)
    
    # 出現回数の降順でソート
    sorted_digits = sorted(digit_counts.items(), key=lambda x: (-x[1], x[0]))
    
    # 予測出目の数字の出現回数を取得
    prediction_counts = [digit_counts.get(d, 0) for d in predictions]
    
    # 実データの上位N位（N=予測出目の数）を取得
    actual_top_n = [d for d, _ in sorted_digits[:len(predictions)]]
    
    # 予測出目が実データの上位N位に含まれているか確認
    all_in_top_n = all(d in actual_top_n for d in predictions)
    
    # 最小出現回数と最大出現回数を計算
    min_count = min(prediction_counts) if prediction_counts else 0
    max_count = max(prediction_counts) if prediction_counts else 0
    
    # 予測出目に含まれていない数字の最大出現回数
    excluded_digits = [d for d, _ in sorted_digits if d not in predictions]
    max_excluded_count = max([digit_counts.get(d, 0) for d in excluded_digits]) if excluded_digits else 0
    
    analysis_results.append({
        'n_type': n_type,
        'column': column,
        'prev2': prev2,
        'prev': prev,
        'predictions': predictions,
        'prediction_count': len(predictions),
        'sample_size': len(pattern_data),
        'prediction_counts': prediction_counts,
        'min_count': min_count,
        'max_count': max_count,
        'max_excluded_count': max_excluded_count,
        'all_in_top_n': all_in_top_n,
        'actual_top_n': actual_top_n
    })

# 分析結果を表示
print(f'分析対象パターン数: {len(analysis_results)}')
print()

# 統計を計算
all_in_top_n_count = sum(1 for r in analysis_results if r['all_in_top_n'])
print(f'予測出目が実データの上位N位に全て含まれている: {all_in_top_n_count}/{len(analysis_results)} ({all_in_top_n_count/len(analysis_results)*100:.1f}%)')
print()

# 予測出目の最小出現回数と除外された数字の最大出現回数の関係を分析
print('=' * 60)
print('選定ルールの分析')
print('=' * 60)
print()

# 予測出目の最小出現回数 >= 除外された数字の最大出現回数 のパターン
rule1_count = sum(1 for r in analysis_results if r['min_count'] >= r['max_excluded_count'])
print(f'ルール候補1: 予測出目の最小出現回数 >= 除外された数字の最大出現回数')
print(f'  該当パターン数: {rule1_count}/{len(analysis_results)} ({rule1_count/len(analysis_results)*100:.1f}%)')
print()

# 予測出目の最小出現回数 > 除外された数字の最大出現回数 のパターン
rule2_count = sum(1 for r in analysis_results if r['min_count'] > r['max_excluded_count'])
print(f'ルール候補2: 予測出目の最小出現回数 > 除外された数字の最大出現回数')
print(f'  該当パターン数: {rule2_count}/{len(analysis_results)} ({rule2_count/len(analysis_results)*100:.1f}%)')
print()

# 予測出目が実データの上位N位に全て含まれているパターン
print(f'ルール候補3: 予測出目が実データの上位N位（N=予測出目の数）に全て含まれている')
print(f'  該当パターン数: {all_in_top_n_count}/{len(analysis_results)} ({all_in_top_n_count/len(analysis_results)*100:.1f}%)')
print()

# 具体例を表示
print('=' * 60)
print('具体例（上位10件）')
print('=' * 60)
print()

for i, result in enumerate(sorted(analysis_results, key=lambda x: x['prediction_count'], reverse=True)[:10], 1):
    print(f'例{i}: {result["n_type"].upper()} {result["column"]} - 前々回={result["prev2"]}, 前回={result["prev"]}')
    print(f'  予測出目 ({result["prediction_count"]}桁): {result["predictions"]}')
    print(f'  サンプル数: {result["sample_size"]}回')
    print(f'  予測出目の出現回数: {result["prediction_counts"]}')
    print(f'  最小出現回数: {result["min_count"]}回')
    print(f'  最大出現回数: {result["max_count"]}回')
    print(f'  除外された数字の最大出現回数: {result["max_excluded_count"]}回')
    print(f'  実データの上位{result["prediction_count"]}位: {result["actual_top_n"]}')
    print(f'  全て上位N位に含まれている: {"✅" if result["all_in_top_n"] else "❌"}')
    print(f'  最小出現回数 >= 除外最大出現回数: {"✅" if result["min_count"] >= result["max_excluded_count"] else "❌"}')
    print()
    print('-' * 60)
    print()

