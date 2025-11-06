#!/usr/bin/env python3
"""
複数の回号・パターンのデータを一括生成するスクリプト

使用方法:
    python3 generate_batch_visualization_data.py [回号リスト] [パターンリスト]
    
例:
    python3 generate_batch_visualization_data.py 6849,6800,6900 A1,A2,B1,B2
"""
import pandas as pd
import numpy as np
import sys
import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
sys.path.append(str(PROJECT_ROOT / 'notebooks'))

from chart_generator import load_keisen_master, generate_chart
from feature_extractor import (
    get_digit_positions,
    get_rehearsal_positions,
    calculate_rehearsal_distance,
    calculate_overlap_count,
    calculate_inverse_ratio
)

def generate_visualization_data(round_number, pattern, target='n3'):
    """指定回号・パターンのデータを生成"""
    DATA_DIR = PROJECT_ROOT / 'data'
    train_csv_path = DATA_DIR / 'train_data_from_4801.csv'
    train_df = pd.read_csv(train_csv_path)
    
    # 指定回号のデータを取得
    if round_number not in train_df['round_number'].values:
        return None
    
    row = train_df[train_df['round_number'] == round_number].iloc[0]
    
    # リハーサル数字が存在するかチェック
    if pd.isna(row[f'{target}_rehearsal']) or str(row[f'{target}_rehearsal']) == 'NULL' or str(row[f'{target}_rehearsal']) == 'nan':
        return None
    
    # 罫線マスターデータの読み込み
    keisen_master = load_keisen_master(DATA_DIR)
    
    # 予測表を生成
    rehearsal_digits = str(row[f'{target}_rehearsal']).replace('.0', '').zfill(3)
    winning_digits = str(row[f'{target}_winning']).replace('.0', '').zfill(3)
    
    grid, rows, cols = generate_chart(train_df, keisen_master, round_number, pattern, target)
    
    # リハーサル数字と当選番号の位置を取得
    rehearsal_positions = get_rehearsal_positions(grid, rows, cols, rehearsal_digits)
    winning_positions = get_rehearsal_positions(grid, rows, cols, winning_digits)
    
    # グリッドをシリアライズ可能な形式に変換
    grid_serializable = []
    for r in range(rows):
        grid_serializable.append([])
        for c in range(cols):
            val = grid[r][c]
            grid_serializable[r].append(int(val) if val is not None else None)
    
    # 各数字の特徴量を計算
    feature_results = []
    for digit in range(10):
        digit_positions = get_digit_positions(grid, rows, cols, digit)
        
        if len(digit_positions) == 0:
            continue
        
        rehearsal_dist = calculate_rehearsal_distance(digit_positions, rehearsal_positions)
        overlap = calculate_overlap_count(digit_positions, rehearsal_positions)
        inverse_ratio = calculate_inverse_ratio(digit_positions, rehearsal_positions, grid)
        
        is_winning = str(digit) in winning_digits
        is_rehearsal = str(digit) in rehearsal_digits
        
        feature_results.append({
            'digit': int(digit),
            'positions_count': len(digit_positions),
            'rehearsal_distance': float(rehearsal_dist),
            'overlap_count': int(overlap),
            'inverse_ratio': float(inverse_ratio),
            'is_winning': bool(is_winning),
            'is_rehearsal': bool(is_rehearsal)
        })
    
    return {
        'round_number': int(round_number),
        'target': target,
        'pattern': pattern,
        'rehearsal_digits': rehearsal_digits,
        'winning_digits': winning_digits,
        'rehearsal_positions': [[int(p[0]), int(p[1])] for p in rehearsal_positions],
        'winning_positions': [[int(p[0]), int(p[1])] for p in winning_positions],
        'feature_results': feature_results,
        'grid': grid_serializable,
        'grid_size': {'rows': int(rows), 'cols': int(cols)}
    }

def main():
    parser = argparse.ArgumentParser(description='複数の回号・パターンのデータを一括生成')
    parser.add_argument('--rounds', type=str, default=None,
                        help='対象回号のカンマ区切りリスト（例: 6849,6800,6900）。指定しない場合は6000回以降の全回号を生成')
    parser.add_argument('--start-round', type=int, default=6000,
                        help='開始回号（--rounds未指定時、デフォルト: 6000）')
    parser.add_argument('--end-round', type=int, default=None,
                        help='終了回号（--rounds未指定時、指定しない場合は最新回まで）')
    parser.add_argument('--patterns', type=str, default='A1,A2,B1,B2',
                        help='パターンのカンマ区切りリスト（デフォルト: A1,A2,B1,B2）')
    parser.add_argument('--target', type=str, default='n3', choices=['n3', 'n4'],
                        help='対象（デフォルト: n3）')
    args = parser.parse_args()
    
    # データの読み込み（利用可能な回号範囲を取得）
    DATA_DIR = PROJECT_ROOT / 'data'
    train_csv_path = DATA_DIR / 'train_data_from_4801.csv'
    train_df = pd.read_csv(train_csv_path)
    
    if args.rounds:
        round_numbers = [int(r.strip()) for r in args.rounds.split(',')]
    else:
        # 6000回以降の全回号を生成
        available_rounds = sorted(train_df['round_number'].unique())
        start_idx = 0
        for i, r in enumerate(available_rounds):
            if r >= args.start_round:
                start_idx = i
                break
        
        if args.end_round:
            round_numbers = [r for r in available_rounds[start_idx:] if r <= args.end_round]
        else:
            round_numbers = available_rounds[start_idx:]
        
        print(f"利用可能な回号範囲: {available_rounds[0]} - {available_rounds[-1]}")
        print(f"生成対象回号数: {len(round_numbers)}件（{args.start_round}回以降）")
    
    patterns = [p.strip() for p in args.patterns.split(',')]
    
    all_data = {}
    success_count = 0
    fail_count = 0
    
    for round_number in round_numbers:
        all_data[round_number] = {}
        for pattern in patterns:
            print(f"生成中: 回号{round_number}, パターン{pattern}...", end=' ')
            data = generate_visualization_data(round_number, pattern, args.target)
            if data:
                all_data[round_number][pattern] = data
                success_count += 1
                print("✓")
            else:
                fail_count += 1
                print("✗ (データなし)")
    
    # JSONファイルとして保存
    output_file = PROJECT_ROOT / 'docs' / 'report' / f'visualization_data_{args.target}.json'
    
    # 既存のデータがあれば読み込んでマージ
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            # 新しいデータで上書き（既存データを保持）
            for round_num, patterns_data in all_data.items():
                if round_num not in existing_data:
                    existing_data[round_num] = {}
                existing_data[round_num].update(patterns_data)
            all_data = existing_data
            print(f"\n既存データにマージしました。")
        except Exception as e:
            print(f"\n既存データの読み込みに失敗しました。新規作成します: {e}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nデータを保存しました: {output_file}")
    print(f"生成されたデータ数: {success_count}件（失敗: {fail_count}件）")
    print(f"総データ数: {sum(len(patterns) for patterns in all_data.values())}件")

if __name__ == '__main__':
    main()

