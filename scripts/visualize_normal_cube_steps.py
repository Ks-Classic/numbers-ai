"""通常CUBE生成の各ステップを可視化（A1～B2の全パターン）"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / 'notebooks'))

from chart_generator import (
    load_keisen_master,
    generate_chart,
    extract_predicted_digits,
    apply_pattern_expansion,
    build_main_rows,
    apply_vertical_inverse,
    apply_horizontal_inverse,
    apply_main_row_remaining_copy,
    place_center_zero,
    apply_remaining_copy
)
import pandas as pd
from typing import List, Optional, Literal

Pattern = Literal['A1', 'A2', 'B1', 'B2']
Target = Literal['n3', 'n4']

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

def visualize_normal_cube_steps(
    df: pd.DataFrame,
    keisen_master: dict,
    round_number: int,
    pattern: Pattern,
    target: Target
):
    """通常CUBE生成の各ステップを可視化"""
    
    print(f"\n{'#'*70}")
    print(f"通常CUBE生成プロセス - 回号: {round_number}, パターン: {pattern}, 対象: {target}")
    print('#'*70)
    
    # ステップ1: 予測出目の抽出
    source_list = extract_predicted_digits(df, keisen_master, round_number, target)
    print(f"\n【ステップ1】予測出目の抽出")
    print(f"  source_list: {source_list}")
    
    # ステップ2: パターン別の元数字リスト作成
    nums = apply_pattern_expansion(source_list, pattern)
    print(f"\n【ステップ2】パターン別の元数字リスト作成（{pattern}パターン）")
    print(f"  nums: {nums}")
    
    pattern_desc = {
        'A1': '欠番補足あり（0-9すべて）',
        'A2': '欠番補足あり（0-9すべて）+ 中心0配置',
        'B1': '欠番補足なし（0も含めて補足しない）',
        'B2': '欠番補足なし（0も含めて補足しない）+ 中心0配置'
    }
    print(f"  → {pattern}パターン: {pattern_desc[pattern]}")
    
    # ステップ3: メイン行の組み立て
    main_rows = build_main_rows(nums)
    print(f"\n【ステップ3】メイン行の組み立て")
    for i, row in enumerate(main_rows):
        print(f"  メイン行{i}: {row}")
    print(f"  → メイン行数: {len(main_rows)}本")
    
    # ステップ4: グリッド初期配置
    rows = len(main_rows) * 2  # メイン行N本の場合、2*N行必要
    cols = 8
    grid = [[None] * (cols + 1) for _ in range(rows + 1)]  # 1-indexed
    
    # メイン行を奇数行の奇数列に配置
    for i, main_row in enumerate(main_rows):
        row = i * 2 + 1  # 1, 3, 5, 7行目...
        for j, val in enumerate(main_row):
            col = j * 2 + 1  # 1, 3, 5, 7列目
            if col <= cols:
                grid[row][col] = val
    
    print_grid(grid, rows, cols, f"【ステップ4】グリッド初期配置（メイン行を奇数行の奇数列に配置）")
    print(f"  → 行数: {rows}行（メイン行{len(main_rows)}本 × 2）")
    
    # ステップ5: メイン行配置後の余りマスルール（裏数字適用前）
    grid_before_remaining = [[row[:] for row in grid]]
    apply_main_row_remaining_copy(grid, rows, cols)
    
    # 変更があったか確認
    changed = False
    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            if grid[row][col] != grid_before_remaining[0][row][col]:
                changed = True
                break
        if changed:
            break
    
    if changed:
        print_grid(grid, rows, cols, "【ステップ5】メイン行配置後の余りマスルール適用後（裏数字適用前）")
        print("  → メイン行内で空いているマスを真上のマスからコピー")
    else:
        print(f"\n【ステップ5】メイン行配置後の余りマスルール適用後（裏数字適用前）")
        print("  → 変更なし（すべてのメイン行が埋まっています）")
    
    # ステップ5.5: パターンA2/B2中心0配置
    if pattern in ['A2', 'B2']:
        grid_before_center = [[row[:] for row in grid]]
        place_center_zero(grid, rows, cols)
        
        changed = False
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                if grid[row][col] != grid_before_center[0][row][col]:
                    changed = True
                    break
            if changed:
                break
        
        if changed:
            print_grid(grid, rows, cols, f"【ステップ5.5】中心0配置（{pattern}パターン固有）")
            print("  → 中心のマス（行中央、列中央）に0を配置")
        else:
            print(f"\n【ステップ5.5】中心0配置（{pattern}パターン固有）")
            print("  → 変更なし（中心マスは既に埋まっています）")
    
    # ステップ6: 裏数字ルール（縦パス）
    print(f"\n【ステップ6】裏数字ルール適用（縦パス）")
    print("  → 上から下へ順に処理し、nullかつ上に値がある場合に裏数字を配置")
    
    grid_before_vertical = [[row[:] for row in grid]]
    apply_vertical_inverse(grid, rows, cols)
    
    changed = False
    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            if grid[row][col] != grid_before_vertical[0][row][col]:
                changed = True
                break
        if changed:
            break
    
    if changed:
        print_grid(grid, rows, cols, "  縦パス適用後（上から下へ裏数字を配置）")
    else:
        print("  → 変更なし")
    
    # ステップ7: 裏数字ルール（横パス）
    print(f"\n【ステップ7】裏数字ルール適用（横パス）")
    print("  → 左から右へ順に処理し、nullかつ左に値がある場合に裏数字を配置")
    
    grid_before_horizontal = [[row[:] for row in grid]]
    apply_horizontal_inverse(grid, rows, cols)
    
    changed = False
    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            if grid[row][col] != grid_before_horizontal[0][row][col]:
                changed = True
                break
        if changed:
            break
    
    if changed:
        print_grid(grid, rows, cols, "  横パス適用後（左から右へ裏数字を配置）")
    else:
        print("  → 変更なし")
    
    # ステップ8: 余りマスルール（真上のマスをコピー）
    print(f"\n【ステップ8】余りマスルール適用（真上のマスをコピー）")
    print("  → 空いているマスを真上のマスからコピー（収束まで繰り返し）")
    
    grid_before_remaining = [[row[:] for row in grid]]
    apply_remaining_copy(grid, rows, cols)
    
    changed = False
    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            if grid[row][col] != grid_before_remaining[0][row][col]:
                changed = True
                break
        if changed:
            break
    
    if changed:
        print_grid(grid, rows, cols, "  余りマスルール適用後")
    else:
        print("  → 変更なし（すべてのマスが埋まっています）")
    
    print_grid(grid, rows, cols, f"【最終結果】通常CUBE（{pattern}パターン、{target}対象）")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='通常CUBE生成の各ステップを可視化')
    parser.add_argument('--round', type=int, default=100, help='回号（デフォルト: 100）')
    parser.add_argument('--pattern', type=str, choices=['A1', 'A2', 'B1', 'B2'], 
                       help='パターン（A1/A2/B1/B2）。指定しない場合は全パターン表示')
    parser.add_argument('--target', type=str, choices=['n3', 'n4'], default='n3',
                       help='対象（n3/n4、デフォルト: n3）')
    parser.add_argument('--all-patterns', action='store_true',
                       help='全パターン（A1, A2, B1, B2）を表示')
    args = parser.parse_args()
    
    # データ読み込み
    data_dir = PROJECT_ROOT / 'data'
    df = pd.read_csv(data_dir / 'past_results.csv')
    keisen_master = load_keisen_master(data_dir)
    
    # パターンの決定
    if args.all_patterns:
        patterns = ['A1', 'A2', 'B1', 'B2']
    elif args.pattern:
        patterns = [args.pattern]
    else:
        patterns = ['A1', 'A2', 'B1', 'B2']  # デフォルトは全パターン
    
    # 各パターンで可視化
    for pattern in patterns:
        visualize_normal_cube_steps(df, keisen_master, args.round, pattern, args.target)
        print("\n" + "="*70 + "\n")

