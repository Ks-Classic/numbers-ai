"""
予測表生成アルゴリズム（Python実装）

TypeScriptの実装（src/lib/chart-generator/index.ts）を参考に、
Pythonで予測表生成ロジックを実装します。
"""

from typing import List, Optional, Tuple, Literal
import json
from pathlib import Path
import numpy as np
import pandas as pd

Pattern = Literal['A1', 'A2', 'B1', 'B2']
Target = Literal['n3', 'n4']
ColumnName = Literal['百の位', '十の位', '一の位'] | Literal['千の位', '百の位', '十の位', '一の位']


class ChartGenerationError(Exception):
    """予測表生成時のエラー"""
    pass


def load_keisen_master(data_dir: Path) -> dict:
    """罫線マスターデータを読み込む"""
    keisen_path = data_dir / 'keisen_master.json'
    
    if not keisen_path.exists():
        raise ChartGenerationError(f"罫線マスターファイルが見つかりません: {keisen_path}")
    
    with open(keisen_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_predicted_digits(
    keisen_master: dict,
    target: Target,
    column_name: ColumnName,
    previous_digit: int,
    previous_previous_digit: int
) -> List[int]:
    """指定された条件で予測出目を取得
    
    Args:
        keisen_master: 罫線マスターデータ
        target: 'n3' または 'n4'
        column_name: 桁名（例: '百の位'）
        previous_digit: 前回の数字（0-9）
        previous_previous_digit: 前々回の数字（0-9）
    
    Returns:
        予測出目の配列
    """
    # 入力値の検証
    if not (0 <= previous_digit <= 9 and isinstance(previous_digit, int)):
        raise ChartGenerationError(f"前回の数字が不正です: {previous_digit}")
    
    if not (0 <= previous_previous_digit <= 9 and isinstance(previous_previous_digit, int)):
        raise ChartGenerationError(f"前々回の数字が不正です: {previous_previous_digit}")
    
    target_data = keisen_master.get(target)
    if not target_data:
        raise ChartGenerationError(f"{target}データが見つかりません")
    
    column_data = target_data.get(column_name)
    if not column_data:
        raise ChartGenerationError(f"{target}の{column_name}データが見つかりません")
    
    # JSONの構造: 外側のキーが前々回、内側のキーが前回
    previous_previous_map = column_data.get(str(previous_previous_digit))
    if not previous_previous_map:
        raise ChartGenerationError(
            f"{target}の{column_name}で前々回'{previous_previous_digit}'のデータが見つかりません"
        )
    
    predicted_digits = previous_previous_map.get(str(previous_digit))
    if not isinstance(predicted_digits, list):
        raise ChartGenerationError(
            f"{target}の{column_name}で前々回'{previous_previous_digit}'、前回'{previous_digit}'の予測出目が見つかりません"
        )
    
    return predicted_digits


def extract_predicted_digits(
    df: pd.DataFrame,
    keisen_master: dict,
    round_number: int,
    target: Target
) -> List[int]:
    """予測出目を抽出する
    
    前回（round_number-1）と前々回（round_number-2）の当選番号から、
    keisen_master.jsonを参照して各桁の予測出目を取得し、結合する。
    """
    # 前回と前々回のデータを取得
    previous_row = df[df['round_number'] == round_number - 1]
    previous_previous_row = df[df['round_number'] == round_number - 2]
    
    if len(previous_row) == 0:
        raise ChartGenerationError(f"前回の当選番号が見つかりません（回号: {round_number - 1}）")
    
    if len(previous_previous_row) == 0:
        raise ChartGenerationError(f"前々回の当選番号が見つかりません（回号: {round_number - 2}）")
    
    # 対象に応じた桁名と当選番号を取得
    if target == 'n3':
        column_names: List[ColumnName] = ['百の位', '十の位', '一の位']
        previous_winning = str(previous_row['n3_winning'].iloc[0])
        previous_previous_winning = str(previous_previous_row['n3_winning'].iloc[0])
        expected_length = 3
    else:
        column_names: List[ColumnName] = ['千の位', '百の位', '十の位', '一の位']
        previous_winning = str(previous_row['n4_winning'].iloc[0])
        previous_previous_winning = str(previous_previous_row['n4_winning'].iloc[0])
        expected_length = 4
    
    # 数値型の場合に備えて、'.0'を除去
    previous_winning = previous_winning.replace('.0', '')
    previous_previous_winning = previous_previous_winning.replace('.0', '')
    
    # 先頭の0が欠落している場合（例: 013 → 13）を補正
    # 数値として読み込まれた場合、先頭の0が失われる可能性がある
    if len(previous_winning) < expected_length:
        previous_winning = previous_winning.zfill(expected_length)
    if len(previous_previous_winning) < expected_length:
        previous_previous_winning = previous_previous_winning.zfill(expected_length)
    
    # 各桁の予測出目を取得して結合
    source_list: List[int] = []
    
    for i, column_name in enumerate(column_names):
        # 前回・前々回の該当桁の数字を取得
        previous_digit = int(previous_winning[i])
        previous_previous_digit = int(previous_previous_winning[i])
        
        # 予測出目を取得
        predicted_digits = get_predicted_digits(
            keisen_master,
            target,
            column_name,
            previous_digit,
            previous_previous_digit
        )
        
        # source_listに追加
        source_list.extend(predicted_digits)
    
    # 昇順ソート
    source_list.sort()
    
    return source_list


def apply_pattern_expansion(source_list: List[int], pattern: Pattern) -> List[int]:
    """パターン別の元数字リストを作成する
    
    Args:
        source_list: 予測出目の配列
        pattern: パターン（'A1' | 'A2' | 'B1' | 'B2'）
    
    Returns:
        拡張後の元数字リスト
    """
    nums = source_list.copy()
    
    # A1/A2: 欠番補足あり（0〜9全追加）
    # B1/B2: 欠番補足なし（0のみ追加）
    if pattern in ['A1', 'A2']:
        # パターンA1/A2: 0〜9の欠番をすべて追加
        for digit in range(10):
            if digit not in nums:
                nums.append(digit)
    else:
        # パターンB1/B2: 0が含まれていなければ0を1つ追加
        if 0 not in nums:
            nums.append(0)
    
    # 昇順ソート（重複は許容）
    nums.sort()
    
    return nums


def build_main_rows(nums: List[int]) -> List[List[int]]:
    """メイン行を組み立てる
    
    仕様: docs/design/表作成ルール.,md の「4. メイン行の組み立て（vFinal 4.1）」
    
    Args:
        nums: 元数字リスト
    
    Returns:
        メイン行の配列（各行は1〜4要素）
    """
    main_rows: List[List[int]] = []
    temp_list = nums.copy()
    
    while len(temp_list) > 0:
        # ユニーク値を昇順で取得
        unique_digits = sorted(list(set(temp_list)))
        
        if len(unique_digits) >= 4:
            # 4種類以上の場合: 最初の4種類を構成メンバーとして使用
            members = unique_digits[:4]
            new_row: List[int] = []
            
            # tempListから順に取り出してnewRowに格納
            for member in members:
                idx = temp_list.index(member)
                new_row.append(temp_list[idx])
                temp_list.pop(idx)
            
            main_rows.append(new_row)
        else:
            # 4種類未満の場合: ユニーク値のみを使用（最大値を繰り返し追加しない）
            # 余りマスは apply_main_row_remaining_copy で補完される
            new_row = unique_digits.copy()
            
            # tempListから使用した数字を削除（重複を考慮）
            for digit in new_row:
                if digit in temp_list:
                    temp_list.remove(digit)
            
            main_rows.append(new_row)
    
    if len(main_rows) == 0:
        raise ChartGenerationError('メイン行が1本も生成されませんでした')
    
    return main_rows


def initialize_grid(rows: int, cols: int, main_rows: List[List[int]]) -> List[List[Optional[int]]]:
    """グリッドを初期化し、メイン行を配置する
    
    メイン行は奇数行（1, 3, 5, 7行目）に配置する。
    列は奇数列（1, 3, 5, 7列目）に配置する。
    実装・表示・配列すべて1-indexedで統一（配列のインデックス1から使用、grid[0]は未使用）。
    
    Args:
        rows: 行数（1-indexedでの行数）
        cols: 列数（常に8）
        main_rows: メイン行の配列
    
    Returns:
        初期化されたグリッド（2次元配列、1-indexed）
    """
    # 2次元配列を初期化（初期値None）
    # 配列のサイズは rows + 1（grid[0]は未使用、grid[1]からgrid[rows]を使用）
    grid: List[List[Optional[int]]] = [
        [None] * (cols + 1) for _ in range(rows + 1)
    ]
    
    # メイン行を配置（奇数行の奇数列に配置: 1, 3, 5, 7行目の1, 3, 5, 7列目）
    for i, main_row in enumerate(main_rows):
        row_num = i * 2 + 1  # 奇数行（1, 3, 5, 7行目）
        
        # 最後のメイン行の下に必ず裏数字を配置する行が存在することを確認
        if row_num + 1 > rows:
            raise ChartGenerationError(
                f"メイン行配置エラー: 行{row_num}にメイン行を配置するためには、行{row_num + 1}が必要です（現在の行数: {rows}行）"
            )
        
        # メイン行の要素数分だけ配置（最大4要素）
        for j in range(min(len(main_row), 4)):
            col_num = j * 2 + 1  # 奇数列（1, 3, 5, 7列目）
            grid[row_num][col_num] = main_row[j]
    
    return grid


def apply_main_row_remaining_copy(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> None:
    """メイン行配置後の余りマスルールを適用する
    
    裏数字ルール適用前に、メイン行配置後の余ったマス（空のマス）に対して、
    その上のメイン行（奇数行）の同じ列の数字をコピーする。
    """
    def has_main_row(row: int) -> bool:
        """奇数行の奇数列（1, 3, 5, 7列目）に数字が入っているかチェック"""
        for col in range(1, cols + 1, 2):
            if grid[row][col] is not None:
                return True
        return False
    
    # 奇数行の奇数列（1, 3, 5, 7列目）を処理
    for row in range(1, rows + 1, 2):
        if not has_main_row(row):
            continue
        
        # 奇数列（1, 3, 5, 7列目）が空の場合、その上のメイン行の数字をコピー
        for col in range(1, cols + 1, 2):
            if grid[row][col] is None and row > 1:
                # 上のメイン行（1つ前の奇数行）を探す
                prev_main_row = row - 2
                while prev_main_row >= 1 and not has_main_row(prev_main_row):
                    prev_main_row -= 2
                
                # 上のメイン行が見つかり、その列に数字がある場合、コピー
                if prev_main_row >= 1 and grid[prev_main_row][col] is not None:
                    grid[row][col] = grid[prev_main_row][col]
    
    # 奇数行の偶数列（2, 4, 6, 8列目）を処理
    for row in range(1, rows + 1, 2):
        if not has_main_row(row):
            continue
        
        # 偶数列（2, 4, 6, 8列目）が空の場合、その上のメイン行の数字をコピー
        for col in range(2, cols + 1, 2):
            if grid[row][col] is None and row > 1:
                # 上のメイン行（1つ前の奇数行）を探す
                prev_main_row = row - 2
                while prev_main_row >= 1 and not has_main_row(prev_main_row):
                    prev_main_row -= 2
                
                if prev_main_row >= 1 and grid[prev_main_row][col] is not None:
                    grid[row][col] = grid[prev_main_row][col]


def place_center_zero(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> bool:
    """パターンA2/B2の中心0配置
    
    中心マス群を (row昇順, col昇順) で走査し、
    最初に見つかる空白マスに0を1つ配置する。
    
    Args:
        grid: グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed、常に8）
    
    Returns:
        0が配置されたかどうか
    """
    # 中心行・列を計算（1-indexed）
    center_rows = [
        (rows + 1) // 2,
        (rows + 2) // 2
    ]
    center_cols = [
        (cols + 1) // 2,
        (cols + 2) // 2
    ]
    
    # 中心マス群を走査（配列のインデックス1から使用）
    for r in center_rows:
        for c in center_cols:
            if grid[r][c] is None:
                grid[r][c] = 0
                return True  # 1つ配置したら終了
    
    return False  # 配置できなかった（すでにすべて埋まっていた）


def inverse(n: int) -> int:
    """裏数字を計算する
    
    Args:
        n: 数字（0-9）
    
    Returns:
        裏数字（(n + 5) % 10）
    """
    return (n + 5) % 10


def apply_vertical_inverse(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> None:
    """裏数字ルール（縦パス）を適用する
    
    上から下へ順に処理し、nullかつ上に値がある場合に裏数字を配置する。
    更新がなくなるまで繰り返す。
    """
    updated = True
    
    while updated:
        updated = False
        
        # 行1から開始（1-indexed）
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                if grid[row][col] is None and row > 1 and grid[row - 1][col] is not None:
                    grid[row][col] = inverse(grid[row - 1][col])
                    updated = True


def apply_horizontal_inverse(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> None:
    """裏数字ルール（横パス）を適用する
    
    左から右へ順に処理し、nullかつ左に値がある場合に裏数字を配置する。
    更新がなくなるまで繰り返す。
    """
    updated = True
    
    while updated:
        updated = False
        
        # 行1から開始（1-indexed）
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                if grid[row][col] is None and col > 1 and grid[row][col - 1] is not None:
                    grid[row][col] = inverse(grid[row][col - 1])
                    updated = True


def apply_remaining_copy(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> None:
    """余りマスルールを適用する
    
    裏数字ルール適用後も空のマスに対して、上から値をコピーする。
    更新がなくなるまで繰り返す。
    """
    updated = True
    
    while updated:
        updated = False
        
        # 行1から開始（1-indexed）
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                if grid[row][col] is None and row > 1 and grid[row - 1][col] is not None:
                    grid[row][col] = grid[row - 1][col]
                    updated = True


def generate_chart(
    df: pd.DataFrame,
    keisen_master: dict,
    round_number: int,
    pattern: Pattern,
    target: Target
) -> Tuple[List[List[Optional[int]]], int, int]:
    """予測表を生成する
    
    Args:
        df: 過去当選番号データ（DataFrame）
        keisen_master: 罫線マスターデータ
        round_number: 回号
        pattern: パターン（'A1' | 'A2' | 'B1' | 'B2'）
        target: 対象（'n3' または 'n4'）
    
    Returns:
        (grid, rows, cols) のタプル
    """
    try:
        # ステップ1: 予測出目の抽出
        source_list = extract_predicted_digits(df, keisen_master, round_number, target)
        
        # ステップ2: パターン別の元数字リスト作成
        nums = apply_pattern_expansion(source_list, pattern)
        
        # ステップ3: メイン行の組み立て
        main_rows = build_main_rows(nums)
        
        # ステップ4: グリッド初期配置
        rows = len(main_rows) * 2  # メイン行N本の場合、2*N行必要
        cols = 8
        grid = initialize_grid(rows, cols, main_rows)
        
        # ステップ5: メイン行配置後の余りマスルール（裏数字適用前）
        apply_main_row_remaining_copy(grid, rows, cols)
        
        # ステップ5.5: パターンA2/B2中心0配置
        if pattern in ['A2', 'B2']:
            place_center_zero(grid, rows, cols)
        
        # ステップ6-8: 裏数字・余りマスルール
        apply_vertical_inverse(grid, rows, cols)
        apply_horizontal_inverse(grid, rows, cols)
        apply_remaining_copy(grid, rows, cols)
        
        return grid, rows, cols
    
    except Exception as e:
        if isinstance(e, ChartGenerationError):
            raise
        raise ChartGenerationError(f"予測表生成エラー: {str(e)}") from e

