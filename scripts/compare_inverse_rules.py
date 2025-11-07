"""通常CUBEと極CUBEの裏数字ルールの違いを具体的に比較"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / 'notebooks'))

from chart_generator import load_keisen_master, extract_predicted_digits, apply_pattern_expansion, build_main_rows
import pandas as pd

def print_grid_simple(grid, rows, cols, title=""):
    """グリッドを簡潔に表示"""
    if title:
        print(f"\n{title}")
        print("-" * 60)
    
    for row in range(1, min(rows + 1, 6)):  # 5行目まで表示
        print(f"行{row}: ", end="")
        for col in range(1, cols + 1):
            val = grid[row][col]
            if val is None:
                print(" .", end=" ")
            else:
                print(f"{val:2d}", end=" ")
        print()

def apply_extreme_inverse_rows(grid, rows, cols):
    """極CUBE専用の裏数字ルール"""
    def inverse(n):
        return (n + 5) % 10
    
    # ステップ1: メイン行（奇数行）の偶数列に左列の裏数字を配置
    for row in range(1, rows + 1, 2):
        for col in range(2, cols + 1, 2):
            if grid[row][col] is None:
                left_col = col - 1
                val_left = grid[row][left_col]
                if val_left is not None:
                    grid[row][col] = inverse(val_left)
    
    # ステップ2: 偶数行が上の行の裏数字を取る
    for row in range(2, rows + 1, 2):
        for col in range(1, cols + 1):
            if grid[row][col] is None:
                val_above = grid[row - 1][col]
                if val_above is not None:
                    grid[row][col] = inverse(val_above)

def apply_normal_inverse_rows(grid, rows, cols):
    """通常CUBEの裏数字ルール（縦パス→横パス）"""
    def inverse(n):
        return (n + 5) % 10
    
    # 縦パス（収束まで）
    updated = True
    iteration = 0
    while updated:
        updated = False
        iteration += 1
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                if grid[row][col] is None and row > 1 and grid[row - 1][col] is not None:
                    grid[row][col] = inverse(grid[row - 1][col])
                    updated = True
    
    # 横パス（収束まで）
    updated = True
    iteration = 0
    while updated:
        updated = False
        iteration += 1
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                if grid[row][col] is None and col > 1 and grid[row][col - 1] is not None:
                    grid[row][col] = inverse(grid[row][col - 1])
                    updated = True

def compare_inverse_rules(df, keisen_master, round_number):
    """通常CUBEと極CUBEの裏数字ルールを比較"""
    
    # データ準備
    source_list = extract_predicted_digits(df, keisen_master, round_number, 'n3')
    nums = apply_pattern_expansion(source_list, 'B1')
    main_rows = build_main_rows(nums)
    
    # 極CUBEは最大3本まで
    if len(main_rows) > 3:
        remaining_digits = []
        for i in range(3, len(main_rows)):
            remaining_digits.extend(main_rows[i])
        if remaining_digits:
            main_rows[2].extend(remaining_digits)
        main_rows = main_rows[:3]
    
    rows = min(len(main_rows) * 2, 5)
    cols = 8
    
    # グリッド1: 極CUBE専用の裏数字ルール
    grid_extreme = [[None] * (cols + 1) for _ in range(rows + 1)]
    for i, main_row in enumerate(main_rows):
        row = i * 2 + 1
        for j, val in enumerate(main_row):
            col = j * 2 + 1
            if col <= cols:
                grid_extreme[row][col] = val
    
    # グリッド初期配置時の余りマスを0で埋める
    for row in range(1, rows + 1, 2):
        for col in range(1, cols + 1, 2):
            if grid_extreme[row][col] is None:
                grid_extreme[row][col] = 0
    
    print_grid_simple(grid_extreme, rows, cols, f"【回号{round_number}】メイン行配置後（0埋め後）")
    
    apply_extreme_inverse_rows(grid_extreme, rows, cols)
    
    # グリッド2: 通常CUBEの裏数字ルール
    grid_normal = [[None] * (cols + 1) for _ in range(rows + 1)]
    for i, main_row in enumerate(main_rows):
        row = i * 2 + 1
        for j, val in enumerate(main_row):
            col = j * 2 + 1
            if col <= cols:
                grid_normal[row][col] = val
    
    # グリッド初期配置時の余りマスを0で埋める
    for row in range(1, rows + 1, 2):
        for col in range(1, cols + 1, 2):
            if grid_normal[row][col] is None:
                grid_normal[row][col] = 0
    
    apply_normal_inverse_rows(grid_normal, rows, cols)
    
    # 比較
    print(f"\n{'='*60}")
    print(f"回号: {round_number} - 裏数字ルール適用後の比較")
    print('='*60)
    
    print_grid_simple(grid_extreme, rows, cols, "極CUBE専用の裏数字ルール適用後")
    print_grid_simple(grid_normal, rows, cols, "通常CUBEの裏数字ルール適用後")
    
    # 差分を確認
    print("\n【差分確認】")
    diff_count = 0
    diff_details = []
    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            val_extreme = grid_extreme[row][col]
            val_normal = grid_normal[row][col]
            if val_extreme != val_normal:
                diff_details.append(f"  行{row}列{col}: 極CUBE={val_extreme}, 通常CUBE={val_normal}")
                diff_count += 1
    
    if diff_count == 0:
        print("  → すべて同じ値です（裏数字ルールの実装方法が異なっても結果は同じ）")
    else:
        print(f"  → {diff_count}箇所で値が異なります:")
        for detail in diff_details:
            print(detail)
    
    return diff_count > 0

if __name__ == "__main__":
    data_dir = PROJECT_ROOT / 'data'
    df = pd.read_csv(data_dir / 'past_results.csv')
    keisen_master = load_keisen_master(data_dir)
    
    # 複数の回号でテスト（10回分）
    available_rounds = sorted(df['round_number'].unique())
    test_rounds = available_rounds[:10]  # 最初の10回分
    
    print(f"\n{'='*60}")
    print(f"テスト対象: {len(test_rounds)}回分")
    print(f"回号: {test_rounds}")
    print('='*60)
    
    found_diff = False
    diff_rounds = []
    
    for round_number in test_rounds:
        try:
            has_diff = compare_inverse_rules(df, keisen_master, round_number)
            if has_diff:
                found_diff = True
                diff_rounds.append(round_number)
                print("\n" + "="*60)
                print(f"違いが見つかりました（回号{round_number}）。次の回号も確認します...")
                print("="*60)
        except Exception as e:
            print(f"\nエラー（回号{round_number}）: {e}")
            continue
    
    print("\n" + "="*60)
    print("【最終結果】")
    print("="*60)
    if not found_diff:
        print(f"✅ すべての回号（{len(test_rounds)}回分）で結果が同じでした。")
        print("裏数字ルールの実装方法が異なっても、最終的な結果は同じになります。")
    else:
        print(f"❌ {len(diff_rounds)}回分で違いが見つかりました:")
        for r in diff_rounds:
            print(f"  - 回号{r}")
    print("="*60)

