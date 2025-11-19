"""通常CUBE生成の各ステップを可視化（A1～B2の全パターン）"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートのパスを設定
# scripts/tools/visualization/ から見て、プロジェクトルートは parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'core'))

# デバッグ: パス確認
import os
if not os.path.exists(str(PROJECT_ROOT / 'core' / 'chart_generator.py')):
    print(f"ERROR: chart_generator.py not found")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"Core path: {PROJECT_ROOT / 'core'}")
    print(f"Core exists: {os.path.exists(str(PROJECT_ROOT / 'core'))}")
    print(f"Chart generator path: {PROJECT_ROOT / 'core' / 'chart_generator.py'}")
    print(f"Chart generator exists: {os.path.exists(str(PROJECT_ROOT / 'core' / 'chart_generator.py'))}")
    sys.exit(1)

from chart_generator import (
    load_keisen_master,
    generate_chart
)
import pandas as pd
from typing import List, Optional, Literal, Dict, Any
import copy

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
    
    # 各ステップの状態を保存
    step_states: Dict[str, Any] = {}
    previous_grids: Dict[str, List[List[Optional[int]]]] = {}
    
    # コールバック関数を定義
    def step1_callback(source_list):
        step_states['step1'] = source_list
        print(f"\n【ステップ1】予測出目の抽出")
        print(f"  source_list: {source_list}")
    
    def step2_callback(nums, pattern):
        step_states['step2'] = nums
        print(f"\n【ステップ2】パターン別の元数字リスト作成（{pattern}パターン）")
        print(f"  nums: {nums}")
        pattern_desc = {
            'A1': '欠番補足あり（0-9すべて）',
            'A2': '欠番補足あり（0-9すべて）+ 中心0配置',
            'B1': '欠番補足なし（0も含めて補足しない）',
            'B2': '欠番補足なし（0も含めて補足しない）+ 中心0配置'
        }
        print(f"  → {pattern}パターン: {pattern_desc[pattern]}")
    
    def step3_callback(main_rows):
        step_states['step3'] = main_rows
        print(f"\n【ステップ3】メイン行の組み立て")
        for i, row in enumerate(main_rows):
            print(f"  メイン行{i}: {row}")
        print(f"  → メイン行数: {len(main_rows)}本")
    
    def step4_callback(grid, rows, cols):
        step_states['step4'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        print_grid(grid, rows, cols, f"【ステップ4】グリッド初期配置（メイン行を奇数行の奇数列に配置）")
        print(f"  → 行数: {rows}行（メイン行{len(step_states['step3'])}本 × 2）")
        previous_grids['step4'] = copy.deepcopy(grid)
    
    def step5_callback(grid, rows, cols):
        step_states['step5'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        # 変更があったか確認
        changed = False
        if 'step4' in previous_grids:
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    if grid[row][col] != previous_grids['step4'][row][col]:
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
        previous_grids['step5'] = copy.deepcopy(grid)
    
    def step5_5_callback(grid, rows, cols):
        step_states['step5_5'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        # 変更があったか確認
        changed = False
        if 'step5' in previous_grids:
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    if grid[row][col] != previous_grids['step5'][row][col]:
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
        previous_grids['step5_5'] = copy.deepcopy(grid)
    
    def step6_callback(grid, rows, cols):
        step_states['step6'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        print(f"\n【ステップ6】裏数字ルール適用（縦パス）")
        print("  → 上から下へ順に処理し、nullかつ上に値がある場合に裏数字を配置")
        
        # 変更があったか確認
        changed = False
        prev_grid = previous_grids.get('step5_5') or previous_grids.get('step5')
        if prev_grid:
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    if grid[row][col] != prev_grid[row][col]:
                        changed = True
                        break
                if changed:
                    break
        
        if changed:
            print_grid(grid, rows, cols, "  縦パス適用後（上から下へ裏数字を配置）")
        else:
            print("  → 変更なし")
        previous_grids['step6'] = copy.deepcopy(grid)
    
    def step7_callback(grid, rows, cols):
        step_states['step7'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        print(f"\n【ステップ7】裏数字ルール適用（横パス）")
        print("  → 左から右へ順に処理し、nullかつ左に値がある場合に裏数字を配置")
        
        # 変更があったか確認
        changed = False
        if 'step6' in previous_grids:
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    if grid[row][col] != previous_grids['step6'][row][col]:
                        changed = True
                        break
                if changed:
                    break
        
        if changed:
            print_grid(grid, rows, cols, "  横パス適用後（左から右へ裏数字を配置）")
        else:
            print("  → 変更なし")
    
    # コールバックを設定してgenerate_chart()を呼び出す
    step_callbacks = {
        'step1': step1_callback,
        'step2': step2_callback,
        'step3': step3_callback,
        'step4': step4_callback,
        'step5': step5_callback,
        'step6': step6_callback,
        'step7': step7_callback
    }
    
    if pattern in ['A2', 'B2']:
        step_callbacks['step5_5'] = step5_5_callback
    
    # メイン関数を呼び出してCUBEを生成（コールバックで各ステップを可視化）
    grid, rows, cols = generate_chart(
        df, keisen_master, round_number, pattern, target,
        step_callbacks=step_callbacks
    )
    
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

