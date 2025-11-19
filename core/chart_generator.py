"""
予測表生成アルゴリズム（Python実装）

TypeScriptの実装（src/lib/chart-generator/index.ts）を参考に、
Pythonで予測表生成ロジックを実装します。
"""

from typing import List, Optional, Tuple, Literal, Callable, Dict, Any
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
    
    # ソートしない（桁順を保持：百の位→十の位→一の位の順）
    
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
    # B1/B2: 欠番補足なし（0も含めて、すべて欠番補足しない）
    if pattern in ['A1', 'A2']:
        # パターンA1/A2: 0〜9の欠番をすべて追加
        for digit in range(10):
            if digit not in nums:
                nums.append(digit)
    # B1/B2の場合は何も追加しない（source_listをそのまま使用）
    
    # 昇順ソート（重複は許容）
    nums.sort()
    
    return nums


def build_main_rows(nums: List[int]) -> Tuple[List[List[int]], List[int]]:
    """メイン行を組み立てる
    
    仕様: 各メイン行に必ず4つまで数字を入れる
    - 最後のメイン行以外は必ず4つ
    - 最後のメイン行だけは残りの数字をすべて入れる（4つ未満でもOK）
    - tempListは最小値順にソート済み（4桁単位で最小値から順に選択するため）
    - 4桁単位で最小値から順に重複せずに選択（連続していなくても良い、例：0,1,2,5）
    - 4桁埋めたら次の最小値から繰り返し
    - 4桁埋まらなかったら、次の未消費の最小値から埋めていく
    - tempListは事前に並べ替え済みなので、メイン行作成時は先頭から順に取るだけ
    - 行をまたぐ連続は許容（前の行の最後と次の行の最初が同じでもOK）
    - 元数字リストに存在する数分だけ使用可能（同じ数字が複数回出現する場合は、その分だけ使用）
    
    Args:
        nums: 元数字リスト（ソート済み）
    
    Returns:
        (メイン行の配列, temp_list) のタプル
    """
    import os
    DEBUG = os.environ.get('DEBUG_CHART', 'false').lower() == 'true'
    
    main_rows: List[List[int]] = []
    # tempListを「4桁単位で最小値から順に重複せずに選択」のルールで並べ替え
    temp_list = []
    remaining = nums.copy()
    
    # 4桁単位で処理
    while len(remaining) > 0:
        chunk = []
        # 重複しない最小値から順に選ぶ
        unique_elements = sorted(list(set(remaining)))
        for digit in unique_elements:
            if len(chunk) < 4 and digit in remaining:
                chunk.append(digit)
                remaining.remove(digit)
        
        # 4桁に満たない場合、残りから最小値から順に埋める（重複してもOK）
        # 「最小値から順に」は0～9まで重複せずに順番に埋めていく（連続していなくてもOK）
        if len(chunk) < 4 and len(remaining) > 0:
            while len(chunk) < 4 and len(remaining) > 0:
                # chunkの最後の数字を取得（なければ-1）
                last_digit = chunk[-1] if chunk else -1
                # 最後の数字の次の最小値（0～9の順序で）を残りから選ぶ
                # 残りにlast_digitより大きい数字がある場合は、その中から最小値を選ぶ
                # 残りにlast_digitより大きい数字がない場合は、残りから最小値を選ぶ
                candidates = [d for d in remaining if d > last_digit]
                if candidates:
                    next_digit = min(candidates)
                else:
                    # last_digitより大きい数字がない場合は、残りから最小値を選ぶ
                    next_digit = min(remaining)
                chunk.append(next_digit)
                remaining.remove(next_digit)
        
        temp_list.extend(chunk)
    
    # temp_listのコピーを保存（メイン行組み立てで消費されるため）
    original_temp_list = temp_list.copy()
    
    row_index = 0
    
    if DEBUG:
        print('[build_main_rows] ========================================')
        print(f'[build_main_rows] 開始: nums = {nums}')
        print(f'[build_main_rows] 初期 temp_list = {temp_list.copy()}')
    
    while len(temp_list) > 0:
        new_row: List[int] = []
        
        # 最後のメイン行かどうかを判定（残りの数字が4つ以下なら最後の行）
        is_last_row = len(temp_list) <= 4
        target_count = len(temp_list) if is_last_row else 4
        
        # tempListは最小値順にソート済み
        # 4桁単位で最小値から順に重複せずに選択（連続していなくても良い、例：0,1,2,5）
        # 4桁埋めたら次の最小値から繰り返し
        # 4桁埋まらなかったら、次の未消費の最小値から埋めていく
        # tempListは事前に並べ替え済みなので、先頭から順に取るだけ
        
        if DEBUG:
            print(f'[build_main_rows] ----------------------------------------')
            print(f'[build_main_rows] 【行{row_index}の処理開始】')
            print(f'[build_main_rows] temp_list = {temp_list.copy()}')
            print(f'[build_main_rows] is_last_row = {is_last_row}, target_count = {target_count}')
        
        # tempListの先頭から順に取るだけ（既にソート済み）
        new_row = temp_list[:target_count]
        temp_list = temp_list[target_count:]
        
        if DEBUG:
            print(f'[build_main_rows]   ✓ 数字{new_row}を選択（先頭から{target_count}個）')
            print(f'[build_main_rows]   残りのtemp_list = {temp_list.copy()}')
        
        if DEBUG:
            print(f'[build_main_rows] 【行{row_index}の処理完了】')
            print(f'[build_main_rows] 完成したnew_row = {new_row}')
            print(f'[build_main_rows] 残りのtemp_list = {temp_list.copy()}')
        
        main_rows.append(new_row)
        row_index += 1
    
    if DEBUG:
        print('[build_main_rows] ========================================')
        print('[build_main_rows] 最終結果:')
        for idx, row in enumerate(main_rows):
            print(f'[build_main_rows]   行{idx}: {row}')
    
    if len(main_rows) == 0:
        raise ChartGenerationError('メイン行が1本も生成されませんでした')
    
    return main_rows, original_temp_list


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
) -> Optional[Tuple[int, int]]:
    """パターンA2/B2の中心0配置
    
    行数に応じて対角線上に0を配置する。
    
    - 6行: 4行5列目
    - 8行: 5行5列目
    - 10行: 6行6列目
    - 12行: 7行7列目
    
    Args:
        grid: グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed、常に8）
    
    Returns:
        0が配置された位置 (row, col) のタプル、配置されなかった場合はNone
    """
    # 行数に応じて対角線上の位置を決定
    if rows == 6:
        center_row = 4
        center_col = 5
    elif rows == 8:
        center_row = 5
        center_col = 5
    elif rows == 10:
        center_row = 6
        center_col = 6
    elif rows == 12:
        center_row = 7
        center_col = 7
    else:
        # その他の行数の場合は従来のロジック（後方互換性のため）
        if rows >= 10:
            center_row = 6
        elif rows >= 4:
            center_row = 4
        else:
            center_row = rows
        
        # 中心列を計算（1-indexed）
        center_cols = [
            (cols + 1) // 2,  # 4列目
            (cols + 2) // 2   # 5列目
        ]
        
        # 中心行の中心列を走査（列昇順）
        for c in center_cols:
            if grid[center_row][c] is None:
                grid[center_row][c] = 0
                return (center_row, c)  # 配置した位置を返す
        
        return None  # 配置できなかった（すでにすべて埋まっていた）
    
    # 対角線上の位置に0を配置
    if grid[center_row][center_col] is None:
        grid[center_row][center_col] = 0
        return (center_row, center_col)  # 配置した位置を返す
    
    return None  # 配置できなかった（すでに埋まっていた）


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
    cols: int,
    center_zero_pos: Optional[Tuple[int, int]] = None
) -> None:
    """裏数字ルール（縦パス）を適用する
    
    上から下へ順に処理し、nullかつ上に値がある場合に裏数字を配置する。
    更新がなくなるまで繰り返す。
    
    Args:
        grid: グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        center_zero_pos: 中心0配置の位置 (row, col)、Noneの場合は通常通り処理
    """
    updated = True
    
    while updated:
        updated = False
        
        # 行1から開始（1-indexed）
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                # 中心0配置で追加した0の下には裏数字を入れない
                if center_zero_pos is not None:
                    center_row, center_col = center_zero_pos
                    if col == center_col and row > center_row and grid[center_row][center_col] == 0:
                        continue
                
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
    target: Target,
    step_callbacks: Optional[Dict[str, Callable]] = None
) -> Tuple[List[List[Optional[int]]], int, int]:
    """予測表を生成する
    
    Args:
        df: 過去当選番号データ（DataFrame）
        keisen_master: 罫線マスターデータ
        round_number: 回号
        pattern: パターン（'A1' | 'A2' | 'B1' | 'B2'）
        target: 対象（'n3' または 'n4'）
        step_callbacks: 各ステップで呼び出されるコールバック関数の辞書
            - 'step1': source_listを受け取る
            - 'step2': numsを受け取る
            - 'step3': main_rowsを受け取る
            - 'step4': grid, rows, colsを受け取る
            - 'step5': grid, rows, colsを受け取る
            - 'step5_5': grid, rows, colsを受け取る（A2/B2のみ）
            - 'step6': grid, rows, colsを受け取る（縦パス後）
            - 'step7': grid, rows, colsを受け取る（横パス後）
    
    Returns:
        (grid, rows, cols) のタプル
    """
    if step_callbacks is None:
        step_callbacks = {}
    
    try:
        # ステップ1: 予測出目の抽出
        source_list = extract_predicted_digits(df, keisen_master, round_number, target)
        if 'step1' in step_callbacks:
            step_callbacks['step1'](source_list)
        
        # ステップ2: パターン別の元数字リスト作成
        nums = apply_pattern_expansion(source_list, pattern)
        if 'step2' in step_callbacks:
            step_callbacks['step2'](nums, pattern)
        
        # ステップ3: メイン行の組み立て
        main_rows, temp_list = build_main_rows(nums)
        if 'step3' in step_callbacks:
            step_callbacks['step3'](main_rows)
        
        # ステップ4: グリッド初期配置
        rows = len(main_rows) * 2  # メイン行N本の場合、2*N行必要
        cols = 8
        grid = initialize_grid(rows, cols, main_rows)
        if 'step4' in step_callbacks:
            step_callbacks['step4'](grid, rows, cols)
        
        # ステップ5: メイン行配置後の余りマスルール（裏数字適用前）
        apply_main_row_remaining_copy(grid, rows, cols)
        if 'step5' in step_callbacks:
            step_callbacks['step5'](grid, rows, cols)
        
        # ステップ5.5: パターンA2/B2中心0配置
        # 注意: 6行の場合は中心0配置を実行せず、最終調整のみを実行する
        center_zero_pos = None
        if pattern in ['A2', 'B2'] and rows != 6:
            center_zero_pos = place_center_zero(grid, rows, cols)
            if 'step5_5' in step_callbacks:
                step_callbacks['step5_5'](grid, rows, cols)
        
        # ステップ6-7: 裏数字ルール
        apply_vertical_inverse(grid, rows, cols, center_zero_pos)
        if 'step6' in step_callbacks:
            step_callbacks['step6'](grid, rows, cols)
        
        apply_horizontal_inverse(grid, rows, cols)
        if 'step7' in step_callbacks:
            step_callbacks['step7'](grid, rows, cols)
        
        # ステップ8: 8行を超える場合は9行以降を削除して8行にする
        if rows > 8 and cols == 8:
            # 9行目以降を削除（grid[0]は未使用、grid[1]からgrid[8]までを保持）
            grid = grid[:9]  # grid[0]からgrid[8]まで（1-8行目）
            rows = 8
        
        # ステップ9: 8列×8行の場合の最終調整（0配置パターンのみ）
        if rows == 8 and cols == 8 and pattern in ['A2', 'B2']:
            # 5列5行目を0に強制置き換え
            grid[5][5] = 0
            # 5列4行目を5に強制置き換え
            grid[4][5] = 5
        
        # ステップ10: 8列×6行の場合の最終調整（0配置パターンのみ）
        if rows == 6 and cols == 8 and pattern in ['A2', 'B2']:
            # 5列4行目を0に強制置き換え
            grid[4][5] = 0
            # 5列3行目を5に強制置き換え
            grid[3][5] = 5
        
        return grid, rows, cols
    
    except Exception as e:
        if isinstance(e, ChartGenerationError):
            raise
        raise ChartGenerationError(f"予測表生成エラー: {str(e)}") from e

