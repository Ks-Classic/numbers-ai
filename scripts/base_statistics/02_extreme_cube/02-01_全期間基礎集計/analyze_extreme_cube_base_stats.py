#!/usr/bin/env python3
"""
極CUBE全期間基礎集計スクリプト

最新回から500回分さかのぼって、極CUBE内での当選番号出現分析、
数字の出現パターン集計、時系列・周期性分析を実施する。
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Set
from datetime import datetime
from collections import defaultdict

import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'core'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'production'))

from chart_generator import load_keisen_master
from generate_extreme_cube import (
    generate_extreme_cube,
    load_past_results,
    validate_round_number
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 出力ディレクトリ
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'analysis_results' / '02_extreme_cube' / '02-01_全期間基礎集計'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_winning_digits(winning_str: str) -> Optional[List[int]]:
    """当選番号文字列を数字リストに変換する
    
    Args:
        winning_str: 当選番号文字列（例: "123"）または数値（例: 379.0）
    
    Returns:
        数字リスト（例: [1, 2, 3]）、無効な場合はNone
    """
    if pd.isna(winning_str) or winning_str == 'NULL' or winning_str == '':
        return None
    
    try:
        # 数値型の場合は整数に変換してから文字列に
        if isinstance(winning_str, (int, float)):
            winning_str = str(int(winning_str))
        else:
            winning_str = str(winning_str)
        
        # 小数点以下を除去（例: "379.0" -> "379"）
        if '.' in winning_str:
            winning_str = winning_str.split('.')[0]
        
        # 各桁を数字に変換
        digits = [int(d) for d in winning_str.zfill(3)]
        return digits
    except (ValueError, TypeError):
        return None


def find_digit_positions(
    grid: List[List[Optional[int]]],
    digit: int,
    rows: int,
    cols: int,
    target_rows: Optional[List[int]] = None
) -> List[Tuple[int, int]]:
    """グリッド内で指定数字の位置をすべて取得する
    
    Args:
        grid: 極CUBEグリッド（1-indexed）
        digit: 検索する数字
        rows: 行数
        cols: 列数
        target_rows: 対象行（指定された場合、その行を優先的に検索）
    
    Returns:
        位置リスト（(row, col)のタプル、1-indexed、target_rowsが指定された場合は優先順位付き）
    """
    positions = []
    if target_rows:
        # 対象行を優先的に検索
        for row in target_rows:
            if row > rows:
                continue
            for col in range(1, cols + 1):
                if grid[row][col] == digit:
                    positions.append((row, col))
        # 対象行以外も検索（対象行で見つからなかった場合のフォールバック）
        for row in range(1, rows + 1):
            if row in target_rows:
                continue
            for col in range(1, cols + 1):
                if grid[row][col] == digit:
                    positions.append((row, col))
    else:
        # 全体を検索
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                if grid[row][col] == digit:
                    positions.append((row, col))
    return positions


def is_connected(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
    """2つの位置がつながっているか判定する（横・斜め・縦）
    
    Args:
        pos1: 位置1（(row, col)、1-indexed）
        pos2: 位置2（(row, col)、1-indexed）
    
    Returns:
        つながっている場合True
    """
    row_diff = abs(pos1[0] - pos2[0])
    col_diff = abs(pos1[1] - pos2[1])
    
    # 横方向（同じ行、列の差が1）
    if row_diff == 0 and col_diff == 1:
        return True
    
    # 縦方向（同じ列、行の差が1）
    if col_diff == 0 and row_diff == 1:
        return True
    
    # 斜め方向（行の差が1、列の差が1）
    if row_diff == 1 and col_diff == 1:
        return True
    
    return False


def are_all_connected(positions: List[Tuple[int, int]]) -> bool:
    """3つの位置がすべてつながっているか判定する（グラフとして連結している）
    
    Args:
        positions: 位置リスト（3つの位置）
    
    Returns:
        すべてつながっている場合True（グラフとして連結している）
    """
    if len(positions) != 3:
        return False
    
    # 3つの位置のつながりを確認
    conn_01 = is_connected(positions[0], positions[1])
    conn_12 = is_connected(positions[1], positions[2])
    conn_02 = is_connected(positions[0], positions[2])
    
    # 3つの位置が連結している条件：
    # - 少なくとも2組がつながっている
    # - かつ、すべての位置が連結している（孤立した位置がない）
    connection_count = sum([conn_01, conn_12, conn_02])
    
    if connection_count == 0:
        return False
    elif connection_count == 1:
        # 1組のみつながっている → 孤立した位置がある
        return False
    else:
        # 2組以上つながっている → 連結している
        return True


def determine_connection_type(positions: List[Tuple[int, int]]) -> str:
    """3つの位置からつながりタイプを判定する
    
    Args:
        positions: 位置リスト（3つの位置、連結していることが前提）
    
    Returns:
        つながりタイプ: 'horizontal', 'vertical', 'diagonal', 'mixed', 'none'
    """
    if len(positions) != 3:
        return 'none'
    
    # 各ペアのつながりを確認
    conn_01 = is_connected(positions[0], positions[1])
    conn_12 = is_connected(positions[1], positions[2])
    conn_02 = is_connected(positions[0], positions[2])
    
    connection_types = set()
    
    # 位置0-1のつながりタイプ
    if conn_01:
        row_diff = abs(positions[0][0] - positions[1][0])
        col_diff = abs(positions[0][1] - positions[1][1])
        if row_diff == 0:
            connection_types.add('horizontal')
        elif col_diff == 0:
            connection_types.add('vertical')
        else:
            connection_types.add('diagonal')
    
    # 位置1-2のつながりタイプ
    if conn_12:
        row_diff = abs(positions[1][0] - positions[2][0])
        col_diff = abs(positions[1][1] - positions[2][1])
        if row_diff == 0:
            connection_types.add('horizontal')
        elif col_diff == 0:
            connection_types.add('vertical')
        else:
            connection_types.add('diagonal')
    
    # 位置0-2のつながりタイプ
    if conn_02:
        row_diff = abs(positions[0][0] - positions[2][0])
        col_diff = abs(positions[0][1] - positions[2][1])
        if row_diff == 0:
            connection_types.add('horizontal')
        elif col_diff == 0:
            connection_types.add('vertical')
        else:
            connection_types.add('diagonal')
    
    # つながりのタイプを決定
    if len(connection_types) == 0:
        return 'none'
    elif len(connection_types) == 1:
        return list(connection_types)[0]
    else:
        return 'mixed'


def check_winning_appearance(
    grid: List[List[Optional[int]]],
    winning_digits: List[int],
    rows: int,
    cols: int
) -> Dict[str, Any]:
    """極CUBE内での当選番号出現を分析する
    
    Args:
        grid: 極CUBEグリッド（1-indexed）
        winning_digits: 当選数字のリスト（3桁、例：[1, 2, 3]）
        rows: 行数
        cols: 列数
    
    Returns:
        出現分析結果の辞書
    """
    result = {
        'all_digits_found': False,
        'found_digits': [],
        'missing_digits': [],
        'positions': {},
        'connection_type': None,  # 'horizontal', 'vertical', 'diagonal', 'mixed', 'none'
        'is_connected': False,
        'connection_count': 0,
        'main_positions': []  # 使用した主要な位置（デバッグ用）
    }
    
    # 各数字の位置を取得（2,3,4行目を優先的に検索）
    target_rows = [2, 3, 4]  # 並び型分析と同じ対象行
    for i, digit in enumerate(winning_digits):
        positions = find_digit_positions(grid, digit, rows, cols, target_rows=target_rows)
        if positions:
            result['found_digits'].append(digit)
            result['positions'][digit] = positions
        else:
            result['missing_digits'].append(digit)
    
    # すべての数字が見つかったか
    result['all_digits_found'] = len(result['missing_digits']) == 0
    
    if not result['all_digits_found']:
        return result
    
    # 各数字のすべての位置の組み合わせを試す
    digit_positions_list = [result['positions'][d] for d in winning_digits]
    
    # すべての位置の組み合わせを生成
    from itertools import product
    all_combinations = list(product(*digit_positions_list))
    
    # 各組み合わせについてつながりをチェック
    found_connections = []
    for combo in all_combinations:
        if are_all_connected(list(combo)):
            conn_type = determine_connection_type(list(combo))
            found_connections.append({
                'positions': combo,
                'connection_type': conn_type
            })
    
    result['all_connection_combinations'] = found_connections
    result['connection_count'] = len(found_connections)
    
    # 見つかったつながりタイプを集計（複数ある場合はすべてカウント）
    if found_connections:
        connection_types = [conn['connection_type'] for conn in found_connections]
        result['connection_types'] = connection_types
        # 後方互換性のため、最初のつながりタイプも設定
        result['connection_type'] = connection_types[0]
        result['is_connected'] = True
    else:
        result['connection_types'] = []
        result['connection_type'] = 'none'
        result['is_connected'] = False
    
    return result


def analyze_digit_patterns(
    df: pd.DataFrame,
    start_round: int,
    end_round: int
) -> Dict[str, Any]:
    """数字の出現パターンを集計する（0-9 × 桁位置）
    
    Args:
        df: 過去当選番号データ
        start_round: 開始回号
        end_round: 終了回号
    
    Returns:
        数字の出現パターン集計結果
    """
    # フィルタリング
    filtered_df = df[(df['round_number'] >= start_round) & (df['round_number'] <= end_round)].copy()
    
    # 数字(0-9) × 桁位置ごとの出現頻度
    digit_position_counts = defaultdict(lambda: defaultdict(int))
    
    # 各桁位置での数字分布
    position_digit_counts = {
        '百の位': defaultdict(int),
        '十の位': defaultdict(int),
        '一の位': defaultdict(int)
    }
    
    # よく出現する数字の組み合わせ
    digit_combinations = defaultdict(int)  # 3桁の組み合わせ（ソート済み）
    full_combinations = defaultdict(int)  # 3桁の完全な組み合わせ（順序保持）  # 3桁の組み合わせ（ソート済み）
    full_combinations = defaultdict(int)  # 3桁の完全な組み合わせ（順序保持）
    
    # 各桁位置での数字のつながり集計
    # 百の位がXのときの十の位、一の位
    hundred_to_tens = defaultdict(lambda: defaultdict(int))  # 百の位 → 十の位
    hundred_to_ones = defaultdict(lambda: defaultdict(int))  # 百の位 → 一の位
    tens_to_ones = defaultdict(lambda: defaultdict(int))  # 十の位 → 一の位
    hundred_tens_to_ones = defaultdict(lambda: defaultdict(int))  # (百の位, 十の位) → 一の位
    
    for _, row in filtered_df.iterrows():
        winning_digits = get_winning_digits(row['n3_winning'])
        if winning_digits is None:
            continue
        
        hundred = winning_digits[0]
        tens = winning_digits[1]
        ones = winning_digits[2]
        
        # 各桁位置での数字を集計
        for pos_idx, (pos_name, digit) in enumerate(zip(['百の位', '十の位', '一の位'], winning_digits)):
            digit_position_counts[digit][pos_name] += 1
            position_digit_counts[pos_name][digit] += 1
        
        # 数字の組み合わせ（3桁の組み合わせ、ソート済み）
        combo_key = tuple(sorted(winning_digits))
        digit_combinations[combo_key] += 1
        
        # 完全な3桁の組み合わせ（順序保持）
        full_combo_key = tuple(winning_digits)
        full_combinations[full_combo_key] += 1
        
        # 各桁位置での数字のつながり集計
        hundred_to_tens[hundred][tens] += 1
        hundred_to_ones[hundred][ones] += 1
        tens_to_ones[tens][ones] += 1
        hundred_tens_to_ones[(hundred, tens)][ones] += 1
    
    # digit_combinationsのタプルキーを文字列キーに変換（JSONシリアライズ用）
    digit_combinations_str = {
        f"{combo[0]}_{combo[1]}_{combo[2]}": count
        for combo, count in digit_combinations.items()
    }
    
    # full_combinationsのタプルキーを文字列キーに変換
    full_combinations_str = {
        f"{combo[0]}{combo[1]}{combo[2]}": count
        for combo, count in full_combinations.items()
    }
    
    # つながり集計のタプルキーを文字列キーに変換
    hundred_tens_to_ones_str = {
        f"{k[0]}_{k[1]}": {str(d): c for d, c in v.items()}
        for k, v in hundred_tens_to_ones.items()
    }
    
    # 統計的分析
    total_samples = len(filtered_df)
    expected_frequency_3digit = total_samples / 1000  # 各3桁の組み合わせの期待出現回数（1000通り）
    expected_frequency_2digit = total_samples / 100  # 各2桁の組み合わせの期待出現回数（100通り）
    
    # 統計的に有意な組み合わせの判定基準
    # サンプル数が少ない場合は、より厳しい基準を適用
    # 100回未満: 期待値の3倍以上、かつ最低3回以上
    # 100回以上500回未満: 期待値の2.5倍以上、かつ最低5回以上
    # 500回以上: 期待値の2倍以上、かつ最低10回以上
    if total_samples < 100:
        threshold_multiplier_3digit = 3.0
        threshold_multiplier_2digit = 3.0
        min_count_3digit = 3
        min_count_2digit = 3
    elif total_samples < 500:
        threshold_multiplier_3digit = 2.5
        threshold_multiplier_2digit = 2.5
        min_count_3digit = 5
        min_count_2digit = 5
    else:
        threshold_multiplier_3digit = 2.0
        threshold_multiplier_2digit = 2.0
        min_count_3digit = 10
        min_count_2digit = 10
    
    # 3桁の統計的に有意な組み合わせ（段階的分類）
    # 期待値比2.5倍以上 = 統計的に有意な可能性
    significant_combinations_3digit = []
    # 期待値比2.0倍以上 = 強い傾向
    strong_trends_3digit = []
    # 期待値比1.5倍以上 = 傾向として注目
    notable_trends_3digit = []
    
    for combo, count in sorted(full_combinations.items(), key=lambda x: -x[1]):
        ratio = count / expected_frequency_3digit if expected_frequency_3digit > 0 else 0
        combo_data = {
            'combination': f"{combo[0]}{combo[1]}{combo[2]}",
            'count': count,
            'rate': (count / total_samples) * 100,
            'expected': expected_frequency_3digit,
            'ratio': ratio
        }
        
        if ratio >= 2.5 and count >= min_count_3digit:
            significant_combinations_3digit.append(combo_data)
        elif ratio >= 2.0 and count >= min_count_3digit:
            strong_trends_3digit.append(combo_data)
        elif ratio >= 1.5:
            notable_trends_3digit.append(combo_data)
    
    # 2桁の組み合わせの統計的分析（段階的分類）
    # 百の位・十の位
    significant_combinations_hundred_tens = []
    strong_trends_hundred_tens = []
    notable_trends_hundred_tens = []
    
    for hundred, tens_counts in hundred_to_tens.items():
        for tens, count in tens_counts.items():
            ratio = count / expected_frequency_2digit if expected_frequency_2digit > 0 else 0
            combo_data = {
                'combination': f"{hundred}{tens}",
                'count': count,
                'rate_overall': (count / total_samples) * 100,
                'rate_conditional': (count / sum(tens_counts.values())) * 100 if sum(tens_counts.values()) > 0 else 0,
                'expected': expected_frequency_2digit,
                'ratio': ratio
            }
            
            if ratio >= 2.5 and count >= min_count_2digit:
                significant_combinations_hundred_tens.append(combo_data)
            elif ratio >= 2.0 and count >= min_count_2digit:
                strong_trends_hundred_tens.append(combo_data)
            elif ratio >= 1.5:
                notable_trends_hundred_tens.append(combo_data)
    
    # 十の位・一の位
    significant_combinations_tens_ones = []
    strong_trends_tens_ones = []
    notable_trends_tens_ones = []
    
    for tens, ones_counts in tens_to_ones.items():
        for ones, count in ones_counts.items():
            ratio = count / expected_frequency_2digit if expected_frequency_2digit > 0 else 0
            combo_data = {
                'combination': f"{tens}{ones}",
                'count': count,
                'rate_overall': (count / total_samples) * 100,
                'rate_conditional': (count / sum(ones_counts.values())) * 100 if sum(ones_counts.values()) > 0 else 0,
                'expected': expected_frequency_2digit,
                'ratio': ratio
            }
            
            if ratio >= 2.5 and count >= min_count_2digit:
                significant_combinations_tens_ones.append(combo_data)
            elif ratio >= 2.0 and count >= min_count_2digit:
                strong_trends_tens_ones.append(combo_data)
            elif ratio >= 1.5:
                notable_trends_tens_ones.append(combo_data)
    
    # 百の位・一の位
    significant_combinations_hundred_ones = []
    strong_trends_hundred_ones = []
    notable_trends_hundred_ones = []
    
    for hundred, ones_counts in hundred_to_ones.items():
        for ones, count in ones_counts.items():
            ratio = count / expected_frequency_2digit if expected_frequency_2digit > 0 else 0
            combo_data = {
                'combination': f"{hundred}{ones}",
                'count': count,
                'rate_overall': (count / total_samples) * 100,
                'rate_conditional': (count / sum(ones_counts.values())) * 100 if sum(ones_counts.values()) > 0 else 0,
                'expected': expected_frequency_2digit,
                'ratio': ratio
            }
            
            if ratio >= 2.5 and count >= min_count_2digit:
                significant_combinations_hundred_ones.append(combo_data)
            elif ratio >= 2.0 and count >= min_count_2digit:
                strong_trends_hundred_ones.append(combo_data)
            elif ratio >= 1.5:
                notable_trends_hundred_ones.append(combo_data)
    
    return {
        'digit_position_counts': dict(digit_position_counts),
        'position_digit_counts': {k: dict(v) for k, v in position_digit_counts.items()},
        'digit_combinations': digit_combinations_str,
        'full_combinations': full_combinations_str,
        'digit_connections': {
            'hundred_to_tens': {str(k): dict(v) for k, v in hundred_to_tens.items()},
            'hundred_to_ones': {str(k): dict(v) for k, v in hundred_to_ones.items()},
            'tens_to_ones': {str(k): dict(v) for k, v in tens_to_ones.items()},
            'hundred_tens_to_ones': hundred_tens_to_ones_str
        },
        'statistical_analysis': {
            'total_samples': total_samples,
            'expected_frequency_3digit': expected_frequency_3digit,
            'expected_frequency_2digit': expected_frequency_2digit,
            'significant_combinations_3digit': significant_combinations_3digit[:20],  # 期待値比2.5倍以上
            'strong_trends_3digit': strong_trends_3digit[:20],  # 期待値比2.0倍以上
            'notable_trends_3digit': notable_trends_3digit[:20],  # 期待値比1.5倍以上
            'significant_combinations_hundred_tens': sorted(significant_combinations_hundred_tens, key=lambda x: -x['count'])[:15],
            'strong_trends_hundred_tens': sorted(strong_trends_hundred_tens, key=lambda x: -x['count'])[:15],
            'notable_trends_hundred_tens': sorted(notable_trends_hundred_tens, key=lambda x: -x['count'])[:15],
            'significant_combinations_tens_ones': sorted(significant_combinations_tens_ones, key=lambda x: -x['count'])[:15],
            'strong_trends_tens_ones': sorted(strong_trends_tens_ones, key=lambda x: -x['count'])[:15],
            'notable_trends_tens_ones': sorted(notable_trends_tens_ones, key=lambda x: -x['count'])[:15],
            'significant_combinations_hundred_ones': sorted(significant_combinations_hundred_ones, key=lambda x: -x['count'])[:15],
            'strong_trends_hundred_ones': sorted(strong_trends_hundred_ones, key=lambda x: -x['count'])[:15],
            'notable_trends_hundred_ones': sorted(notable_trends_hundred_ones, key=lambda x: -x['count'])[:15]
        },
        'total_rounds': len(filtered_df)
    }


def analyze_time_series(
    df: pd.DataFrame,
    start_round: int,
    end_round: int
) -> Dict[str, Any]:
    """時系列・周期性分析を実施する
    
    Args:
        df: 過去当選番号データ
        start_round: 開始回号
        end_round: 終了回号
    
    Returns:
        時系列・周期性分析結果
    """
    # フィルタリング
    filtered_df = df[(df['round_number'] >= start_round) & (df['round_number'] <= end_round)].copy()
    
    # 日付列をdatetime型に変換
    filtered_df['draw_date'] = pd.to_datetime(filtered_df['draw_date'], errors='coerce')
    
    # 曜日分析
    weekday_counts = defaultdict(int)
    weekday_digit_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    # 月分析
    month_counts = defaultdict(int)
    month_digit_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    # 季節分析
    season_counts = defaultdict(int)
    season_digit_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    # 年分析
    year_counts = defaultdict(int)
    year_digit_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for _, row in filtered_df.iterrows():
        if pd.isna(row['draw_date']):
            continue
        
        winning_digits = get_winning_digits(row['n3_winning'])
        if winning_digits is None:
            continue
        
        # 曜日（0=日, 1=月, ..., 6=土）
        weekday = row['draw_date'].weekday()
        weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        weekday_name = weekday_names[weekday]
        weekday_counts[weekday_name] += 1
        
        # 月（1-12）
        month = row['draw_date'].month
        month_counts[month] += 1
        
        # 季節（1-3月=春、4-6月=夏、7-9月=秋、10-12月=冬）
        if month in [1, 2, 3]:
            season = '春'
        elif month in [4, 5, 6]:
            season = '夏'
        elif month in [7, 8, 9]:
            season = '秋'
        else:
            season = '冬'
        season_counts[season] += 1
        
        # 年
        year = row['draw_date'].year
        year_counts[year] += 1
        
        # 各要素での数字分布を集計
        for pos_idx, (pos_name, digit) in enumerate(zip(['百の位', '十の位', '一の位'], winning_digits)):
            weekday_digit_counts[weekday_name][pos_name][digit] += 1
            month_digit_counts[month][pos_name][digit] += 1
            season_digit_counts[season][pos_name][digit] += 1
            year_digit_counts[year][pos_name][digit] += 1
    
    return {
        'weekday_counts': dict(weekday_counts),
        'weekday_digit_counts': {
            k: {pos: dict(d) for pos, d in v.items()}
            for k, v in weekday_digit_counts.items()
        },
        'month_counts': dict(month_counts),
        'month_digit_counts': {
            k: {pos: dict(d) for pos, d in v.items()}
            for k, v in month_digit_counts.items()
        },
        'season_counts': dict(season_counts),
        'season_digit_counts': {
            k: {pos: dict(d) for pos, d in v.items()}
            for k, v in season_digit_counts.items()
        },
        'year_counts': dict(year_counts),
        'year_digit_counts': {
            k: {pos: dict(d) for pos, d in v.items()}
            for k, v in year_digit_counts.items()
        },
        'total_rounds': len(filtered_df)
    }


def analyze_extreme_cube_base_stats(
    df: pd.DataFrame,
    keisen_master: dict,
    start_round: int,
    end_round: int
) -> Dict[str, Any]:
    """極CUBE全期間基礎集計を実施する
    
    Args:
        df: 過去当選番号データ
        keisen_master: 罫線マスターデータ
        start_round: 開始回号
        end_round: 終了回号
    
    Returns:
        分析結果の辞書
    """
    logger.info(f"極CUBE全期間基礎集計を開始します（回号: {start_round}-{end_round}）")
    
    # フィルタリング
    filtered_df = df[(df['round_number'] >= start_round) & (df['round_number'] <= end_round)].copy()
    filtered_df = filtered_df.sort_values('round_number')
    
    # 集計用の変数
    cube_appearance_stats = {
        'total_rounds': 0,
        'all_digits_found_count': 0,
        'all_digits_found_rate': 0.0,
        'connection_stats': {
            'horizontal': 0,
            'vertical': 0,
            'diagonal': 0,
            'mixed': 0,
            'none': 0
        },
        'position_stats': defaultdict(int),  # 位置ごとの出現回数
        'round_details': [],  # 各回号の詳細
        'skipped_rounds': 0,  # スキップされた回数
        'skipped_reasons': defaultdict(int),  # スキップ理由別の回数
        'error_details': []  # エラーの詳細（最初の20件まで）
    }
    
    # 各回号について分析
    for idx, row in filtered_df.iterrows():
        round_number = int(row['round_number'])
        
        # 回号の妥当性を検証
        if not validate_round_number(df, round_number):
            logger.debug(f"回号{round_number}はスキップします（前回・前々回のデータが不足）")
            continue
        
        try:
            # 極CUBEを生成
            grid, rows, cols = generate_extreme_cube(df, keisen_master, round_number)
            
            # 当選番号を取得
            winning_digits = get_winning_digits(row['n3_winning'])
            if winning_digits is None:
                continue
            
            # 極CUBE内での当選番号出現を分析
            appearance_result = check_winning_appearance(grid, winning_digits, rows, cols)
            
            # 統計情報を更新
            cube_appearance_stats['total_rounds'] += 1
            
            if appearance_result['all_digits_found']:
                cube_appearance_stats['all_digits_found_count'] += 1
                
                # つながり統計は、すべての数字が見つかった場合のみカウント
                # 複数のつながりがある場合は、すべてカウント
                if 'connection_types' in appearance_result and appearance_result['connection_types']:
                    # 見つかったすべてのつながりタイプをカウント
                    for conn_type in appearance_result['connection_types']:
                        if conn_type and conn_type != 'none':
                            cube_appearance_stats['connection_stats'][conn_type] += 1
                    # つながりが見つからなかった場合は'none'としてカウント
                    if not any(ct != 'none' for ct in appearance_result['connection_types']):
                        cube_appearance_stats['connection_stats']['none'] += 1
                else:
                    # 後方互換性のため
                    conn_type = appearance_result.get('connection_type')
                    if conn_type and conn_type != 'none':
                        cube_appearance_stats['connection_stats'][conn_type] += 1
                    else:
                        cube_appearance_stats['connection_stats']['none'] += 1
            
            # 位置統計を更新
            for digit, positions in appearance_result['positions'].items():
                for pos in positions:
                    cube_appearance_stats['position_stats'][pos] += 1
            
            # 詳細情報を記録（最初の10回のみ）
            if len(cube_appearance_stats['round_details']) < 10:
                cube_appearance_stats['round_details'].append({
                    'round_number': round_number,
                    'winning_digits': winning_digits,
                    'appearance_result': appearance_result
                })
            
            # 進捗表示（100回ごと）
            if cube_appearance_stats['total_rounds'] % 100 == 0:
                logger.info(f"進捗: {cube_appearance_stats['total_rounds']}回処理完了")
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"回号{round_number}の分析でエラー: {error_msg}")
            cube_appearance_stats['skipped_rounds'] += 1
            
            # エラーメッセージから主要な理由を抽出
            if '前回' in error_msg or '前々回' in error_msg or '未登録' in error_msg:
                reason = '前回・前々回のデータ不足'
            elif 'ChartGenerationError' in str(type(e).__name__):
                reason = '極CUBE生成エラー'
            else:
                reason = f'分析エラー: {error_msg[:50]}'  # 最初の50文字まで
            
            cube_appearance_stats['skipped_reasons'][reason] += 1
            
            # エラー詳細を記録（最初の20件まで）
            if len(cube_appearance_stats['error_details']) < 20:
                cube_appearance_stats['error_details'].append({
                    'round_number': round_number,
                    'error_type': str(type(e).__name__),
                    'error_message': error_msg
                })
            continue
    
    # 出現率を計算
    if cube_appearance_stats['total_rounds'] > 0:
        cube_appearance_stats['all_digits_found_rate'] = (
            cube_appearance_stats['all_digits_found_count'] / cube_appearance_stats['total_rounds']
        ) * 100
    
    logger.info("極CUBE内での当選番号出現分析が完了しました")
    
    # 数字の出現パターンを集計
    logger.info("数字の出現パターンを集計しています...")
    digit_patterns = analyze_digit_patterns(df, start_round, end_round)
    
    # 時系列・周期性分析
    logger.info("時系列・周期性分析を実施しています...")
    time_series = analyze_time_series(df, start_round, end_round)
    
    # position_statsのタプルキーを文字列キーに変換（JSONシリアライズ用）
    cube_appearance_stats['position_stats'] = {
        f"{row}_{col}": count
        for (row, col), count in cube_appearance_stats['position_stats'].items()
    }
    
    # 結果をまとめる
    result = {
        'analysis_period': {
            'start_round': start_round,
            'end_round': end_round,
            'total_rounds': end_round - start_round + 1
        },
        'cube_appearance_stats': cube_appearance_stats,
        'digit_patterns': digit_patterns,
        'time_series': time_series,
        'generated_at': datetime.now().isoformat()
    }
    
    logger.info("極CUBE全期間基礎集計が完了しました")
    return result


def save_results(result: Dict[str, Any], output_dir: Path):
    """結果をCSV/JSON形式で出力する
    
    Args:
        result: 分析結果の辞書
        output_dir: 出力ディレクトリ
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON形式で出力
    json_path = output_dir / f'extreme_cube_base_stats_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON形式で結果を保存しました: {json_path}")
    
    # CSV形式で出力（主要統計のみ）
    csv_path = output_dir / f'extreme_cube_base_stats_{timestamp}.csv'
    
    # 主要統計をDataFrameに変換
    summary_data = {
        '項目': [
            '分析期間開始回号',
            '分析期間終了回号',
            '分析対象回数',
            '極CUBE内出現回数',
            '極CUBE内出現率(%)',
            '横方向つながり',
            '縦方向つながり',
            '斜め方向つながり',
            '混合つながり',
            'つながりなし',
            'つながり統計合計'
        ],
        '値': [
            result['analysis_period']['start_round'],
            result['analysis_period']['end_round'],
            result['cube_appearance_stats']['total_rounds'],
            result['cube_appearance_stats']['all_digits_found_count'],
            f"{result['cube_appearance_stats']['all_digits_found_rate']:.2f}",
            result['cube_appearance_stats']['connection_stats']['horizontal'],
            result['cube_appearance_stats']['connection_stats']['vertical'],
            result['cube_appearance_stats']['connection_stats']['diagonal'],
            result['cube_appearance_stats']['connection_stats']['mixed'],
            result['cube_appearance_stats']['connection_stats']['none'],
            sum(result['cube_appearance_stats']['connection_stats'].values())
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    logger.info(f"CSV形式で結果を保存しました: {csv_path}")
    
    # Markdown形式でレポートを出力
    md_path = output_dir / f'extreme_cube_base_stats_{timestamp}.md'
    save_markdown_report(result, md_path)


def _write_statistical_summary(f, digit_patterns: Dict[str, Any], period: Dict[str, Any]):
    """統計的分析の結論とコメントを出力する
    
    Args:
        f: ファイルオブジェクト
        digit_patterns: 数字パターン分析結果
        period: 分析期間情報
    """
    if 'statistical_analysis' not in digit_patterns:
        return
    
    stats = digit_patterns['statistical_analysis']
    expected_3digit = stats['expected_frequency_3digit']
    expected_2digit = stats['expected_frequency_2digit']
    total_samples = stats['total_samples']
    
    # 3桁の組み合わせランキングを取得
    full_combinations = digit_patterns.get('full_combinations', {})
    combo_list = []
    for combo_str, count in full_combinations.items():
        combo_list.append((combo_str, count))
    combo_list.sort(key=lambda x: -x[1])
    
    # 2桁の組み合わせランキングを取得（期待値比1.3倍以上）
    significant_2digit_1_3 = []
    digit_connections = digit_patterns.get('digit_connections', {})
    
    # 十の位・一の位
    tens_ones = digit_connections.get('tens_to_ones', {})
    if isinstance(tens_ones, dict):
        for tens_str, ones_counts in tens_ones.items():
            if isinstance(ones_counts, dict):
                for ones_str, count in ones_counts.items():
                    try:
                        count = int(count)
                        if expected_2digit > 0:
                            ratio = count / expected_2digit
                            if ratio >= 1.3:
                                significant_2digit_1_3.append({
                                    'combo': f"{tens_str}-{ones_str}",
                                    'type': '十の位・一の位',
                                    'count': count,
                                    'expected': expected_2digit,
                                    'ratio': ratio,
                                    'rate': (count / total_samples) * 100 if total_samples > 0 else 0.0
                                })
                    except (ValueError, TypeError):
                        continue
    
    # 百の位・十の位
    hundred_tens = digit_connections.get('hundred_to_tens', {})
    if isinstance(hundred_tens, dict):
        for hundred_str, tens_counts in hundred_tens.items():
            if isinstance(tens_counts, dict):
                for tens_str, count in tens_counts.items():
                    try:
                        count = int(count)
                        if expected_2digit > 0:
                            ratio = count / expected_2digit
                            if ratio >= 1.3:
                                significant_2digit_1_3.append({
                                    'combo': f"{hundred_str}-{tens_str}",
                                    'type': '百の位・十の位',
                                    'count': count,
                                    'expected': expected_2digit,
                                    'ratio': ratio,
                                    'rate': (count / total_samples) * 100 if total_samples > 0 else 0.0
                                })
                    except (ValueError, TypeError):
                        continue
    
    # 百の位・一の位
    hundred_ones = digit_connections.get('hundred_to_ones', {})
    if isinstance(hundred_ones, dict):
        for hundred_str, ones_counts in hundred_ones.items():
            if isinstance(ones_counts, dict):
                for ones_str, count in ones_counts.items():
                    try:
                        count = int(count)
                        if expected_2digit > 0:
                            ratio = count / expected_2digit
                            if ratio >= 1.3:
                                significant_2digit_1_3.append({
                                    'combo': f"{hundred_str}-{ones_str}",
                                    'type': '百の位・一の位',
                                    'count': count,
                                    'expected': expected_2digit,
                                    'ratio': ratio,
                                    'rate': (count / total_samples) * 100 if total_samples > 0 else 0.0
                                })
                    except (ValueError, TypeError):
                        continue
    
    significant_2digit_1_3.sort(key=lambda x: -x['ratio'])
    
    # 条件付き確率で特に強い傾向を取得
    strong_conditional = []
    # 百の位 → 十の位
    if isinstance(hundred_tens, dict):
        for hundred_str, tens_counts in hundred_tens.items():
            if isinstance(tens_counts, dict):
                try:
                    total_for_hundred = sum(int(v) for v in tens_counts.values())
                    for tens_str, count in tens_counts.items():
                        try:
                            count = int(count)
                            if total_for_hundred > 0:
                                conditional_prob = (count / total_for_hundred) * 100
                                expected_conditional = 10.0  # 期待値10%
                                if conditional_prob > 0:
                                    ratio_conditional = conditional_prob / expected_conditional
                                    if ratio_conditional >= 1.4:  # 期待値の1.4倍以上
                                        strong_conditional.append({
                                            'axis': f"百の位「{hundred_str}」",
                                            'next': f"十の位「{tens_str}」",
                                            'prob': conditional_prob,
                                            'ratio': ratio_conditional
                                        })
                        except (ValueError, TypeError):
                            continue
                except (ValueError, TypeError):
                    continue
    
    # 十の位 → 一の位
    if isinstance(tens_ones, dict):
        for tens_str, ones_counts in tens_ones.items():
            if isinstance(ones_counts, dict):
                try:
                    total_for_tens = sum(int(v) for v in ones_counts.values())
                    for ones_str, count in ones_counts.items():
                        try:
                            count = int(count)
                            if total_for_tens > 0:
                                conditional_prob = (count / total_for_tens) * 100
                                expected_conditional = 10.0
                                if conditional_prob > 0:
                                    ratio_conditional = conditional_prob / expected_conditional
                                    if ratio_conditional >= 1.4:
                                        strong_conditional.append({
                                            'axis': f"十の位「{tens_str}」",
                                            'next': f"一の位「{ones_str}」",
                                            'prob': conditional_prob,
                                            'ratio': ratio_conditional
                                        })
                        except (ValueError, TypeError):
                            continue
                except (ValueError, TypeError):
                    continue
    
    strong_conditional.sort(key=lambda x: -x['ratio'])
    
    f.write(f"## 📊 統計的分析の結論とコメント\n\n")
    f.write(f"### 主要な結論\n\n")
    
    # 1. 3桁の組み合わせについて
    f.write(f"#### 1. 3桁の組み合わせについて\n")
    sig_3digit = stats.get('significant_combinations_3digit', [])  # 期待値比2.5倍以上
    strong_3digit = stats.get('strong_trends_3digit', [])  # 期待値比2.0倍以上
    notable_3digit = stats.get('notable_trends_3digit', [])  # 期待値比1.5倍以上
    
    f.write(f"- **統計的に有意な可能性**: {len(sig_3digit)}件（期待値比2.5倍以上）\n")
    if sig_3digit:
        for sig_combo in sig_3digit[:3]:
            f.write(f"  - 「{sig_combo['combination']}」: {sig_combo['count']}回出現（期待値{expected_3digit:.2f}回の{sig_combo['ratio']:.2f}倍）\n")
    
    f.write(f"- **強い傾向**: {len(strong_3digit)}件（期待値比2.0倍以上）\n")
    if strong_3digit:
        for strong_combo in strong_3digit[:3]:
            f.write(f"  - 「{strong_combo['combination']}」: {strong_combo['count']}回出現（期待値{expected_3digit:.2f}回の{strong_combo['ratio']:.2f}倍）\n")
    
    f.write(f"- **傾向として注目**: {len(notable_3digit)}件（期待値比1.5倍以上）\n")
    if notable_3digit:
        for notable_combo in notable_3digit[:3]:
            f.write(f"  - 「{notable_combo['combination']}」: {notable_combo['count']}回出現（期待値{expected_3digit:.2f}回の{notable_combo['ratio']:.2f}倍）\n")
    
    f.write(f"- **解釈**: ")
    if sig_3digit:
        f.write(f"期待値比2.5倍以上の組み合わせは統計的に有意な可能性があるが、サンプル数が少ない場合、誤検出のリスクがある。")
    elif strong_3digit:
        f.write(f"期待値比2.0倍以上の組み合わせは強い傾向を示しているが、統計的に有意な可能性を判断するには、より多くのサンプル数が必要。")
    elif notable_3digit:
        f.write(f"期待値比1.5倍以上の組み合わせは傾向として注目に値するが、統計的検定の信頼性は限定的。")
    else:
        f.write(f"期待値比1.5倍以上の組み合わせは見つからなかった。")
    f.write(f"\n")
    
    # 2. 2桁の組み合わせについて
    f.write(f"#### 2. 2桁の組み合わせについて\n")
    
    # 2桁の組み合わせの分類を統合（タイプ情報を追加）
    sig_hundred_tens = stats.get('significant_combinations_hundred_tens', [])
    sig_tens_ones = stats.get('significant_combinations_tens_ones', [])
    sig_hundred_ones = stats.get('significant_combinations_hundred_ones', [])
    strong_hundred_tens = stats.get('strong_trends_hundred_tens', [])
    strong_tens_ones = stats.get('strong_trends_tens_ones', [])
    strong_hundred_ones = stats.get('strong_trends_hundred_ones', [])
    notable_hundred_tens = stats.get('notable_trends_hundred_tens', [])
    notable_tens_ones = stats.get('notable_trends_tens_ones', [])
    notable_hundred_ones = stats.get('notable_trends_hundred_ones', [])
    
    # タイプ情報を追加（コピーを作成してから追加）
    sig_2digit_with_type = []
    for item in sig_hundred_tens:
        item_copy = item.copy()
        item_copy['type'] = '百の位・十の位'
        sig_2digit_with_type.append(item_copy)
    for item in sig_tens_ones:
        item_copy = item.copy()
        item_copy['type'] = '十の位・一の位'
        sig_2digit_with_type.append(item_copy)
    for item in sig_hundred_ones:
        item_copy = item.copy()
        item_copy['type'] = '百の位・一の位'
        sig_2digit_with_type.append(item_copy)
    
    strong_2digit_with_type = []
    for item in strong_hundred_tens:
        item_copy = item.copy()
        item_copy['type'] = '百の位・十の位'
        strong_2digit_with_type.append(item_copy)
    for item in strong_tens_ones:
        item_copy = item.copy()
        item_copy['type'] = '十の位・一の位'
        strong_2digit_with_type.append(item_copy)
    for item in strong_hundred_ones:
        item_copy = item.copy()
        item_copy['type'] = '百の位・一の位'
        strong_2digit_with_type.append(item_copy)
    
    notable_2digit_with_type = []
    for item in notable_hundred_tens:
        item_copy = item.copy()
        item_copy['type'] = '百の位・十の位'
        notable_2digit_with_type.append(item_copy)
    for item in notable_tens_ones:
        item_copy = item.copy()
        item_copy['type'] = '十の位・一の位'
        notable_2digit_with_type.append(item_copy)
    for item in notable_hundred_ones:
        item_copy = item.copy()
        item_copy['type'] = '百の位・一の位'
        notable_2digit_with_type.append(item_copy)
    
    f.write(f"- **統計的に有意な可能性**: {len(sig_2digit_with_type)}件（期待値比2.5倍以上）\n")
    if sig_2digit_with_type:
        for item in sorted(sig_2digit_with_type, key=lambda x: -x['ratio'])[:3]:
            f.write(f"  - {item['type']}「{item['combination']}」: {item['count']}回（期待値{expected_2digit:.2f}回の{item['ratio']:.2f}倍）\n")
    
    f.write(f"- **強い傾向**: {len(strong_2digit_with_type)}件（期待値比2.0倍以上）\n")
    if strong_2digit_with_type:
        for item in sorted(strong_2digit_with_type, key=lambda x: -x['ratio'])[:3]:
            f.write(f"  - {item['type']}「{item['combination']}」: {item['count']}回（期待値{expected_2digit:.2f}回の{item['ratio']:.2f}倍）\n")
    
    f.write(f"- **傾向として注目**: {len(notable_2digit_with_type)}件（期待値比1.5倍以上）\n")
    if notable_2digit_with_type:
        for item in sorted(notable_2digit_with_type, key=lambda x: -x['ratio'])[:3]:
            f.write(f"  - {item['type']}「{item['combination']}」: {item['count']}回（期待値{expected_2digit:.2f}回の{item['ratio']:.2f}倍）\n")
    
    # 1.3倍以上の組み合わせも表示（参考情報）
    f.write(f"- **参考情報（期待値比1.3倍以上）**: {len(significant_2digit_1_3)}件\n")
    if significant_2digit_1_3:
        for item in significant_2digit_1_3[:3]:
            f.write(f"  - {item['type']}「{item['combo']}」: {item['count']}回（期待値{expected_2digit:.2f}回の{item['ratio']:.2f}倍）\n")
    
    f.write(f"- **解釈**: 期待値比2.5倍以上の組み合わせは統計的に有意な可能性があるが、サンプル数が少ない場合、誤検出のリスクがある。")
    f.write(f"期待値比1.5倍以上の組み合わせは傾向として注目に値する。\n")
    f.write(f"\n")
    
    # 3. 条件付き確率について
    f.write(f"#### 3. 条件付き確率（軸数字ごとの傾向）について\n")
    f.write(f"- **実用的な傾向が確認できる**: 軸数字（例：百の位）が決まった時、次の数字（例：十の位）の出現に偏りがある\n")
    f.write(f"- **特に強い傾向の例**:\n")
    for item in strong_conditional[:5]:
        f.write(f"  - {item['axis']}の時、{item['next']}の確率: {item['prob']:.2f}%（期待値10%の{item['ratio']:.2f}倍）\n")
    f.write(f"- **解釈**: 軸数字ごとに次の数字の出現確率に明確な偏りがあり、実用的な予測に活用できる可能性がある。\n")
    f.write(f"\n")
    
    # 統計的指標の説明
    f.write(f"### 統計的指標の説明\n\n")
    f.write(f"#### 「出現率」と「割合」の違い\n")
    f.write(f"- **出現率**: 全体に対する割合（無条件確率）\n")
    f.write(f"  - 例：百の位・十の位の組み合わせ「5-0」の出現率 = 43回 ÷ {total_samples}回 = 1.44%\n")
    f.write(f"- **割合（条件付き確率）**: 特定の条件が満たされた時の確率\n")
    f.write(f"  - 例：百の位が「5」の時、十の位が「0」の割合 = 43回 ÷ 291回 = 14.78%\n")
    f.write(f"  - **意味**: 軸数字が決まった時点で、次の数字を選ぶ際の参考になる実用的な指標\n")
    f.write(f"\n")
    
    f.write(f"#### 期待値比の意味\n")
    f.write(f"- **期待値比 = 実際の出現回数 ÷ 期待値**\n")
    f.write(f"- **期待値**: すべての組み合わせが均等に出現する場合の期待出現回数\n")
    f.write(f"  - 3桁の組み合わせ: {expected_3digit:.2f}回（{total_samples}回 ÷ 1000通り）\n")
    f.write(f"  - 2桁の組み合わせ: {expected_2digit:.2f}回（{total_samples}回 ÷ 100通り）\n")
    f.write(f"- **期待値比の目安（段階的分類）**:\n")
    f.write(f"  - 1.0倍 = 期待通り\n")
    f.write(f"  - 1.5倍以上 = **傾向として注目**（傾向がある可能性）\n")
    f.write(f"  - 2.0倍以上 = **強い傾向**（より強い傾向を示す）\n")
    f.write(f"  - 2.5倍以上 = **統計的に有意な可能性**（統計的検定で有意な可能性が高い）\n")
    f.write(f"  - **注意**: サンプル数が少ない場合、誤検出（false positive）のリスクが高くなる。\n")
    f.write(f"    サンプル数が増えると、期待値比が変わり、統計的優位性の判定も変わる可能性がある。\n")
    f.write(f"\n")
    
    # 実用的な活用方法
    f.write(f"### 実用的な活用方法\n\n")
    f.write(f"#### 軸数字の候補を選ぶ際の推奨方法\n")
    f.write(f"1. **条件付き確率（割合）を優先的に使用**\n")
    f.write(f"   - 軸数字が決まった時点で、次の数字の出現確率を比較\n")
    f.write(f"   - 期待値（10%）より高い割合の数字を優先的に選択\n")
    f.write(f"\n")
    f.write(f"2. **期待値比も併用**\n")
    f.write(f"   - 条件付き確率だけでなく、期待値比も確認\n")
    f.write(f"   - 期待値比1.3倍以上の組み合わせを傾向として注目\n")
    f.write(f"\n")
    f.write(f"3. **注意事項**\n")
    f.write(f"   - 過去の傾向が将来も続く保証はない\n")
    f.write(f"   - ナンバーズ3は抽選によるランダムな結果\n")
    f.write(f"   - 統計的傾向は「参考情報」として活用し、過度な期待は避ける\n")
    f.write(f"\n")
    
    # 根拠データ
    f.write(f"### 根拠データ\n\n")
    
    # 3桁の組み合わせ
    f.write(f"#### 3桁の組み合わせ\n\n")
    
    f.write(f"##### 統計的に有意な可能性（期待値比2.5倍以上）\n")
    f.write(f"| 組み合わせ | 出現回数 | 期待値 | 期待値比 | 出現率 |\n")
    f.write(f"|-----------|----------|--------|----------|--------|\n")
    if sig_3digit:
        for sig_combo in sig_3digit[:5]:
            f.write(f"| {sig_combo['combination']} | {sig_combo['count']}回 | {expected_3digit:.2f}回 | {sig_combo['ratio']:.2f}倍 | {sig_combo['rate']:.2f}% |\n")
    else:
        f.write(f"| （該当なし） | - | - | - | - |\n")
    f.write(f"\n")
    
    f.write(f"##### 強い傾向（期待値比2.0倍以上）\n")
    f.write(f"| 組み合わせ | 出現回数 | 期待値 | 期待値比 | 出現率 |\n")
    f.write(f"|-----------|----------|--------|----------|--------|\n")
    if strong_3digit:
        for strong_combo in strong_3digit[:5]:
            f.write(f"| {strong_combo['combination']} | {strong_combo['count']}回 | {expected_3digit:.2f}回 | {strong_combo['ratio']:.2f}倍 | {strong_combo['rate']:.2f}% |\n")
    else:
        f.write(f"| （該当なし） | - | - | - | - |\n")
    f.write(f"\n")
    
    f.write(f"##### 傾向として注目（期待値比1.5倍以上）\n")
    f.write(f"| 組み合わせ | 出現回数 | 期待値 | 期待値比 | 出現率 |\n")
    f.write(f"|-----------|----------|--------|----------|--------|\n")
    if notable_3digit:
        for notable_combo in notable_3digit[:5]:
            f.write(f"| {notable_combo['combination']} | {notable_combo['count']}回 | {expected_3digit:.2f}回 | {notable_combo['ratio']:.2f}倍 | {notable_combo['rate']:.2f}% |\n")
    else:
        f.write(f"| （該当なし） | - | - | - | - |\n")
    f.write(f"\n")
    
    # 2桁の組み合わせ
    f.write(f"#### 2桁の組み合わせ\n\n")
    
    f.write(f"##### 統計的に有意な可能性（期待値比2.5倍以上）\n")
    f.write(f"| 組み合わせ | タイプ | 出現回数 | 期待値 | 期待値比 | 出現率 |\n")
    f.write(f"|-----------|--------|----------|--------|----------|--------|\n")
    if sig_2digit_with_type:
        for item in sorted(sig_2digit_with_type, key=lambda x: -x['ratio'])[:5]:
            f.write(f"| {item['combination']} | {item['type']} | {item['count']}回 | {expected_2digit:.2f}回 | {item['ratio']:.2f}倍 | {item['rate_overall']:.2f}% |\n")
    else:
        f.write(f"| （該当なし） | - | - | - | - | - |\n")
    f.write(f"\n")
    
    f.write(f"##### 強い傾向（期待値比2.0倍以上）\n")
    f.write(f"| 組み合わせ | タイプ | 出現回数 | 期待値 | 期待値比 | 出現率 |\n")
    f.write(f"|-----------|--------|----------|--------|----------|--------|\n")
    if strong_2digit_with_type:
        for item in sorted(strong_2digit_with_type, key=lambda x: -x['ratio'])[:5]:
            f.write(f"| {item['combination']} | {item['type']} | {item['count']}回 | {expected_2digit:.2f}回 | {item['ratio']:.2f}倍 | {item['rate_overall']:.2f}% |\n")
    else:
        f.write(f"| （該当なし） | - | - | - | - | - |\n")
    f.write(f"\n")
    
    f.write(f"##### 傾向として注目（期待値比1.5倍以上）\n")
    f.write(f"| 組み合わせ | タイプ | 出現回数 | 期待値 | 期待値比 | 出現率 |\n")
    f.write(f"|-----------|--------|----------|--------|----------|--------|\n")
    if notable_2digit_with_type:
        for item in sorted(notable_2digit_with_type, key=lambda x: -x['ratio'])[:5]:
            f.write(f"| {item['combination']} | {item['type']} | {item['count']}回 | {expected_2digit:.2f}回 | {item['ratio']:.2f}倍 | {item['rate_overall']:.2f}% |\n")
    else:
        f.write(f"| （該当なし） | - | - | - | - | - |\n")
    f.write(f"\n")
    
    f.write(f"#### 条件付き確率で特に強い傾向（期待値10%に対する割合）\n")
    f.write(f"| 軸数字 | 次の数字 | 条件付き確率 | 期待値比 |\n")
    f.write(f"|--------|----------|--------------|----------|\n")
    for item in strong_conditional[:5]:
        f.write(f"| {item['axis']} | {item['next']} | {item['prob']:.2f}% | {item['ratio']:.2f}倍 |\n")
    f.write(f"\n")


def save_markdown_report(result: Dict[str, Any], md_path: Path):
    """Markdown形式でレポートを出力する
    
    Args:
        result: 分析結果の辞書
        md_path: 出力ファイルパス
    """
    cube_stats = result['cube_appearance_stats']
    period = result['analysis_period']
    digit_patterns = result['digit_patterns']
    time_series = result['time_series']
    
    # つながり統計の合計を計算
    connection_total = sum(cube_stats['connection_stats'].values())
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 極CUBE全期間基礎集計レポート\n\n")
        f.write(f"**生成日時**: {result['generated_at']}\n\n")
        
        f.write(f"## 分析期間\n\n")
        f.write(f"- **開始回号**: {period['start_round']}回\n")
        f.write(f"- **終了回号**: {period['end_round']}回\n")
        f.write(f"- **指定回数**: {period['total_rounds']}回\n")
        f.write(f"- **分析対象回数**: {cube_stats['total_rounds']}回\n")
        if 'skipped_rounds' in cube_stats and cube_stats['skipped_rounds'] > 0:
            f.write(f"- **スキップされた回数**: {cube_stats['skipped_rounds']}回\n")
            if 'skipped_reasons' in cube_stats:
                f.write(f"  - スキップ理由:\n")
                for reason, count in sorted(cube_stats['skipped_reasons'].items(), key=lambda x: -x[1]):
                    f.write(f"    - {reason}: {count}回\n")
            
            # エラー詳細を表示（最初の10件まで）
            if 'error_details' in cube_stats and cube_stats['error_details']:
                f.write(f"\n  - **エラー詳細（最初の10件）**:\n")
                for error_detail in cube_stats['error_details'][:10]:
                    f.write(f"    - 回号{error_detail['round_number']}: {error_detail['error_type']} - {error_detail['error_message'][:100]}\n")
        f.write(f"\n")
        
        # 統計的分析の結論とコメントを冒頭に追加
        if 'statistical_analysis' in digit_patterns:
            _write_statistical_summary(f, digit_patterns, period)
        
        f.write(f"## 極CUBE内での当選番号出現分析\n\n")
        f.write(f"### 基本統計\n\n")
        f.write(f"- **極CUBE内出現回数**: {cube_stats['all_digits_found_count']}回\n")
        f.write(f"- **極CUBE内出現率**: {cube_stats['all_digits_found_rate']:.2f}%\n\n")
        
        f.write(f"### つながり統計\n\n")
        f.write(f"#### つながりタイプの定義\n\n")
        f.write(f"- **横方向**: 3つの数字が同じ行で隣接する列に配置されている（例: (2,2), (2,3), (2,4)）\n")
        f.write(f"- **縦方向**: 3つの数字が同じ列で隣接する行に配置されている（例: (2,3), (3,3), (4,3)）\n")
        f.write(f"- **斜め方向**: 3つの数字が斜め方向に隣接して配置されている（例: (2,2), (3,3), (4,4)）\n")
        f.write(f"- **混合**: 複数のつながりタイプが混在している（例: 横方向と斜め方向の組み合わせ）\n")
        f.write(f"- **つながりなし**: 3つの数字が極CUBE内に見つかったが、つながっていない\n\n")
        f.write(f"**注意**: つながり判定は、3つの数字の位置がグラフとして連結している場合のみ有効です。\n")
        f.write(f"孤立した位置がある場合は「つながりなし」としてカウントされます。\n\n")
        
        f.write(f"#### つながり統計結果\n\n")
        f.write(f"| つながりタイプ | 回数 | 割合 |\n")
        f.write(f"|---------------|------|------|\n")
        for conn_type, count in cube_stats['connection_stats'].items():
            if connection_total > 0:
                rate = (count / connection_total) * 100
            else:
                rate = 0.0
            conn_name = {
                'horizontal': '横方向',
                'vertical': '縦方向',
                'diagonal': '斜め方向',
                'mixed': '混合',
                'none': 'つながりなし'
            }.get(conn_type, conn_type)
            f.write(f"| {conn_name} | {count}回 | {rate:.2f}% |\n")
        f.write(f"| **合計** | **{connection_total}回** | **100.00%** |\n\n")
        
        f.write(f"## 数字の出現パターン\n\n")
        f.write(f"### 各桁位置での数字分布\n\n")
        for pos_name, digit_counts in digit_patterns['position_digit_counts'].items():
            f.write(f"#### {pos_name}\n\n")
            f.write(f"| 数字 | 出現回数 | 割合 |\n")
            f.write(f"|------|----------|------|\n")
            total = sum(digit_counts.values())
            for digit in sorted(digit_counts.keys()):
                count = digit_counts[digit]
                if total > 0:
                    rate = (count / total) * 100
                else:
                    rate = 0.0
                f.write(f"| {digit} | {count}回 | {rate:.2f}% |\n")
            f.write(f"\n")
        
        # 各桁位置での数字のつながり集計
        if 'digit_connections' in digit_patterns:
            f.write(f"### 各桁位置での数字のつながり集計\n\n")
            
            # 百・十、十・一、百・一の位の組み合わせランキング
            f.write(f"#### 2桁の組み合わせランキング\n\n")
            
            # 百の位・十の位の組み合わせランキング
            f.write(f"##### 百の位・十の位の組み合わせランキング（上位20件）\n\n")
            f.write(f"| 順位 | 百の位 | 十の位 | 出現回数 | 出現率 |\n")
            f.write(f"|------|--------|--------|----------|--------|\n")
            hundred_tens_ranking = []
            for hundred_digit, tens_counts in digit_patterns['digit_connections']['hundred_to_tens'].items():
                for tens_digit, count in tens_counts.items():
                    hundred_tens_ranking.append((hundred_digit, tens_digit, count))
            hundred_tens_ranking.sort(key=lambda x: -x[2])
            total_samples = digit_patterns.get('total_rounds', 0)
            for rank, (hundred, tens, count) in enumerate(hundred_tens_ranking[:20], 1):
                rate = (count / total_samples) * 100 if total_samples > 0 else 0.0
                f.write(f"| {rank} | {hundred} | {tens} | {count}回 | {rate:.2f}% |\n")
            f.write(f"\n")
            
            # 十の位・一の位の組み合わせランキング
            f.write(f"##### 十の位・一の位の組み合わせランキング（上位20件）\n\n")
            f.write(f"| 順位 | 十の位 | 一の位 | 出現回数 | 出現率 |\n")
            f.write(f"|------|--------|--------|----------|--------|\n")
            tens_ones_ranking = []
            for tens_digit, ones_counts in digit_patterns['digit_connections']['tens_to_ones'].items():
                for ones_digit, count in ones_counts.items():
                    tens_ones_ranking.append((tens_digit, ones_digit, count))
            tens_ones_ranking.sort(key=lambda x: -x[2])
            for rank, (tens, ones, count) in enumerate(tens_ones_ranking[:20], 1):
                rate = (count / total_samples) * 100 if total_samples > 0 else 0.0
                f.write(f"| {rank} | {tens} | {ones} | {count}回 | {rate:.2f}% |\n")
            f.write(f"\n")
            
            # 百の位・一の位の組み合わせランキング
            f.write(f"##### 百の位・一の位の組み合わせランキング（上位20件）\n\n")
            f.write(f"| 順位 | 百の位 | 一の位 | 出現回数 | 出現率 |\n")
            f.write(f"|------|--------|--------|----------|--------|\n")
            hundred_ones_ranking = []
            for hundred_digit, ones_counts in digit_patterns['digit_connections']['hundred_to_ones'].items():
                for ones_digit, count in ones_counts.items():
                    hundred_ones_ranking.append((hundred_digit, ones_digit, count))
            hundred_ones_ranking.sort(key=lambda x: -x[2])
            for rank, (hundred, ones, count) in enumerate(hundred_ones_ranking[:20], 1):
                rate = (count / total_samples) * 100 if total_samples > 0 else 0.0
                f.write(f"| {rank} | {hundred} | {ones} | {count}回 | {rate:.2f}% |\n")
            f.write(f"\n")
            
            # 百の位 → 十の位
            f.write(f"#### 百の位 → 十の位\n\n")
            f.write(f"| 百の位 | 十の位 | 出現回数 | 割合 |\n")
            f.write(f"|--------|--------|----------|------|\n")
            for hundred_digit, tens_counts in sorted(digit_patterns['digit_connections']['hundred_to_tens'].items()):
                total_for_hundred = sum(tens_counts.values())
                for tens_digit, count in sorted(tens_counts.items(), key=lambda x: -x[1])[:10]:  # 上位10件
                    if total_for_hundred > 0:
                        rate = (count / total_for_hundred) * 100
                    else:
                        rate = 0.0
                    f.write(f"| {hundred_digit} | {tens_digit} | {count}回 | {rate:.2f}% |\n")
            f.write(f"\n")
            
            # 百の位 → 一の位
            f.write(f"#### 百の位 → 一の位\n\n")
            f.write(f"| 百の位 | 一の位 | 出現回数 | 割合 |\n")
            f.write(f"|--------|--------|----------|------|\n")
            for hundred_digit, ones_counts in sorted(digit_patterns['digit_connections']['hundred_to_ones'].items()):
                total_for_hundred = sum(ones_counts.values())
                for ones_digit, count in sorted(ones_counts.items(), key=lambda x: -x[1])[:10]:  # 上位10件
                    if total_for_hundred > 0:
                        rate = (count / total_for_hundred) * 100
                    else:
                        rate = 0.0
                    f.write(f"| {hundred_digit} | {ones_digit} | {count}回 | {rate:.2f}% |\n")
            f.write(f"\n")
            
            # 十の位 → 一の位
            f.write(f"#### 十の位 → 一の位\n\n")
            f.write(f"| 十の位 | 一の位 | 出現回数 | 割合 |\n")
            f.write(f"|--------|--------|----------|------|\n")
            for tens_digit, ones_counts in sorted(digit_patterns['digit_connections']['tens_to_ones'].items()):
                total_for_tens = sum(ones_counts.values())
                for ones_digit, count in sorted(ones_counts.items(), key=lambda x: -x[1])[:10]:  # 上位10件
                    if total_for_tens > 0:
                        rate = (count / total_for_tens) * 100
                    else:
                        rate = 0.0
                    f.write(f"| {tens_digit} | {ones_digit} | {count}回 | {rate:.2f}% |\n")
            f.write(f"\n")
            
            # 百の位・十の位 → 一の位
            f.write(f"#### 百の位・十の位 → 一の位（上位20件）\n\n")
            f.write(f"| 百の位 | 十の位 | 一の位 | 出現回数 |\n")
            f.write(f"|--------|--------|--------|----------|\n")
            all_combinations = []
            for key, ones_counts in digit_patterns['digit_connections']['hundred_tens_to_ones'].items():
                hundred, tens = key.split('_')
                for ones_digit, count in ones_counts.items():
                    all_combinations.append((hundred, tens, ones_digit, count))
            # 出現回数でソートして上位20件
            all_combinations.sort(key=lambda x: -x[3])
            for hundred, tens, ones, count in all_combinations[:20]:
                f.write(f"| {hundred} | {tens} | {ones} | {count}回 |\n")
            f.write(f"\n")
        
        # 3桁の組み合わせ総合ランキングと統計的分析
        if 'full_combinations' in digit_patterns and 'statistical_analysis' in digit_patterns:
            f.write(f"### 3桁の組み合わせ総合ランキング（上位30件）\n\n")
            f.write(f"| 順位 | 組み合わせ | 出現回数 | 出現率 | 期待値 | 期待値比 |\n")
            f.write(f"|------|-----------|----------|--------|--------|----------|\n")
            
            # 完全な組み合わせを出現回数でソート
            combo_list = []
            for combo_str, count in digit_patterns['full_combinations'].items():
                combo_list.append((combo_str, count))
            combo_list.sort(key=lambda x: -x[1])
            
            stats = digit_patterns['statistical_analysis']
            expected_3digit = stats['expected_frequency_3digit']
            expected_2digit = stats['expected_frequency_2digit']
            
            for rank, (combo_str, count) in enumerate(combo_list[:30], 1):
                rate = (count / stats['total_samples']) * 100 if stats['total_samples'] > 0 else 0.0
                ratio = count / expected_3digit if expected_3digit > 0 else 0.0
                f.write(f"| {rank} | {combo_str} | {count}回 | {rate:.2f}% | {expected_3digit:.2f} | {ratio:.2f}倍 |\n")
            f.write(f"\n")
            
            # 統計的分析とコメント
            f.write(f"### 統計的分析と知見\n\n")
            f.write(f"#### 基本統計\n\n")
            f.write(f"- **総サンプル数**: {stats['total_samples']}回\n")
            f.write(f"- **3桁の期待出現回数**: {expected_3digit:.2f}回（各3桁の組み合わせが均等に出現する場合）\n")
            f.write(f"- **2桁の期待出現回数**: {expected_2digit:.2f}回（各2桁の組み合わせが均等に出現する場合）\n")
            
            # 判定基準の説明
            if stats['total_samples'] < 100:
                threshold_desc = "期待値の3倍以上、かつ最低3回以上"
            elif stats['total_samples'] < 500:
                threshold_desc = "期待値の2.5倍以上、かつ最低5回以上"
            else:
                threshold_desc = "期待値の2倍以上、かつ最低10回以上"
            
            f.write(f"- **統計的に有意な組み合わせの判定基準**: {threshold_desc}\n")
            f.write(f"  （サンプル数に応じて基準を調整しています）\n")
            f.write(f"- **統計的に有意な3桁の組み合わせ**: {len(stats['significant_combinations_3digit'])}件\n")
            f.write(f"- **統計的に有意な2桁の組み合わせ**: \n")
            f.write(f"  - 百の位・十の位: {len(stats['significant_combinations_hundred_tens'])}件\n")
            f.write(f"  - 十の位・一の位: {len(stats['significant_combinations_tens_ones'])}件\n")
            f.write(f"  - 百の位・一の位: {len(stats['significant_combinations_hundred_ones'])}件\n\n")
            
            # 3桁の統計的に有意な組み合わせ
            if stats['significant_combinations_3digit']:
                f.write(f"#### 3桁の統計的に有意な組み合わせ（期待値の2倍以上）\n\n")
                f.write(f"| 組み合わせ | 出現回数 | 出現率（全体） | 期待値比 |\n")
                f.write(f"|-----------|----------|----------------|----------|\n")
                for sig_combo in stats['significant_combinations_3digit'][:15]:
                    f.write(f"| {sig_combo['combination']} | {sig_combo['count']}回 | {sig_combo['rate']:.2f}% | {sig_combo['ratio']:.2f}倍 |\n")
                f.write(f"\n")
            
            # 2桁の統計的に有意な組み合わせ
            if stats['significant_combinations_hundred_tens']:
                f.write(f"#### 百の位・十の位の統計的に有意な組み合わせ\n\n")
                f.write(f"| 組み合わせ | 出現回数 | 出現率（全体） | 出現率（条件付き） | 期待値比 |\n")
                f.write(f"|-----------|----------|----------------|-------------------|----------|\n")
                f.write(f"**出現率（全体）**: 全サンプル数に対する出現率\n")
                f.write(f"**出現率（条件付き）**: 百の位がXのときの出現率（例：百の位が0のとき、次に十の位が何が出たか）\n\n")
                for sig_combo in stats['significant_combinations_hundred_tens'][:15]:
                    f.write(f"| {sig_combo['combination']} | {sig_combo['count']}回 | {sig_combo['rate_overall']:.2f}% | {sig_combo['rate_conditional']:.2f}% | {sig_combo['ratio']:.2f}倍 |\n")
                f.write(f"\n")
            
            if stats['significant_combinations_tens_ones']:
                f.write(f"#### 十の位・一の位の統計的に有意な組み合わせ\n\n")
                f.write(f"| 組み合わせ | 出現回数 | 出現率（全体） | 出現率（条件付き） | 期待値比 |\n")
                f.write(f"|-----------|----------|----------------|-------------------|----------|\n")
                f.write(f"**出現率（全体）**: 全サンプル数に対する出現率\n")
                f.write(f"**出現率（条件付き）**: 十の位がXのときの出現率（例：十の位が0のとき、次に一の位が何が出たか）\n\n")
                for sig_combo in stats['significant_combinations_tens_ones'][:15]:
                    f.write(f"| {sig_combo['combination']} | {sig_combo['count']}回 | {sig_combo['rate_overall']:.2f}% | {sig_combo['rate_conditional']:.2f}% | {sig_combo['ratio']:.2f}倍 |\n")
                f.write(f"\n")
            
            if stats['significant_combinations_hundred_ones']:
                f.write(f"#### 百の位・一の位の統計的に有意な組み合わせ\n\n")
                f.write(f"| 組み合わせ | 出現回数 | 出現率（全体） | 出現率（条件付き） | 期待値比 |\n")
                f.write(f"|-----------|----------|----------------|-------------------|----------|\n")
                f.write(f"**出現率（全体）**: 全サンプル数に対する出現率\n")
                f.write(f"**出現率（条件付き）**: 百の位がXのときの出現率（例：百の位が0のとき、一の位が何が出たか）\n\n")
                for sig_combo in stats['significant_combinations_hundred_ones'][:15]:
                    f.write(f"| {sig_combo['combination']} | {sig_combo['count']}回 | {sig_combo['rate_overall']:.2f}% | {sig_combo['rate_conditional']:.2f}% | {sig_combo['ratio']:.2f}倍 |\n")
                f.write(f"\n")
            
            # 統計的コメント
            f.write(f"#### 統計的知見\n\n")
            top_combo = combo_list[0] if combo_list else None
            if top_combo:
                top_rate = (top_combo[1] / stats['total_samples']) * 100 if stats['total_samples'] > 0 else 0.0
                top_ratio = top_combo[1] / expected_3digit if expected_3digit > 0 else 0.0
                f.write(f"1. **最も出現頻度が高い3桁の組み合わせ**: {top_combo[0]}（{top_combo[1]}回、{top_rate:.2f}%、期待値の{top_ratio:.2f}倍）\n")
            
            if stats['significant_combinations_3digit']:
                f.write(f"2. **3桁の統計的に有意な組み合わせ**: {len(stats['significant_combinations_3digit'])}件の組み合わせが統計的に有意な基準を満たしています。\n")
                f.write(f"   ただし、サンプル数が少ない場合（特に100回未満）は、統計的な信頼性が低いことに注意が必要です。\n")
                f.write(f"   これは、ランダムな出現とは異なる何らかの傾向がある可能性を示唆していますが、\n")
                f.write(f"   より多くのサンプルでの検証が必要です。\n")
            
            if stats['significant_combinations_hundred_tens'] or stats['significant_combinations_tens_ones'] or stats['significant_combinations_hundred_ones']:
                f.write(f"3. **2桁の組み合わせの傾向**: \n")
                if stats['significant_combinations_hundred_tens']:
                    f.write(f"   - 百の位・十の位: {len(stats['significant_combinations_hundred_tens'])}件の組み合わせが統計的に有意です。\n")
                if stats['significant_combinations_tens_ones']:
                    f.write(f"   - 十の位・一の位: {len(stats['significant_combinations_tens_ones'])}件の組み合わせが統計的に有意です。\n")
                if stats['significant_combinations_hundred_ones']:
                    f.write(f"   - 百の位・一の位: {len(stats['significant_combinations_hundred_ones'])}件の組み合わせが統計的に有意です。\n")
                f.write(f"   - 条件付き出現率は、特定の桁がXのときの次の桁の出現傾向を示しています。\n")
            
            # 各桁位置での傾向
            f.write(f"4. **各桁位置での傾向**: \n")
            f.write(f"   - 百の位、十の位、一の位それぞれで出現頻度の高い数字が存在します。\n")
            f.write(f"   - これらの組み合わせが特定のパターンを形成している可能性があります。\n")
            
            f.write(f"5. **注意事項**: \n")
            f.write(f"   - 統計的に有意な組み合わせが存在しても、これは過去のデータに基づく傾向であり、\n")
            f.write(f"     将来の出現を保証するものではありません。\n")
            f.write(f"   - ナンバーズ3は抽選によるランダムな結果であり、過去の傾向が将来も続くとは限りません。\n")
            f.write(f"\n")
        
        f.write(f"## 時系列・周期性分析\n\n")
        f.write(f"### 曜日別統計\n\n")
        f.write(f"| 曜日 | 回数 | 割合 |\n")
        f.write(f"|------|------|------|\n")
        weekday_total = sum(time_series['weekday_counts'].values())
        for weekday in ['月', '火', '水', '木', '金', '土', '日']:
            count = time_series['weekday_counts'].get(weekday, 0)
            if weekday_total > 0:
                rate = (count / weekday_total) * 100
            else:
                rate = 0.0
            f.write(f"| {weekday} | {count}回 | {rate:.2f}% |\n")
        f.write(f"\n")
        
        f.write(f"### 月別統計\n\n")
        f.write(f"| 月 | 回数 | 割合 |\n")
        f.write(f"|----|------|------|\n")
        month_total = sum(time_series['month_counts'].values())
        for month in range(1, 13):
            count = time_series['month_counts'].get(month, 0)
            if month_total > 0:
                rate = (count / month_total) * 100
            else:
                rate = 0.0
            f.write(f"| {month}月 | {count}回 | {rate:.2f}% |\n")
        f.write(f"\n")
        
        f.write(f"### 季節別統計\n\n")
        f.write(f"| 季節 | 回数 | 割合 |\n")
        f.write(f"|------|------|------|\n")
        season_total = sum(time_series['season_counts'].values())
        for season in ['春', '夏', '秋', '冬']:
            count = time_series['season_counts'].get(season, 0)
            if season_total > 0:
                rate = (count / season_total) * 100
            else:
                rate = 0.0
            f.write(f"| {season} | {count}回 | {rate:.2f}% |\n")
        f.write(f"\n")
        
        f.write(f"## 備考\n\n")
        f.write(f"- 極CUBEはN3のみ、1パターンのみで生成\n")
        f.write(f"- つながり統計は、すべての数字が極CUBE内に見つかった場合のみカウント\n")
        f.write(f"- 分析対象回数は、前回・前々回のデータが存在する回号のみ\n")
    
    logger.info(f"Markdown形式でレポートを保存しました: {md_path}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='極CUBE全期間基礎集計スクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--start-round',
        type=int,
        help='開始回号（未指定の場合は最新回から500回分さかのぼる）'
    )
    
    parser.add_argument(
        '--end-round',
        type=int,
        help='終了回号（未指定の場合は最新回）'
    )
    
    parser.add_argument(
        '--num-rounds',
        type=int,
        default=500,
        help='分析回数（デフォルト: 500回）'
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default=str(PROJECT_ROOT / 'data'),
        help='データディレクトリ（デフォルト: data）'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='出力ディレクトリ（デフォルト: data/analysis_results/02_extreme_cube/02-01_全期間基礎集計）'
    )
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = OUTPUT_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # データ読み込み
        logger.info("データを読み込んでいます...")
        df = load_past_results(data_dir)
        keisen_master = load_keisen_master(data_dir)
        logger.info(f"データ読み込み完了（{len(df)}回分）")
        
        # 回号範囲を決定
        if args.end_round:
            end_round = args.end_round
        else:
            end_round = int(df['round_number'].max())
        
        if args.start_round:
            start_round = args.start_round
        else:
            start_round = max(3, end_round - args.num_rounds + 1)
        
        logger.info(f"分析範囲: {start_round}回 - {end_round}回（{end_round - start_round + 1}回分）")
        
        # 分析を実施
        result = analyze_extreme_cube_base_stats(
            df, keisen_master, start_round, end_round
        )
        
        # 結果を出力
        save_results(result, output_dir)
        
        # 結果サマリーを表示
        print("\n=== 分析結果サマリー ===")
        print(f"分析期間: {result['analysis_period']['start_round']}回 - {result['analysis_period']['end_round']}回")
        print(f"総回数: {result['analysis_period']['total_rounds']}回")
        print(f"極CUBE内出現回数: {result['cube_appearance_stats']['all_digits_found_count']}回")
        print(f"極CUBE内出現率: {result['cube_appearance_stats']['all_digits_found_rate']:.2f}%")
        print(f"\nつながり統計:")
        for conn_type, count in result['cube_appearance_stats']['connection_stats'].items():
            print(f"  {conn_type}: {count}回")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

