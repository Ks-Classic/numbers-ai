"""極CUBE生成の各ステップを可視化"""

import sys
from pathlib import Path

# プロジェクトルートのパスを設定
# scripts/tools/visualization/ から見て、プロジェクトルートは parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'core'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

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

from chart_generator import load_keisen_master, build_main_rows
from generate_extreme_cube import generate_extreme_cube
import pandas as pd
import copy
from typing import Dict, Any, List, Optional

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
    
    # 各ステップの状態を保存
    step_states: Dict[str, Any] = {}
    previous_grids: Dict[str, List[List[Optional[int]]]] = {}
    
    # コールバック関数を定義
    def step1_callback(source_list):
        step_states['step1'] = source_list
        print(f"\n【ステップ1】予測出目の抽出")
        print(f"  source_list: {source_list}")
    
    def step2_callback(nums):
        step_states['step2'] = nums
        print(f"\n【ステップ2】パターン別の元数字リスト作成（B1パターン）")
        print(f"  nums: {nums}")
        print(f"  → B1パターン: 欠番補足なし（0も含めて補足しない）")
    
    def step3_callback(main_rows):
        step_states['step3'] = main_rows
        # temp_listを取得（step2のnumsから）
        _, temp_list = build_main_rows(step_states['step2'])
        step_states['temp_list'] = temp_list
        print(f"\n【ステップ3】メイン行の組み立て")
        print(f"  tempList: {temp_list}")
        for i, row in enumerate(main_rows):
            print(f"  メイン行{i}: {row}")
    
    def step3_5_callback(main_rows):
        step_states['step3_5'] = main_rows
        if len(step_states['step3']) > 3:
            print(f"  → メイン行が{len(step_states['step3'])}本ありますが、極CUBEは最大3本まで")
            remaining_digits = []
            for i in range(3, len(step_states['step3'])):
                remaining_digits.extend(step_states['step3'][i])
            if remaining_digits:
                print(f"  → 4本目以降の数字 {remaining_digits} を3本目に統合します")
            print(f"  → 使用するメイン行数: {len(main_rows)}本")
    
    def step4_callback(grid, rows, cols):
        step_states['step4'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        print_grid(grid, rows, cols, "【ステップ4】グリッド初期配置（メイン行を奇数行の奇数列に配置）")
        previous_grids['step4'] = copy.deepcopy(grid)
    
    def step5_callback(grid, rows, cols):
        step_states['step5'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        print_grid(grid, rows, cols, "【ステップ5】グリッド初期配置時の余りマスを0で埋めた後（極CUBE固有）")
        print("  → 奇数行（メイン行）の奇数列（1, 3, 5, 7列目）で空いているマスを0で埋める")
        previous_grids['step5'] = copy.deepcopy(grid)
    
    def step6_callback(grid, rows, cols):
        step_states['step6'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        print(f"\n【ステップ6】裏数字ルール適用")
        print("  → 通常CUBEの裏数字ルールを適用（縦パス→横パス）")
        print("  → 極CUBEの5行目までの範囲では、メイン行（奇数行）の偶数列と偶数行（2,4行目）に裏数字が配置される")
        print_grid(grid, rows, cols, "  縦パス適用後（上から下へ裏数字を配置）")
        previous_grids['step6'] = copy.deepcopy(grid)
    
    def step7_callback(grid, rows, cols):
        step_states['step7'] = {'grid': copy.deepcopy(grid), 'rows': rows, 'cols': cols}
        print_grid(grid, rows, cols, "  横パス適用後（左から右へ裏数字を配置）")
    
    # コールバックを設定してgenerate_extreme_cube()を呼び出す
    step_callbacks = {
        'step1': step1_callback,
        'step2': step2_callback,
        'step3': step3_callback,
        'step3_5': step3_5_callback,
        'step4': step4_callback,
        'step5': step5_callback,
        'step6': step6_callback,
        'step7': step7_callback
    }
    
    # メイン関数を呼び出してCUBEを生成（コールバックで各ステップを可視化）
    grid, rows, cols = generate_extreme_cube(
        df, keisen_master, round_number,
        step_callbacks=step_callbacks
    )
    
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

