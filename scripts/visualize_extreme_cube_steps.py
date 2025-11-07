"""極CUBE生成の各ステップを可視化"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / 'notebooks'))

from chart_generator import (
    load_keisen_master,
    extract_predicted_digits,
    apply_pattern_expansion,
    build_main_rows,
    apply_vertical_inverse,
    apply_horizontal_inverse
)
import pandas as pd
import json

def print_grid(grid, rows, cols, title=""):
    """グリッドをアスキーアートで表示"""
    if title:
        print(f"\n{'='*70}")
        print(f"{title}")
        print('='*70)
    
    print("      ", end="")
    for col in range(1, cols + 1):
        print(f"列{col:2d} ", end="")
    print()
    
    for row in range(1, rows + 1):
        print(f"行{row}: ", end="")
        for col in range(1, cols + 1):
            val = grid[row][col]
            if val is None:
                print("  . ", end="")
            else:
                print(f" {val:2d} ", end="")
        print()

def visualize_extreme_cube_steps(df, keisen_master, round_number):
    """極CUBE生成の各ステップを可視化"""
    
    print(f"\n{'#'*70}")
    print(f"極CUBE生成プロセス - 回号: {round_number}")
    print('#'*70)
    
    # ステップ1: 予測出目の抽出
    source_list = extract_predicted_digits(df, keisen_master, round_number, 'n3')
    print(f"\n【ステップ1】予測出目の抽出")
    print(f"  source_list: {source_list}")
    
    # ステップ2: パターン別の元数字リスト作成（B1: 欠番補足なし）
    nums = apply_pattern_expansion(source_list, 'B1')
    print(f"\n【ステップ2】パターン別の元数字リスト作成（B1パターン）")
    print(f"  nums: {nums}")
    print(f"  → B1パターン: 欠番補足なし（0も含めて補足しない）")
    
    # ステップ3: メイン行の組み立て
    main_rows = build_main_rows(nums)
    print(f"\n【ステップ3】メイン行の組み立て")
    for i, row in enumerate(main_rows):
        print(f"  メイン行{i}: {row}")
    
    # 極CUBEは最大3本のメイン行まで
    if len(main_rows) > 3:
        print(f"  → メイン行が{len(main_rows)}本ありますが、極CUBEは最大3本まで")
        # 4本目以降の数字を3本目に統合
        remaining_digits = []
        for i in range(3, len(main_rows)):
            remaining_digits.extend(main_rows[i])
        if remaining_digits:
            print(f"  → 4本目以降の数字 {remaining_digits} を3本目に統合します")
            main_rows[2].extend(remaining_digits)
        main_rows = main_rows[:3]
        print(f"  → 使用するメイン行数: {len(main_rows)}本")
    
    # ステップ4: グリッド初期配置
    rows = min(len(main_rows) * 2, 5)  # 最大5行まで
    cols = 8
    grid = [[None] * (cols + 1) for _ in range(rows + 1)]  # 1-indexed
    
    # メイン行を奇数行の奇数列に配置
    for i, main_row in enumerate(main_rows):
        row = i * 2 + 1  # 1, 3, 5行目
        for j, val in enumerate(main_row):
            col = j * 2 + 1  # 1, 3, 5, 7列目
            if col <= cols:
                grid[row][col] = val
    
    print_grid(grid, rows, cols, "【ステップ4】グリッド初期配置（メイン行を奇数行の奇数列に配置）")
    
    # ステップ5: グリッド初期配置時の余りマスを0で埋める（極CUBE固有）
    # メイン行配置後、裏数字適用前に実行
    # 対象: 奇数行（メイン行）の奇数列（1, 3, 5, 7列目）で空いているマス
    for row in range(1, rows + 1, 2):  # 奇数行（1, 3, 5行目）
        for col in range(1, cols + 1, 2):  # 奇数列（1, 3, 5, 7列目）
            if grid[row][col] is None:
                grid[row][col] = 0
    
    print_grid(grid, rows, cols, "【ステップ5】グリッド初期配置時の余りマスを0で埋めた後（極CUBE固有）")
    print("  → 奇数行（メイン行）の奇数列（1, 3, 5, 7列目）で空いているマスを0で埋める")
    
    # ステップ6: 裏数字ルール（通常CUBEと同じロジックを再利用）
    print(f"\n【ステップ6】裏数字ルール適用")
    print("  → 通常CUBEの裏数字ルールを適用（縦パス→横パス）")
    print("  → 極CUBEの5行目までの範囲では、メイン行（奇数行）の偶数列と偶数行（2,4行目）に裏数字が配置される")
    
    apply_vertical_inverse(grid, rows, cols)
    print_grid(grid, rows, cols, "  縦パス適用後（上から下へ裏数字を配置）")
    
    apply_horizontal_inverse(grid, rows, cols)
    print_grid(grid, rows, cols, "  横パス適用後（左から右へ裏数字を配置）")
    
    # ステップ7: 5行目の余りマスを0で埋める
    if rows >= 5:
        empty_before = sum(1 for col in range(1, cols + 1) if grid[5][col] is None)
        if empty_before > 0:
            print(f"\n【ステップ7】5行目の余りマスを0で埋める（極CUBE固有）")
            print(f"  → 5行目に{empty_before}個の空マスがあります")
            for col in range(1, cols + 1):
                if grid[5][col] is None:
                    grid[5][col] = 0
            print_grid(grid, rows, cols, "  5行目の余りマスを0で埋めた後")
        else:
            print(f"\n【ステップ7】5行目の余りマスを0で埋める（極CUBE固有）")
            print(f"  → 5行目に空マスはありません（すべて裏数字ルールで埋められています）")
    
    print_grid(grid, rows, cols, "【最終結果】極CUBE")
    
    # 最終的な5行目を確認
    if rows >= 5:
        print("\n最終的な5行目:")
        for col in range(1, cols + 1):
            print(f"  列{col}: {grid[5][col]}", end="  ")
        print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='極CUBE生成の各ステップを可視化')
    parser.add_argument('--round', type=int, default=100, help='回号（デフォルト: 100）')
    args = parser.parse_args()
    
    # データ読み込み
    data_dir = PROJECT_ROOT / 'data'
    df = pd.read_csv(data_dir / 'past_results.csv')
    keisen_master = load_keisen_master(data_dir)
    
    # 指定された回号で可視化
    visualize_extreme_cube_steps(df, keisen_master, args.round)

