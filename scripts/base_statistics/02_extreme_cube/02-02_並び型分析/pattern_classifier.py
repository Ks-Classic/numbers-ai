"""
極CUBE並び型判定スクリプト

極CUBEの2,3,4行目における当選数字（N3の3桁）の並び型を判定する。
22種類の型に分類し、各回号について型を判定して結果を出力する。
"""

import sys
import argparse
import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Set, Union
from datetime import datetime
from collections import defaultdict

import pandas as pd

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


def get_winning_digits_positions(
    grid: List[List[Optional[int]]],
    winning_digits: List[int],
    target_rows: List[int] = [1, 2, 3, 4, 5],
    return_all_candidates: bool = False
) -> Union[List[Tuple[int, int]], Tuple[List[Tuple[int, int]], List[List[Tuple[int, int]]]]]:
    """極CUBEの1,2,3,4,5行目で当選数字の位置を取得する（つながりを形成できる組み合わせを探索）
    
    Args:
        grid: 極CUBEグリッド（0-indexed、row 0は空行）
        winning_digits: 当選数字のリスト（3桁、例：[1, 2, 3]）
        target_rows: 対象行（デフォルト: [1, 2, 3, 4, 5] = 実際の1,2,3,4,5行目、1-indexed）
        return_all_candidates: Trueの場合、各桁の全候補位置も返す
    
    Returns:
        return_all_candidates=False: 当選数字の位置リスト（(row, col)のタプル）
        return_all_candidates=True: (位置リスト, 各桁の全候補位置リスト)のタプル
    
    Note:
        - gridは0-indexed（row 0は空行、row 1が1行目、row 2が2行目...）
        - 同じ数字が複数の位置にある場合、つながりを形成できる組み合わせを探索
        - 1行目は罫線番号に対応する数字（0-9が順番に並ぶ）
    """
    from itertools import product
    
    # 各数字の候補位置を収集
    digit_positions = []
    for digit in winning_digits:
        candidates = []
        for row in target_rows:
            if row >= len(grid):
                continue
            for col in range(1, len(grid[row])):
                if grid[row][col] == digit:
                    candidates.append((row, col))
        digit_positions.append(candidates)
    
    # いずれかの数字が見つからない場合
    if any(len(candidates) == 0 for candidates in digit_positions):
        # 見つかった位置のみを返す（従来の動作）
        positions = []
        used_positions = set()
        for candidates in digit_positions:
            for pos in candidates:
                if pos not in used_positions:
                    positions.append(pos)
                    used_positions.add(pos)
                    break
        if return_all_candidates:
            return positions, digit_positions
        return positions
    
    # すべての組み合わせを探索して、つながりを形成できるものを探す
    for combo in product(*digit_positions):
        # 位置が重複していないかチェック
        if len(set(combo)) != 3:
            continue
        
        # つながりを形成できるかチェック
        positions = list(combo)
        if _check_connected(positions):
            if return_all_candidates:
                return positions, digit_positions
            return positions
    
    # つながりを形成できる組み合わせがない場合、最初の組み合わせを返す
    positions = []
    used_positions = set()
    for candidates in digit_positions:
        for pos in candidates:
            if pos not in used_positions:
                positions.append(pos)
                used_positions.add(pos)
                break
    if return_all_candidates:
        return positions, digit_positions
    return positions


def _check_connected(positions: List[Tuple[int, int]]) -> bool:
    """3つの位置がつながっているか簡易チェック（are_all_connectedの軽量版）"""
    if len(positions) != 3:
        return False
    
    def is_adj(p1, p2):
        row_diff = abs(p1[0] - p2[0])
        col_diff = abs(p1[1] - p2[1])
        return (row_diff <= 1 and col_diff <= 1 and (row_diff + col_diff) > 0 
                and row_diff <= 1 and col_diff <= 1)
    
    # 少なくとも2組がつながっている必要がある
    conn_01 = is_adj(positions[0], positions[1])
    conn_12 = is_adj(positions[1], positions[2])
    conn_02 = is_adj(positions[0], positions[2])
    
    return sum([conn_01, conn_12, conn_02]) >= 2


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
    
    # 横方向（同じ行で隣接する列）
    if row_diff == 0 and col_diff == 1:
        return True
    
    # 縦方向（同じ列で隣接する行）
    if col_diff == 0 and row_diff == 1:
        return True
    
    # 斜め方向（隣接する行・列）
    if row_diff == 1 and col_diff == 1:
        return True
    
    return False


def are_all_connected(positions: List[Tuple[int, int]]) -> bool:
    """3つの位置がすべてつながっているか判定する（グラフとして連結している）
    
    Args:
        positions: 位置リスト（3つの位置）
    
    Returns:
        すべてつながっている場合True（グラフとして連結している）
    
    Note:
        3つの位置が連結しているとは、任意の2つの位置の間に経路が存在すること。
        3つの位置A, B, Cについて：
        - A-B, B-C がつながっている → 連結（A-B-Cの経路）
        - A-B, A-C がつながっている → 連結（Aを中心にB, Cがつながっている）
        - A-B, B-C, A-C がすべてつながっている → 連結（完全グラフ）
        - A-B のみがつながっている → 非連結（Cが孤立）
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
        # すべてつながっていない
        return False
    elif connection_count == 1:
        # 1組のみつながっている → 孤立した位置がある
        return False
    else:
        # 2組以上つながっている → 連結している
        return True


def classify_position_zone(positions: List[Tuple[int, int]]) -> str:
    """当選数字の位置から区分（上部/中部/下部）を判定する
    
    分類ルール（排他的）:
    - 1行目を含む → 上部 (upper)
    - 5行目を含む → 下部 (lower)
    - 2,3,4行のみ → 中部 (middle)
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        区分名: "upper", "middle", "lower", または "unknown"
    """
    if len(positions) != 3:
        return "unknown"
    
    rows = set(p[0] for p in positions)
    
    # 1行目を含む → 上部
    if 1 in rows:
        return "upper"
    
    # 5行目を含む → 下部
    if 5 in rows:
        return "lower"
    
    # 2,3,4行のみ → 中部
    if rows.issubset({2, 3, 4}):
        return "middle"
    
    return "unknown"


def get_zone_display_name(zone: str) -> str:
    """区分の表示名を取得する"""
    zone_names = {
        "upper": "上部（1,2,3行目）",
        "middle": "中部（2,3,4行目）",
        "lower": "下部（3,4,5行目）",
        "unknown": "不明"
    }
    return zone_names.get(zone, zone)


def classify_direction(positions: List[Tuple[int, int]]) -> str:
    """百の位→十の位→一の位の方向を判定する
    
    Args:
        positions: 当選数字の位置リスト（[百の位, 十の位, 一の位]の順、各要素は(row, col)）
    
    Returns:
        方向を表す文字列:
        - "straight": 左→右 または 上→下（正方向）
        - "reverse": 右→左 または 下→上（逆方向）
        - "mixed": 混合（一方向に定まらない）
    """
    if len(positions) != 3:
        return "unknown"
    
    pos_100 = positions[0]  # 百の位
    pos_10 = positions[1]   # 十の位
    pos_1 = positions[2]    # 一の位
    
    # 行の変化
    row_diff_1 = pos_10[0] - pos_100[0]  # 百→十
    row_diff_2 = pos_1[0] - pos_10[0]    # 十→一
    
    # 列の変化
    col_diff_1 = pos_10[1] - pos_100[1]  # 百→十
    col_diff_2 = pos_1[1] - pos_10[1]    # 十→一
    
    # 行方向の判定
    row_direction = None
    if row_diff_1 >= 0 and row_diff_2 >= 0 and (row_diff_1 > 0 or row_diff_2 > 0):
        row_direction = "down"  # 上→下
    elif row_diff_1 <= 0 and row_diff_2 <= 0 and (row_diff_1 < 0 or row_diff_2 < 0):
        row_direction = "up"    # 下→上
    elif row_diff_1 == 0 and row_diff_2 == 0:
        row_direction = "same"  # 同じ行
    else:
        row_direction = "mixed"
    
    # 列方向の判定
    col_direction = None
    if col_diff_1 >= 0 and col_diff_2 >= 0 and (col_diff_1 > 0 or col_diff_2 > 0):
        col_direction = "right"  # 左→右
    elif col_diff_1 <= 0 and col_diff_2 <= 0 and (col_diff_1 < 0 or col_diff_2 < 0):
        col_direction = "left"   # 右→左
    elif col_diff_1 == 0 and col_diff_2 == 0:
        col_direction = "same"   # 同じ列
    else:
        col_direction = "mixed"
    
    # 総合判定
    # 正方向: 左→右 または 上→下
    if (col_direction == "right" and row_direction in ["same", "down"]) or \
       (col_direction == "same" and row_direction == "down") or \
       (col_direction == "right" and row_direction == "mixed"):
        return "straight"
    
    # 逆方向: 右→左 または 下→上
    if (col_direction == "left" and row_direction in ["same", "up"]) or \
       (col_direction == "same" and row_direction == "up") or \
       (col_direction == "left" and row_direction == "mixed"):
        return "reverse"
    
    # その他は混合
    return "mixed"


def normalize_positions_to_relative(positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """位置を相対座標に正規化する（並び型判定の汎用化用）
    
    最小行を0として相対化することで、どの区分でも同じ判定ロジックを適用可能にする。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        相対化された位置リスト（最小行が0になる）
    """
    if len(positions) != 3:
        return positions
    
    min_row = min(p[0] for p in positions)
    return [(p[0] - min_row, p[1]) for p in positions]


def is_horizontal_straight(positions: List[Tuple[int, int]]) -> bool:
    """横一文字型かどうかを判定する
    
    同じ行に3桁が連続して並んでいる（列の差が1）
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        横一文字型の場合True
    """
    if len(positions) != 3:
        return False
    
    # すべて同じ行か確認
    rows = [p[0] for p in positions]
    if len(set(rows)) != 1:
        return False
    
    # 列をソート
    cols = sorted([p[1] for p in positions])
    
    # 3桁が連続しているか確認（列の差が1）
    return (cols[1] - cols[0] == 1) and (cols[2] - cols[1] == 1)


def is_vertical_straight(positions: List[Tuple[int, int]]) -> bool:
    """縦一文字型かどうかを判定する
    
    同じ列に3桁が縦に連続して並んでいる（行の差が1）
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        縦一文字型の場合True
    """
    if len(positions) != 3:
        return False
    
    # すべて同じ列か確認
    cols = [p[1] for p in positions]
    if len(set(cols)) != 1:
        return False
    
    # 行をソート
    rows = sorted([p[0] for p in positions])
    
    # 3桁が連続しているか確認（行の差が1）
    return (rows[1] - rows[0] == 1) and (rows[2] - rows[1] == 1)


def is_v_shape(positions: List[Tuple[int, int]]) -> bool:
    """V字型かどうかを判定する
    
    AとCが同じ行で1列を挟んで隣（列の差が2列以上）、
    BがAとCのプラス1行目でAとCの間にある列に存在する
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        V字型の場合True
    """
    if len(positions) != 3:
        return False
    
    # すべての組み合わせを確認
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            k = 3 - i - j
            
            pos_a = positions[i]
            pos_b = positions[j]
            pos_c = positions[k]
            
            # AとCが同じ行で、列の差が2列以上か確認
            if pos_a[0] == pos_c[0] and (pos_c[1] - pos_a[1]) >= 2:
                # BがAとCのプラス1行目で、AとCの間にある列か確認
                if (pos_b[0] == pos_a[0] + 1 and 
                    pos_a[1] < pos_b[1] < pos_c[1]):
                    return True
    
    return False


def is_inverted_v_shape(positions: List[Tuple[int, int]]) -> bool:
    """逆V字型かどうかを判定する
    
    AとCが同じ行で1列を挟んで隣（列の差が2列）、
    BがAとCのマイナス1行目でAとCの間にある列に存在する
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        逆V字型の場合True
    """
    if len(positions) != 3:
        return False
    
    # 位置をソート（行、列の順）
    sorted_positions = sorted(positions, key=lambda p: (p[0], p[1]))
    pos1, pos2, pos3 = sorted_positions
    
    # AとCが同じ行で、列の差が2列か確認
    if pos1[0] == pos3[0] and (pos3[1] - pos1[1]) == 2:
        # BがAとCのマイナス1行目で、AとCの間にある列か確認
        if pos2[0] == pos1[0] - 1 and pos1[1] < pos2[1] < pos3[1]:
            return True
    
    # 別の組み合わせも確認（pos1とpos2が同じ行の場合）
    if pos1[0] == pos2[0] and (pos2[1] - pos1[1]) == 2:
        if pos3[0] == pos1[0] - 1 and pos1[1] < pos3[1] < pos2[1]:
            return True
    
    # pos2とpos3が同じ行の場合
    if pos2[0] == pos3[0] and (pos3[1] - pos2[1]) == 2:
        if pos1[0] == pos2[0] - 1 and pos2[1] < pos1[1] < pos3[1]:
            return True
    
    return False


def is_l_shape_bottom_left(positions: List[Tuple[int, int]]) -> bool:
    """└字型（左下L字）かどうかを判定する
    
    縦方向が上から下に伸び、横方向が右に伸びるL字。
    縦方向は2行目→3行目、または3行目→4行目で連続。
    横方向は同じ行内で連続（右に伸びる、2桁まで）。
    角は縦方向の下の点と横方向の左端が同じ位置。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        └字型の場合True
    """
    if len(positions) != 3:
        return False
    
    # 2つが同じ行にあり、1つが別の行にあるか確認
    rows = [p[0] for p in positions]
    row_counts = {}
    for row in rows:
        row_counts[row] = row_counts.get(row, 0) + 1
    
    # 2つが同じ行、1つが別の行
    if sorted(row_counts.values()) != [1, 2]:
        return False
    
    # 同じ行の2つの位置を取得
    horizontal_positions = [p for p in positions if rows.count(p[0]) == 2]
    vertical_position = [p for p in positions if rows.count(p[0]) == 1][0]
    
    # 横方向の2つが隣接しているか確認（列の差が1）
    horizontal_sorted = sorted(horizontal_positions, key=lambda p: p[1])
    if horizontal_sorted[1][1] - horizontal_sorted[0][1] != 1:
        return False
    
    # 縦方向が横方向の行の下の行にあるか確認（行の差が1）
    # └字型の場合: 縦方向が上（小さい行）、横方向が下（大きい行）
    horizontal_row = horizontal_positions[0][0]
    vertical_row = vertical_position[0]
    
    # 縦方向が横方向の上の行にあるか確認（行の差が1）
    if vertical_row != horizontal_row - 1:
        return False
    
    # 角の位置を確認: 縦方向の下の点と横方向の左端が同じ位置
    # つまり、vertical_positionの行+1と列が、horizontal_sorted[0]の行と列が同じ
    corner_row = vertical_row + 1  # 縦方向の下の点の行
    corner_col = horizontal_sorted[0][1]  # 横方向の左端の列
    
    # 角の位置が一致するか確認（縦方向の下の点 = 横方向の左端）
    if corner_row == horizontal_row and corner_col == horizontal_sorted[0][1]:
        # 縦方向の位置が角の上にあるか確認
        if vertical_position[0] == corner_row - 1 and vertical_position[1] == corner_col:
            # 横方向が右に伸びているか確認（左端が角、右端が角+1）
            if horizontal_sorted[1][1] == corner_col + 1:
                return True
    
    return False


def is_l_shape_bottom_right(positions: List[Tuple[int, int]]) -> bool:
    """┘字型（右下L字）かどうかを判定する
    
    縦方向が上から下に伸び、横方向が左に伸びるL字。
    縦方向は2行目→3行目、または3行目→4行目で連続。
    横方向は同じ行内で連続（左に伸びる、2桁まで）。
    角は縦方向の下の点と横方向の右端が同じ位置。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        ┘字型の場合True
    """
    if len(positions) != 3:
        return False
    
    # 2つが同じ行にあり、1つが別の行にあるか確認
    rows = [p[0] for p in positions]
    row_counts = {}
    for row in rows:
        row_counts[row] = row_counts.get(row, 0) + 1
    
    # 2つが同じ行、1つが別の行
    if sorted(row_counts.values()) != [1, 2]:
        return False
    
    # 同じ行の2つの位置を取得
    horizontal_positions = [p for p in positions if rows.count(p[0]) == 2]
    vertical_position = [p for p in positions if rows.count(p[0]) == 1][0]
    
    # 横方向の2つが隣接しているか確認（列の差が1）
    horizontal_sorted = sorted(horizontal_positions, key=lambda p: p[1])
    if horizontal_sorted[1][1] - horizontal_sorted[0][1] != 1:
        return False
    
    # 縦方向が横方向の行の下の行にあるか確認（行の差が1）
    # ┘字型の場合: 縦方向が上（小さい行）、横方向が下（大きい行）
    horizontal_row = horizontal_positions[0][0]
    vertical_row = vertical_position[0]
    
    # 縦方向が横方向の上の行にあるか確認（行の差が1）
    if vertical_row != horizontal_row - 1:
        return False
    
    # 角の位置を確認: 縦方向の下の点と横方向の右端が同じ位置
    # つまり、vertical_positionの行+1と列が、horizontal_sorted[1]の行と列が同じ
    corner_row = vertical_row + 1  # 縦方向の下の点の行
    corner_col = horizontal_sorted[1][1]  # 横方向の右端の列
    
    # 角の位置が一致するか確認（縦方向の下の点 = 横方向の右端）
    if corner_row == horizontal_row and corner_col == horizontal_sorted[1][1]:
        # 縦方向の位置が角の上にあるか確認
        if vertical_position[0] == corner_row - 1 and vertical_position[1] == corner_col:
            # 横方向が左に伸びているか確認（右端が角、左端が角-1）
            if horizontal_sorted[0][1] == corner_col - 1:
                return True
    
    return False


def is_l_shape_top_left(positions: List[Tuple[int, int]]) -> bool:
    """┌字型（左上L字）かどうかを判定する
    
    横方向が右に伸び、縦方向が下に伸びるL字。
    縦方向は2行目→3行目、または3行目→4行目で連続。
    横方向は同じ行内で連続（右に伸びる、2桁まで）。
    角は横方向の左端と縦方向の上の点が同じ位置。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        ┌字型の場合True
    """
    if len(positions) != 3:
        return False
    
    # 2つが同じ行にあり、1つが別の行にあるか確認
    rows = [p[0] for p in positions]
    row_counts = {}
    for row in rows:
        row_counts[row] = row_counts.get(row, 0) + 1
    
    # 2つが同じ行、1つが別の行
    if sorted(row_counts.values()) != [1, 2]:
        return False
    
    # 同じ行の2つの位置を取得
    horizontal_positions = [p for p in positions if rows.count(p[0]) == 2]
    vertical_position = [p for p in positions if rows.count(p[0]) == 1][0]
    
    # 横方向の2つが隣接しているか確認（列の差が1）
    horizontal_sorted = sorted(horizontal_positions, key=lambda p: p[1])
    if horizontal_sorted[1][1] - horizontal_sorted[0][1] != 1:
        return False
    
    # 縦方向が横方向の行の下の行にあるか確認（行の差が1）
    horizontal_row = horizontal_positions[0][0]
    if vertical_position[0] != horizontal_row + 1:
        return False
    
    # 角の位置を確認: 横方向の左端と縦方向の上の点が同じ位置
    # つまり、horizontal_sorted[0]の行と列が、vertical_positionの行-1と列が同じ
    corner_row = horizontal_row
    corner_col = horizontal_sorted[0][1]
    
    # 角の位置がvertical_positionの行-1と列が一致するか確認
    if vertical_position[0] == corner_row + 1 and vertical_position[1] == corner_col:
        # 横方向が右に伸びているか確認（左端が角、右端が角+1）
        if horizontal_sorted[1][1] == corner_col + 1:
            return True
    
    return False


def is_l_shape_top_right(positions: List[Tuple[int, int]]) -> bool:
    """┐字型（右上L字）かどうかを判定する
    
    横方向が左に伸び、縦方向が下に伸びるL字。
    縦方向は2行目→3行目、または3行目→4行目で連続。
    横方向は同じ行内で連続（左に伸びる、2桁まで）。
    角は横方向の右端と縦方向の上の点が同じ位置。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        ┐字型の場合True
    """
    if len(positions) != 3:
        return False
    
    # 2つが同じ行にあり、1つが別の行にあるか確認
    rows = [p[0] for p in positions]
    row_counts = {}
    for row in rows:
        row_counts[row] = row_counts.get(row, 0) + 1
    
    # 2つが同じ行、1つが別の行
    if sorted(row_counts.values()) != [1, 2]:
        return False
    
    # 同じ行の2つの位置を取得
    horizontal_positions = [p for p in positions if rows.count(p[0]) == 2]
    vertical_position = [p for p in positions if rows.count(p[0]) == 1][0]
    
    # 横方向の2つが隣接しているか確認（列の差が1）
    horizontal_sorted = sorted(horizontal_positions, key=lambda p: p[1])
    if horizontal_sorted[1][1] - horizontal_sorted[0][1] != 1:
        return False
    
    # 縦方向が横方向の行の下の行にあるか確認（行の差が1）
    horizontal_row = horizontal_positions[0][0]
    if vertical_position[0] != horizontal_row + 1:
        return False
    
    # 角の位置を確認: 横方向の右端と縦方向の上の点が同じ位置
    # つまり、horizontal_sorted[1]の行と列が、vertical_positionの行-1と列が同じ
    corner_row = horizontal_row
    corner_col = horizontal_sorted[1][1]
    
    # 角の位置がvertical_positionの行-1と列が一致するか確認
    if vertical_position[0] == corner_row + 1 and vertical_position[1] == corner_col:
        # 横方向が左に伸びているか確認（右端が角、左端が角-1）
        if horizontal_sorted[0][1] == corner_col - 1:
            return True
    
    return False


def check_diagonal_patterns(positions: List[Tuple[int, int]]) -> Optional[str]:
    """斜め型（4種類）の判定（相対位置で汎用化）
    
    どの区分（上部/中部/下部）でも同じロジックで判定可能。
    3つの位置が連続する3行にまたがり、斜めに並んでいるかを判定。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        斜め型の名前（斜め右下型、斜め左下型、斜め右上型、斜め左上型）、該当しない場合はNone
    """
    if len(positions) != 3:
        return None
    
    # 元の位置の順序を保持（斜め右上型・斜め左上型との区別のため）
    original_positions = positions.copy()
    
    # 位置をソート（行、列の順）
    sorted_positions = sorted(positions, key=lambda p: (p[0], p[1]))
    pos1, pos2, pos3 = sorted_positions
    
    row1, col1 = pos1
    row2, col2 = pos2
    row3, col3 = pos3
    
    # 行の差を確認
    row_diff_12 = row2 - row1
    row_diff_23 = row3 - row2
    
    # 列の差を確認
    col_diff_12 = col2 - col1
    col_diff_23 = col3 - col2
    
    # 斜め型の条件: 3つの位置が連続する3行にまたがる（行差が1ずつ）
    if row_diff_12 == 1 and row_diff_23 == 1:
        # 列の差が±1ずつであることを確認
        if abs(col_diff_12) == 1 and abs(col_diff_23) == 1:
            # 列の変化が一貫しているか確認
            if col_diff_12 == col_diff_23:
                # 元の位置の順序を確認（斜め右上型・斜め左上型との区別のため）
                # 元の位置で最初の位置の行がソート後の最大行なら、上から下への方向
                original_first_row = original_positions[0][0]
                max_row = row3  # ソート後の最大行
                
                # 斜め右下型: 列が+1ずつ増える
                # 斜め左上型: 最大行から始まる場合（逆順）
                if col_diff_12 == 1:
                    if original_first_row == max_row:
                        return "斜め左上型"
                    else:
                        return "斜め右下型"
                
                # 斜め左下型: 列が-1ずつ減る
                # 斜め右上型: 最大行から始まる場合（逆順）
                elif col_diff_12 == -1:
                    if original_first_row == max_row:
                        return "斜め右上型"
                    else:
                        return "斜め左下型"
    
    return None


def is_zigzag_right(positions: List[Tuple[int, int]]) -> bool:
    """ジグザグ型（右斜め）かどうかを判定する（相対位置で汎用化）
    
    最上行と最下行が同じ列にあり、中間行が右斜め下に配置される形。
    連続する3行にまたがる必要がある。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        ジグザグ型（右斜め）の場合True
    """
    if len(positions) != 3:
        return False
    
    # 位置を行でソート
    sorted_positions = sorted(positions, key=lambda p: p[0])
    pos1, pos2, pos3 = sorted_positions
    
    # 連続する3行であることを確認（相対位置で判定）
    if pos2[0] - pos1[0] != 1 or pos3[0] - pos2[0] != 1:
        return False
    
    # 最上行と最下行が同じ列か確認
    if pos1[1] != pos3[1]:
        return False
    
    # 中間行が最上行の列+1にあるか確認（右斜め下）
    if pos2[1] != pos1[1] + 1:
        return False
    
    return True


def is_zigzag_left(positions: List[Tuple[int, int]]) -> bool:
    """ジグザグ型（左斜め）かどうかを判定する（相対位置で汎用化）
    
    最上行と最下行が同じ列にあり、中間行が左斜め下に配置される形。
    連続する3行にまたがる必要がある。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        ジグザグ型（左斜め）の場合True
    """
    if len(positions) != 3:
        return False
    
    # 位置を行でソート
    sorted_positions = sorted(positions, key=lambda p: p[0])
    pos1, pos2, pos3 = sorted_positions
    
    # 連続する3行であることを確認（相対位置で判定）
    if pos2[0] - pos1[0] != 1 or pos3[0] - pos2[0] != 1:
        return False
    
    # 最上行と最下行が同じ列か確認
    if pos1[1] != pos3[1]:
        return False
    
    # 中間行が最上行の列-1にあるか確認（左斜め下）
    if pos2[1] != pos1[1] - 1:
        return False
    
    return True


def is_corner_horizontal_left_up(positions: List[Tuple[int, int]]) -> bool:
    """コーナー型（横長・左斜め上）かどうかを判定する（相対位置で汎用化）
    
    上の行に1つ、下の行に2つが横に並ぶ形。
    上の位置から左斜め下に伸び、その後横方向に右に伸びる。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        コーナー型（横長・左斜め上）の場合True
    """
    if len(positions) != 3:
        return False
    
    sorted_positions = sorted(positions, key=lambda p: (p[0], p[1]))
    pos1, pos2, pos3 = sorted_positions
    
    # 上の行に1つ、下の行に2つ（行差が1）
    if pos2[0] == pos1[0] + 1 and pos3[0] == pos1[0] + 1:
        # 上の行X列 → 下の行(X+1)列、下の行(X+2)列
        if pos2[1] == pos1[1] + 1 and pos3[1] == pos2[1] + 1:
            return True
    
    return False


def is_corner_horizontal_right_up(positions: List[Tuple[int, int]]) -> bool:
    """コーナー型（横長・右斜め上）かどうかを判定する（相対位置で汎用化）
    
    下の行に2つが横に並び、上の行に1つ。
    下から横に伸び、その後右斜め上に伸びる形。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        コーナー型（横長・右斜め上）の場合True
    """
    if len(positions) != 3:
        return False
    
    # 行ごとに分類
    rows = [p[0] for p in positions]
    row_counts = {}
    for row in rows:
        row_counts[row] = row_counts.get(row, 0) + 1
    
    # 2つが同じ行、1つが別の行（差が1）
    if sorted(row_counts.values()) != [1, 2]:
        return False
    
    # 2つある行と1つの行を特定
    row_with_two = [r for r, c in row_counts.items() if c == 2][0]
    row_with_one = [r for r, c in row_counts.items() if c == 1][0]
    
    # 2つある行が下（大きい行番号）で、1つの行が上（小さい行番号）
    if row_with_two - row_with_one != 1:
        return False
    
    # 下の行の2つの位置を取得
    lower_positions = sorted([p for p in positions if p[0] == row_with_two], key=lambda p: p[1])
    upper_position = [p for p in positions if p[0] == row_with_one][0]
    
    # 下の行の2つが横に連続
    if lower_positions[1][1] - lower_positions[0][1] != 1:
        return False
    
    # 上の位置が下の行の右端の右斜め上
    if upper_position[1] == lower_positions[1][1] + 1:
        return True
    
    return False


def is_corner_horizontal_left_down(positions: List[Tuple[int, int]]) -> bool:
    """コーナー型（横長・左斜め下）かどうかを判定する（相対位置で汎用化）
    
    下の行に1つ、上の行に2つが横に並ぶ形。
    下から右斜め上に伸び、その後横方向に右に伸びる。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        コーナー型（横長・左斜め下）の場合True
    """
    if len(positions) != 3:
        return False
    
    # 行ごとに分類
    rows = [p[0] for p in positions]
    row_counts = {}
    for row in rows:
        row_counts[row] = row_counts.get(row, 0) + 1
    
    # 2つが同じ行、1つが別の行（差が1）
    if sorted(row_counts.values()) != [1, 2]:
        return False
    
    # 2つある行と1つの行を特定
    row_with_two = [r for r, c in row_counts.items() if c == 2][0]
    row_with_one = [r for r, c in row_counts.items() if c == 1][0]
    
    # 2つある行が上（小さい行番号）で、1つの行が下（大きい行番号）
    if row_with_one - row_with_two != 1:
        return False
    
    # 上の行の2つの位置を取得
    upper_positions = sorted([p for p in positions if p[0] == row_with_two], key=lambda p: p[1])
    lower_position = [p for p in positions if p[0] == row_with_one][0]
    
    # 上の行の2つが横に連続
    if upper_positions[1][1] - upper_positions[0][1] != 1:
        return False
    
    # 下の位置が上の行の左端の左斜め下
    if lower_position[1] == upper_positions[0][1] - 1:
        return True
    
    return False


def is_corner_horizontal_right_down(positions: List[Tuple[int, int]]) -> bool:
    """コーナー型（横長・右斜め下）かどうかを判定する（相対位置で汎用化）
    
    上の行に2つが横に並び、下の行に1つ。
    横に伸び、その後右斜め下に伸びる形。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        コーナー型（横長・右斜め下）の場合True
    """
    if len(positions) != 3:
        return False
    
    sorted_positions = sorted(positions, key=lambda p: (p[0], p[1]))
    pos1, pos2, pos3 = sorted_positions
    
    # 上の行に2つ、下の行に1つ（行差が1）
    if pos1[0] == pos2[0] and pos3[0] == pos1[0] + 1:
        # 上の行X列・(X+1)列 → 下の行(X+2)列
        if pos2[1] == pos1[1] + 1 and pos3[1] == pos2[1] + 1:
            return True
    
    return False


def is_corner_vertical_left_up(positions: List[Tuple[int, int]]) -> bool:
    """コーナー型（縦長・左斜め上）かどうかを判定する（相対位置で汎用化）
    
    連続する3行で、最上行から左斜め下に伸び、その後縦方向に下に伸びる（同じ列）。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        コーナー型（縦長・左斜め上）の場合True
    """
    if len(positions) != 3:
        return False
    
    sorted_positions = sorted(positions, key=lambda p: (p[0], p[1]))
    pos1, pos2, pos3 = sorted_positions
    
    # 連続する3行であることを確認
    if pos2[0] - pos1[0] != 1 or pos3[0] - pos2[0] != 1:
        return False
    
    # 最上行X列 → 中間行(X+1)列 → 最下行(X+1)列
    if pos2[1] == pos1[1] + 1 and pos3[1] == pos2[1]:
        return True
    
    return False


def is_corner_vertical_right_up(positions: List[Tuple[int, int]]) -> bool:
    """コーナー型（縦長・右斜め上）かどうかを判定する（相対位置で汎用化）
    
    連続する3行で、最上行から右斜め下に伸び、その後縦方向に下に伸びる（同じ列）。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        コーナー型（縦長・右斜め上）の場合True
    """
    if len(positions) != 3:
        return False
    
    sorted_positions = sorted(positions, key=lambda p: (p[0], p[1]))
    pos1, pos2, pos3 = sorted_positions
    
    # 連続する3行であることを確認
    if pos2[0] - pos1[0] != 1 or pos3[0] - pos2[0] != 1:
        return False
    
    # 最上行X列 → 中間行(X-1)列 → 最下行(X-1)列
    if pos2[1] == pos1[1] - 1 and pos3[1] == pos2[1]:
        return True
    
    return False


def is_corner_vertical_left_down(positions: List[Tuple[int, int]]) -> bool:
    """コーナー型（縦長・左斜め下）かどうかを判定する（相対位置で汎用化）
    
    連続する3行で、最上行から縦方向に下に伸び、その後左斜め下に伸びる。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        コーナー型（縦長・左斜め下）の場合True
    """
    if len(positions) != 3:
        return False
    
    sorted_positions = sorted(positions, key=lambda p: (p[0], p[1]))
    pos1, pos2, pos3 = sorted_positions
    
    # 連続する3行であることを確認
    if pos2[0] - pos1[0] != 1 or pos3[0] - pos2[0] != 1:
        return False
    
    # 最上行X列 → 中間行X列 → 最下行(X-1)列
    if pos2[1] == pos1[1] and pos3[1] == pos2[1] - 1:
        return True
    
    return False


def is_corner_vertical_right_down(positions: List[Tuple[int, int]]) -> bool:
    """コーナー型（縦長・右斜め下）かどうかを判定する（相対位置で汎用化）
    
    連続する3行で、最上行から縦方向に下に伸び、その後右斜め下に伸びる。
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        コーナー型（縦長・右斜め下）の場合True
    """
    if len(positions) != 3:
        return False
    
    sorted_positions = sorted(positions, key=lambda p: (p[0], p[1]))
    pos1, pos2, pos3 = sorted_positions
    
    # 連続する3行であることを確認
    if pos2[0] - pos1[0] != 1 or pos3[0] - pos2[0] != 1:
        return False
    
    # 最上行X列 → 中間行X列 → 最下行(X+1)列
    if pos2[1] == pos1[1] and pos3[1] == pos2[1] + 1:
        return True
    
    return False


def classify_pattern(positions: List[Tuple[int, int]]) -> Optional[str]:
    """当選数字の位置から並び型を判定する
    
    判定順序の最適化:
    1. 横一文字型・縦一文字型（最も簡単、O(1)で判定可能）
    2. 斜め型（判定が比較的簡単、O(1)で判定可能）
    3. V字型・逆V字型（中程度の複雑さ）
    4. L字型（中程度の複雑さ）
    5. ジグザグ型（中程度の複雑さ）
    6. コーナー型（最も複雑、最後に判定）
    
    Args:
        positions: 当選数字の位置リスト（3つの位置、1-indexed）
    
    Returns:
        並び型の名前（22種類のうちどれか）、判定できない場合はNone
    """
    if len(positions) != 3:
        return None
    
    # Phase 3: 判定順序の最適化
    # 判定しやすい型から順に判定することで、早期リターンが可能
    
    # 1. 横一文字型・縦一文字型（最も簡単、O(1)で判定可能）
    if is_horizontal_straight(positions):
        return "横一文字型"
    
    if is_vertical_straight(positions):
        return "縦一文字型"
    
    # 2. 斜め型（判定が比較的簡単、O(1)で判定可能）
    # V字型・逆V字型より先に判定することで効率化
    diagonal_pattern = check_diagonal_patterns(positions)
    if diagonal_pattern:
        return diagonal_pattern
    
    # 3. V字型・逆V字型（中程度の複雑さ）
    if is_v_shape(positions):
        return "V字型"
    
    if is_inverted_v_shape(positions):
        return "逆V字型"
    
    # 4. L字型（└、┘、┌、┐）（中程度の複雑さ）
    if is_l_shape_bottom_left(positions):
        return "└字型（左下L字）"
    
    if is_l_shape_bottom_right(positions):
        return "┘字型（右下L字）"
    
    if is_l_shape_top_left(positions):
        return "┌字型（左上L字）"
    
    if is_l_shape_top_right(positions):
        return "┐字型（右上L字）"
    
    # 5. ジグザグ型（中程度の複雑さ）
    if is_zigzag_right(positions):
        return "ジグザグ型（右斜め）"
    
    if is_zigzag_left(positions):
        return "ジグザグ型（左斜め）"
    
    # 6. コーナー型（8種類）（最も複雑、最後に判定）
    # 横長バージョン（4種類）
    if is_corner_horizontal_left_up(positions):
        return "コーナー型（横長・左斜め上）"
    
    if is_corner_horizontal_right_up(positions):
        return "コーナー型（横長・右斜め上）"
    
    if is_corner_horizontal_left_down(positions):
        return "コーナー型（横長・左斜め下）"
    
    if is_corner_horizontal_right_down(positions):
        return "コーナー型（横長・右斜め下）"
    
    # 縦長バージョン（4種類）
    if is_corner_vertical_left_up(positions):
        return "コーナー型（縦長・左斜め上）"
    
    if is_corner_vertical_right_up(positions):
        return "コーナー型（縦長・右斜め上）"
    
    if is_corner_vertical_left_down(positions):
        return "コーナー型（縦長・左斜め下）"
    
    if is_corner_vertical_right_down(positions):
        return "コーナー型（縦長・右斜め下）"
    
    # すべての型を判定したが、該当する型が見つからなかった場合
    return None


def analyze_patterns(
    df: pd.DataFrame,
    keisen_master: dict,
    start_round: int = 3,
    end_round: Optional[int] = None,
    enable_detailed_stats: bool = False
) -> Dict[str, Any]:
    """全期間の並び型を分析する
    
    Args:
        df: 過去当選番号データ
        keisen_master: 罫線マスターデータ
        start_round: 開始回号
        end_round: 終了回号（Noneの場合は最新回まで）
        enable_detailed_stats: 詳細な統計情報を収集するか（デフォルト: False）
    
    Returns:
        分析結果の辞書
    """
    if end_round is None:
        end_round = int(df['round_number'].max())
    
    results = []
    pattern_counts = defaultdict(int)
    failed_rounds = []
    failure_reasons = defaultdict(list)  # 失敗理由別の回号リスト
    
    # Phase 3: エラーハンドリングの強化 - 詳細な統計情報
    unclassified_patterns = []  # 判定できないパターンの詳細
    pattern_attempts = defaultdict(int)  # 各型の判定試行回数（デバッグ用）
    pattern_times = defaultdict(list) if enable_detailed_stats else None  # 各型の判定時間（ミリ秒）
    
    for round_number in range(start_round, end_round + 1):
        try:
            # 回号の妥当性を検証
            if not validate_round_number(df, round_number):
                logger.debug(f"回号 {round_number} はスキップします（データ不足）")
                failure_reasons['validation_failed'].append(round_number)
                continue
            
            # 極CUBEを生成
            grid, rows, cols = generate_extreme_cube(df, keisen_master, round_number)
            
            # 当選数字を取得
            round_data = df[df['round_number'] == round_number].iloc[0]
            n3_winning_raw = round_data['n3_winning']
            
            # NULLチェック（文字列として読み込まれる）
            if pd.isna(n3_winning_raw) or str(n3_winning_raw).upper() == 'NULL':
                reason = "n3_winningがNULL"
                logger.debug(f"回号 {round_number}: {reason}")
                failed_rounds.append(round_number)
                failure_reasons['null_data'].append({
                    'round_number': round_number,
                    'reason': reason
                })
                continue
            
            # 文字列として読み込まれているので、そのままzfillで3桁にする
            n3_winning = str(n3_winning_raw).zfill(3)
            winning_digits = [int(d) for d in n3_winning]
            
            # 2,3,4,5行目で当選数字の位置を取得（各桁の全候補位置も取得）
            positions, all_candidates = get_winning_digits_positions(grid, winning_digits, return_all_candidates=True)
            
            if len(positions) != 3:
                reason = f"位置が3つ見つからない（見つかった数: {len(positions)}, 当選数字: {n3_winning}）"
                logger.debug(f"回号 {round_number}: {reason}")
                failed_rounds.append(round_number)
                failure_reasons['position_not_found'].append({
                    'round_number': round_number,
                    'n3_winning': n3_winning,
                    'found_count': len(positions),
                    'positions': positions,
                    'all_candidates': all_candidates,
                    'winning_digits': winning_digits
                })
                continue
            
            # つながりの確認
            if not are_all_connected(positions):
                reason = f"当選数字がつながっていない（位置: {positions}, 当選数字: {n3_winning}）"
                logger.debug(f"回号 {round_number}: {reason}")
                failed_rounds.append(round_number)
                failure_reasons['not_connected'].append({
                    'round_number': round_number,
                    'n3_winning': n3_winning,
                    'positions': positions,
                    'all_candidates': all_candidates,
                    'winning_digits': winning_digits
                })
                continue
            
            # 並び型を判定
            if enable_detailed_stats:
                start_time = time.time()
            
            pattern = classify_pattern(positions)
            
            if enable_detailed_stats and pattern_times is not None:
                elapsed_time = (time.time() - start_time) * 1000  # ミリ秒
                if pattern:
                    pattern_times[pattern].append(elapsed_time)
            
            if pattern is None:
                # Phase 3: エラーハンドリングの強化 - 判定できないパターンの詳細記録
                # 位置を実際の行番号で表示（1-indexedに変換）
                if len(positions) == 3:
                    pos_str = ", ".join([f"{p[0]}行目{p[1]}列" for p in positions])
                else:
                    pos_str = str(positions)
                unclassified_info = {
                    'round_number': round_number,
                    'n3_winning': n3_winning,
                    'positions': positions,
                    'position_str': pos_str
                }
                unclassified_patterns.append(unclassified_info)
                
                reason = f"並び型を判定できませんでした（位置: {positions}, 当選数字: {n3_winning}）"
                logger.debug(f"回号 {round_number}: {reason}")
                failed_rounds.append(round_number)
                failure_reasons['pattern_not_classified'].append({
                    'round_number': round_number,
                    'n3_winning': n3_winning,
                    'positions': positions
                })
                continue
            
            # 日付情報を取得（Phase 5: 集計機能のため）
            draw_date = round_data.get('draw_date', None)
            weekday_raw = round_data.get('weekday', None)
            month = None
            if draw_date and draw_date != 'NULL':
                try:
                    date_obj = pd.to_datetime(draw_date, errors='coerce')
                    if pd.notna(date_obj):
                        month = date_obj.month
                except:
                    pass
            
            # weekdayの処理（0=月曜日も正しく処理）
            weekday = None
            if weekday_raw is not None and str(weekday_raw).upper() != 'NULL':
                try:
                    weekday = int(weekday_raw)
                except (ValueError, TypeError):
                    weekday = None
            
            # 区分を判定
            zone = classify_position_zone(positions)
            
            # 方向を判定（百→十→一の順序）
            direction = classify_direction(positions)
            
            # 結果を記録
            results.append({
                'round_number': round_number,
                'n3_winning': n3_winning,
                'positions': positions,
                'pattern': pattern,
                'direction': direction,  # 方向（straight/reverse/mixed）
                'zone': zone,  # 区分（upper/middle/lower）
                'draw_date': draw_date if draw_date and draw_date != 'NULL' else None,
                'weekday': weekday,
                'month': month
            })
            pattern_counts[pattern] += 1
            
            if round_number % 100 == 0:
                logger.info(f"処理中: 回号 {round_number} / {end_round}（成功: {len(results)}, 失敗: {len(failed_rounds)}）")
        
        except Exception as e:
            logger.error(f"回号 {round_number} の処理中にエラーが発生しました: {e}", exc_info=True)
            failed_rounds.append(round_number)
            failure_reasons['exception'].append({
                'round_number': round_number,
                'error': str(e)
            })
            continue
    
    # Phase 5: 集計機能の実装
    # 曜日ごとの集計
    weekday_counts = defaultdict(lambda: defaultdict(int))
    weekday_names = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金'}
    
    # 月ごとの集計
    month_counts = defaultdict(lambda: defaultdict(int))
    
    # 週ごとの集計（ISO週番号を使用）
    week_counts = defaultdict(lambda: defaultdict(int))
    
    # 区分別の集計（新規追加）
    zone_counts = defaultdict(int)  # 区分ごとの総数
    zone_pattern_counts = defaultdict(lambda: defaultdict(int))  # 区分×並び型
    zone_weekday_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # 区分×曜日×並び型
    zone_month_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # 区分×月×並び型
    
    # 方向別の集計（BOX/ストレート/逆ストレート）
    direction_counts = defaultdict(int)  # 方向ごとの総数
    direction_pattern_counts = defaultdict(lambda: defaultdict(int))  # 方向×並び型
    direction_weekday_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # 方向×曜日×並び型
    direction_zone_counts = defaultdict(lambda: defaultdict(int))  # 方向×区分
    
    for result in results:
        pattern = result['pattern']
        weekday = result.get('weekday')
        month = result.get('month')
        draw_date = result.get('draw_date')
        zone = result.get('zone', 'unknown')
        direction = result.get('direction', 'unknown')
        
        # 曜日ごとの集計
        if weekday is not None:
            weekday_counts[weekday][pattern] += 1
        
        # 月ごとの集計
        if month is not None:
            month_counts[month][pattern] += 1
        
        # 週ごとの集計
        if draw_date:
            try:
                date_obj = pd.to_datetime(draw_date, errors='coerce')
                if pd.notna(date_obj):
                    # ISO週番号を取得（年-週番号の形式）
                    year, week_num, _ = date_obj.isocalendar()
                    week_key = f"{year}-W{week_num:02d}"
                    week_counts[week_key][pattern] += 1
            except:
                pass
        
        # 区分別の集計（新規追加）
        zone_counts[zone] += 1
        zone_pattern_counts[zone][pattern] += 1
        
        if weekday is not None:
            zone_weekday_counts[zone][weekday][pattern] += 1
        
        if month is not None:
            zone_month_counts[zone][month][pattern] += 1
        
        # 方向別の集計
        direction_counts[direction] += 1
        direction_pattern_counts[direction][pattern] += 1
        direction_zone_counts[direction][zone] += 1
        
        if weekday is not None:
            direction_weekday_counts[direction][weekday][pattern] += 1
    
    # Phase 3: エラーハンドリングの強化 - 統計情報の集計
    result_dict = {
        'results': results,
        'pattern_counts': dict(pattern_counts),
        'failed_rounds': failed_rounds,
        'failure_reasons': {
            'validation_failed': len(failure_reasons['validation_failed']),
            'position_not_found': len(failure_reasons['position_not_found']),
            'not_connected': len(failure_reasons['not_connected']),
            'pattern_not_classified': len(failure_reasons['pattern_not_classified']),
            'exception': len(failure_reasons['exception'])
        },
        'failure_details': dict(failure_reasons),  # 詳細情報（デバッグ用）
        'total_analyzed': len(results),
        'total_failed': len(failed_rounds),
        'total_rounds': end_round - start_round + 1,
        # Phase 5: 集計結果
        'aggregations': {
            'by_weekday': {
                weekday_names.get(wd, f'不明({wd})'): dict(counts) 
                for wd, counts in weekday_counts.items()
            },
            'by_month': {
                f'{month}月': dict(counts) 
                for month, counts in month_counts.items()
            },
            'by_week': dict(week_counts)
        },
        # 区分別集計（新規追加）
        'zone_aggregations': {
            'zone_counts': dict(zone_counts),  # 区分ごとの総数
            'zone_pattern_counts': {
                zone: dict(patterns) 
                for zone, patterns in zone_pattern_counts.items()
            },
            'zone_weekday_counts': {
                zone: {
                    weekday_names.get(wd, f'不明({wd})'): dict(patterns)
                    for wd, patterns in weekday_data.items()
                }
                for zone, weekday_data in zone_weekday_counts.items()
            },
            'zone_month_counts': {
                zone: {
                    f'{month}月': dict(patterns)
                    for month, patterns in month_data.items()
                }
                for zone, month_data in zone_month_counts.items()
            }
        },
        # 方向別集計（BOX/ストレート/逆ストレート）
        'direction_aggregations': {
            'direction_counts': dict(direction_counts),
            'direction_pattern_counts': {
                direction: dict(patterns)
                for direction, patterns in direction_pattern_counts.items()
            },
            'direction_zone_counts': {
                direction: dict(zones)
                for direction, zones in direction_zone_counts.items()
            },
            'direction_weekday_counts': {
                direction: {
                    weekday_names.get(wd, f'不明({wd})'): dict(patterns)
                    for wd, patterns in weekday_data.items()
                }
                for direction, weekday_data in direction_weekday_counts.items()
            }
        }
    }
    
    # 詳細な統計情報（enable_detailed_stats=Trueの場合のみ）
    if enable_detailed_stats and pattern_times is not None:
        # 各型の平均判定時間を計算
        pattern_avg_times = {}
        for pattern, times in pattern_times.items():
            if times:
                pattern_avg_times[pattern] = {
                    'avg_time_ms': sum(times) / len(times),
                    'min_time_ms': min(times),
                    'max_time_ms': max(times),
                    'count': len(times)
                }
        
        result_dict['detailed_stats'] = {
            'unclassified_patterns': unclassified_patterns,
            'unclassified_count': len(unclassified_patterns),
            'pattern_avg_times': pattern_avg_times,
            'pattern_attempts': dict(pattern_attempts)
        }
    else:
        # 未分類パターン情報（すべて出力）
        result_dict['unclassified_patterns_sample'] = unclassified_patterns if unclassified_patterns else []
        result_dict['unclassified_count'] = len(unclassified_patterns)
    
    return result_dict


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='極CUBE並び型判定スクリプト')
    parser.add_argument('--start-round', type=int, default=3, help='開始回号（デフォルト: 3）')
    parser.add_argument('--end-round', type=int, default=None, help='終了回号（デフォルト: 最新回）')
    parser.add_argument('--output-dir', type=str, default=None, help='出力ディレクトリ（デフォルト: data/analysis_results/02_extreme_cube/02-02_並び型分析）')
    parser.add_argument('--csv-path', type=str, default=None, help='過去当選番号CSVファイルのパス（デフォルト: data/past_results.csv）')
    parser.add_argument('--detailed-stats', action='store_true', help='詳細な統計情報を収集する（判定時間の計測など）')
    
    args = parser.parse_args()
    
    # パスの設定
    if args.csv_path is None:
        data_dir = PROJECT_ROOT / 'data'
    else:
        # csv_pathが指定された場合は、その親ディレクトリを使用
        csv_path = Path(args.csv_path)
        data_dir = csv_path.parent
    
    if args.output_dir is None:
        output_dir = PROJECT_ROOT / 'data' / 'analysis_results' / '02_extreme_cube' / '02-02_並び型分析'
    else:
        output_dir = Path(args.output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # データの読み込み
    logger.info("データを読み込んでいます...")
    df = load_past_results(data_dir)
    keisen_master = load_keisen_master(data_dir)
    
    # 分析実行
    logger.info(f"並び型分析を開始します（回号: {args.start_round} - {args.end_round or '最新'}）")
    if args.detailed_stats:
        logger.info("詳細統計モード: 判定時間の計測を有効化しました")
    results = analyze_patterns(df, keisen_master, args.start_round, args.end_round, enable_detailed_stats=args.detailed_stats)
    
    # 結果を保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # # JSON形式で保存（現在不要のためコメントアウト）
    # json_path = output_dir / f'pattern_analysis_{timestamp}.json'
    # with open(json_path, 'w', encoding='utf-8') as f:
    #     json.dump(results, f, ensure_ascii=False, indent=2)
    # logger.info(f"結果をJSON形式で保存しました: {json_path}")
    
    # # CSV形式で保存（現在不要のためコメントアウト）
    # csv_path_output = output_dir / f'pattern_analysis_{timestamp}.csv'
    # if results['results']:
    #     df_results = pd.DataFrame(results['results'])
    #     df_results.to_csv(csv_path_output, index=False, encoding='utf-8-sig')
    #     logger.info(f"結果をCSV形式で保存しました: {csv_path_output}")
    
    # # Phase 5: 集計結果をCSV形式で保存（現在不要のためコメントアウト）
    # if 'aggregations' in results:
    #     aggregations = results['aggregations']
    #     
    #     # 曜日ごとの集計CSV
    #     if aggregations.get('by_weekday'):
    #         weekday_csv_path = output_dir / f'pattern_analysis_by_weekday_{timestamp}.csv'
    #         weekday_data = []
    #         for weekday, counts in aggregations['by_weekday'].items():
    #             for pattern, count in counts.items():
    #                 weekday_data.append({
    #                     'weekday': weekday,
    #                     'pattern': pattern,
    #                     'count': count
    #                 })
    #         if weekday_data:
    #             df_weekday = pd.DataFrame(weekday_data)
    #             df_weekday.to_csv(weekday_csv_path, index=False, encoding='utf-8-sig')
    #             logger.info(f"曜日ごとの集計結果をCSV形式で保存しました: {weekday_csv_path}")
    #     
    #     # 月ごとの集計CSV
    #     if aggregations.get('by_month'):
    #         month_csv_path = output_dir / f'pattern_analysis_by_month_{timestamp}.csv'
    #         month_data = []
    #         for month, counts in aggregations['by_month'].items():
    #             for pattern, count in counts.items():
    #                 month_data.append({
    #                     'month': month,
    #                     'pattern': pattern,
    #                     'count': count
    #                 })
    #         if month_data:
    #             df_month = pd.DataFrame(month_data)
    #             df_month.to_csv(month_csv_path, index=False, encoding='utf-8-sig')
    #             logger.info(f"月ごとの集計結果をCSV形式で保存しました: {month_csv_path}")
    #     
    #     # 週ごとの集計CSV
    #     if aggregations.get('by_week'):
    #         week_csv_path = output_dir / f'pattern_analysis_by_week_{timestamp}.csv'
    #         week_data = []
    #         for week, counts in aggregations['by_week'].items():
    #             for pattern, count in counts.items():
    #                 week_data.append({
    #                     'week': week,
    #                     'pattern': pattern,
    #                     'count': count
    #                 })
    #         if week_data:
    #             df_week = pd.DataFrame(week_data)
    #             df_week.to_csv(week_csv_path, index=False, encoding='utf-8-sig')
    #             logger.info(f"週ごとの集計結果をCSV形式で保存しました: {week_csv_path}")
    
    # 統計情報を表示
    logger.info("=" * 60)
    logger.info("分析結果サマリー")
    logger.info("=" * 60)
    logger.info(f"総回数: {results['total_rounds']}")
    logger.info(f"分析成功回数: {results['total_analyzed']}")
    logger.info(f"分析失敗回数: {results['total_failed']}")
    
    if results['total_failed'] > 0:
        logger.info("\n失敗理由別の内訳:")
        for reason, count in results['failure_reasons'].items():
            if count > 0:
                logger.info(f"  {reason}: {count}回")
    
    if results['pattern_counts']:
        logger.info("\n並び型の出現回数:")
        for pattern, count in sorted(results['pattern_counts'].items(), key=lambda x: -x[1]):
            percentage = (count / results['total_analyzed'] * 100) if results['total_analyzed'] > 0 else 0
            logger.info(f"  {pattern}: {count}回 ({percentage:.2f}%)")
    else:
        logger.info("\n並び型の出現回数: なし（判定ロジック未実装）")
    
    # Phase 3: エラーハンドリングの強化 - 未分類パターンの情報表示
    if results.get('unclassified_count', 0) > 0:
        logger.info(f"\n未分類パターン: {results['unclassified_count']}件")
        if results.get('unclassified_patterns_sample'):
            logger.info("未分類パターン一覧:")
            for i, pattern_info in enumerate(results['unclassified_patterns_sample'], 1):
                logger.info(f"  {i}. 回号 {pattern_info['round_number']}: {pattern_info['n3_winning']} - {pattern_info.get('position_str', pattern_info['positions'])}")
    
    # Phase 3: 詳細統計情報の表示
    if args.detailed_stats and 'detailed_stats' in results:
        detailed = results['detailed_stats']
        logger.info("\n詳細統計情報:")
        if detailed.get('pattern_avg_times'):
            logger.info("各型の平均判定時間:")
            for pattern, time_info in sorted(detailed['pattern_avg_times'].items(), key=lambda x: x[1]['avg_time_ms']):
                logger.info(f"  {pattern}: 平均 {time_info['avg_time_ms']:.3f}ms (最小: {time_info['min_time_ms']:.3f}ms, 最大: {time_info['max_time_ms']:.3f}ms, 件数: {time_info['count']})")
    
    # Phase 5: 集計結果の表示
    if 'aggregations' in results:
        aggregations = results['aggregations']
        
        # 曜日ごとの集計
        if aggregations.get('by_weekday'):
            logger.info("\n曜日ごとの並び型出現回数:")
            for weekday, counts in sorted(aggregations['by_weekday'].items()):
                total = sum(counts.values())
                logger.info(f"  {weekday}曜日: 合計 {total}回")
                for pattern, count in sorted(counts.items(), key=lambda x: -x[1]):
                    percentage = (count / total * 100) if total > 0 else 0
                    logger.info(f"    {pattern}: {count}回 ({percentage:.2f}%)")
        
        # 月ごとの集計
        if aggregations.get('by_month'):
            logger.info("\n月ごとの並び型出現回数:")
            for month, counts in sorted(aggregations['by_month'].items(), key=lambda x: int(x[0].replace('月', ''))):
                total = sum(counts.values())
                logger.info(f"  {month}: 合計 {total}回")
                for pattern, count in sorted(counts.items(), key=lambda x: -x[1])[:5]:  # 上位5件のみ表示
                    percentage = (count / total * 100) if total > 0 else 0
                    logger.info(f"    {pattern}: {count}回 ({percentage:.2f}%)")
    
    logger.info("=" * 60)
    
    # Markdown形式でレポートを出力
    md_path = output_dir / f'pattern_analysis_{timestamp}.md'
    save_markdown_report(results, md_path, args.start_round, args.end_round or int(df['round_number'].max()))
    logger.info(f"Markdown形式でレポートを保存しました: {md_path}")


def save_markdown_report(result: Dict[str, Any], md_path: Path, start_round: int, end_round: int):
    """Markdown形式でレポートを出力する
    
    Args:
        result: 分析結果の辞書
        md_path: 出力ファイルパス
        start_round: 開始回号
        end_round: 終了回号
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 極CUBE並び型分析レポート\n\n")
        f.write(f"**生成日時**: {timestamp}\n\n")
        
        # ==================== 分析期間（冒頭に配置） ====================
        f.write(f"## 分析期間\n\n")
        f.write(f"- **開始回号**: {start_round}回\n")
        f.write(f"- **終了回号**: {end_round}回\n")
        f.write(f"- **総回数**: {result['total_rounds']}回\n\n")
        
        # ==================== 極CUBE内出現統計（冒頭に配置） ====================
        total_rounds = result['total_rounds']
        total_analyzed = result['total_analyzed']
        total_failed = result['total_failed']
        
        # 各失敗理由の件数を取得
        position_not_found = result['failure_reasons'].get('position_not_found', 0)
        not_connected = result['failure_reasons'].get('not_connected', 0)
        validation_failed = result['failure_reasons'].get('validation_failed', 0)
        exception_count = result['failure_reasons'].get('exception', 0)
        pattern_not_classified = result['failure_reasons'].get('pattern_not_classified', 0)
        
        # 極CUBE内に3桁すべてが存在する回数（データ不備を除く）
        valid_rounds = total_rounds - validation_failed - exception_count
        cube_appearance_count = valid_rounds - position_not_found
        cube_appearance_rate = (cube_appearance_count / valid_rounds * 100) if valid_rounds > 0 else 0
        
        f.write(f"## 極CUBE内出現統計\n\n")
        f.write(f"**有効データ**: {valid_rounds}回（総回数{total_rounds}回のうち、データ不備{validation_failed + exception_count}回を除く）\n\n")
        
        f.write(f"| 項目 | 回数 | 割合 |\n")
        f.write(f"|------|------|------|\n")
        f.write(f"| 極CUBE内に当選数字3桁すべてが出現 | {cube_appearance_count}回 | {cube_appearance_rate:.2f}% |\n")
        
        # 出現した中でつながりを形成したケース
        connected_rate = (total_analyzed / cube_appearance_count * 100) if cube_appearance_count > 0 else 0
        f.write(f"| 　├ つながりを形成（並び型判定成功） | {total_analyzed}回 | {connected_rate:.2f}% |\n")
        
        # 出現した中でつながりを形成しなかったケース
        not_connected_rate = (not_connected / cube_appearance_count * 100) if cube_appearance_count > 0 else 0
        f.write(f"| 　└ つながりを形成しない | {not_connected}回 | {not_connected_rate:.2f}% |\n")
        
        # 一部欠損
        not_found_rate = (position_not_found / valid_rounds * 100) if valid_rounds > 0 else 0
        f.write(f"| 極CUBE内に当選数字が出現しない（一部欠損） | {position_not_found}回 | {not_found_rate:.2f}% |\n")
        f.write(f"\n")
        
        # ==================== 分析結果サマリー ====================
        direction_agg = result.get('direction_aggregations', {})
        direction_counts = direction_agg.get('direction_counts', {})
        
        f.write(f"## 分析結果から言えること\n\n")
        
        # 極CUBEの有用性について
        f.write(f"### 極CUBEの有用性について\n\n")
        f.write(f"極CUBE内に当選数字3桁すべてが出現する確率は**{cube_appearance_rate:.1f}%**です。\n\n")
        
        if cube_appearance_rate >= 85:
            f.write(f"- ✅ **高い出現率**: 約{int(cube_appearance_rate)}%の確率で当選数字が極CUBE内に存在\n")
            f.write(f"- これは、極CUBEが当選数字の候補を絞り込むための有効なツールであることを示唆しています\n")
            f.write(f"- ただし、つながりを形成するのは出現ケースの約{connected_rate:.0f}%（全体の約{total_analyzed/valid_rounds*100:.0f}%）\n")
        elif cube_appearance_rate >= 70:
            f.write(f"- ⚠️ **中程度の出現率**: 約{int(cube_appearance_rate)}%の確率で当選数字が極CUBE内に存在\n")
            f.write(f"- 極CUBEは参考情報として活用できますが、約{int(100-cube_appearance_rate)}%は外れることに注意が必要\n")
        else:
            f.write(f"- ❌ **低い出現率**: 約{int(cube_appearance_rate)}%の確率で当選数字が極CUBE内に存在\n")
            f.write(f"- 極CUBEのみに依存した予測は推奨されません\n")
        f.write(f"\n")
        
        # 全体的な予測について
        f.write(f"### 全体的な予測について\n\n")
        
        # 方向別の集計
        straight_count = direction_counts.get('straight', 0)
        reverse_count = direction_counts.get('reverse', 0)
        mixed_count = direction_counts.get('mixed', 0)
        straight_rate = (straight_count / total_analyzed * 100) if total_analyzed > 0 else 0
        reverse_rate = (reverse_count / total_analyzed * 100) if total_analyzed > 0 else 0
        mixed_rate = (mixed_count / total_analyzed * 100) if total_analyzed > 0 else 0
        
        if total_analyzed > 0:
            f.write(f"| 方向 | 回数 | 割合 |\n")
            f.write(f"|------|------|------|\n")
            f.write(f"| ストレート（左→右/上→下） | {straight_count}回 | {straight_rate:.1f}% |\n")
            f.write(f"| 逆ストレート（右→左/下→上） | {reverse_count}回 | {reverse_rate:.1f}% |\n")
            f.write(f"| 混合 | {mixed_count}回 | {mixed_rate:.1f}% |\n")
            f.write(f"\n")
            
            # 統計的判断
            expected_rate = 33.3
            significance_threshold = 10
            
            max_direction = max(
                [('ストレート', straight_rate), ('逆ストレート', reverse_rate), ('混合', mixed_rate)],
                key=lambda x: x[1]
            )
            
            f.write(f"#### 統計学的観点\n\n")
            if max_direction[1] - expected_rate > significance_threshold:
                f.write(f"- **{max_direction[0]}方向が優勢**（{max_direction[1]:.1f}%、期待値33.3%に対し+{max_direction[1] - expected_rate:.1f}ポイント）\n")
            else:
                f.write(f"- 方向別の出現率は**ほぼ均等**（各方向30〜37%程度で、大きな偏りなし）\n")
            
            f.write(f"\n#### 傾向と予測への活用\n\n")
            
            if total_analyzed < 100:
                f.write(f"- ⚠️ **サンプル数が{total_analyzed}回と少ないため、統計的に有意な結論を出すには不十分です**\n")
                f.write(f"- 傾向は参考程度とし、より多くのデータでの検証が必要です\n")
            else:
                if max_direction[1] - expected_rate > significance_threshold:
                    f.write(f"- {max_direction[0]}方向の並び型が多いため、予測時に{max_direction[0]}型を優先的に考慮することは合理的\n")
                else:
                    f.write(f"- 方向別の出現率に大きな偏りがないため、**型に基づく予測は困難**\n")
                    f.write(f"- 並び型よりも、出現数字そのものの傾向に注目する方が有効と考えられます\n")
            
            f.write(f"\n")
            
            # 結論
            f.write(f"#### 結論\n\n")
            if cube_appearance_rate >= 85 and total_analyzed >= 50:
                f.write(f"極CUBEは当選数字の絞り込みには有効ですが、並び型だけで予測精度を上げることは難しいです。\n")
                f.write(f"極CUBE内の数字を候補として活用しつつ、他の分析（出現頻度、連続性など）と組み合わせることを推奨します。\n")
            else:
                f.write(f"サンプル数またはデータの特性から、現時点では明確な傾向を特定できません。\n")
                f.write(f"より長期間のデータで検証することを推奨します。\n")
            f.write(f"\n")
        else:
            f.write(f"分析対象データがないため、コメントできません。\n\n")
        
        # ==================== 概要（詳細説明） ====================
        f.write(f"## 概要\n\n")
        f.write(f"このレポートは、極CUBE（Extreme CUBE）における当選数字（N3の3桁）の並び型を分析した結果です。\n")
        f.write(f"極CUBEの1〜5行目で当選数字がつながりを形成する場合、その位置関係から並び型（V字型、L字型、コーナー型など）を判定しています。\n\n")
        
        # 区分別集計（新規追加）
        zone_agg = result.get('zone_aggregations', {})
        zone_counts = zone_agg.get('zone_counts', {})
        zone_pattern_counts = zone_agg.get('zone_pattern_counts', {})
        
        # 区分別集計（常に表示）
        f.write(f"## 区分別集計\n\n")
        f.write(f"当選数字が出現する行の位置によって、上部・中部・下部に分類しています。\n\n")
        f.write(f"- **上部**: 1行目を含む（1,2,3行目）\n")
        f.write(f"- **中部**: 2,3,4行目のみ\n")
        f.write(f"- **下部**: 5行目を含む（3,4,5行目）\n\n")
        
        f.write(f"### 区分ごとの出現回数\n\n")
        f.write(f"| 区分 | 出現回数 | 出現率 |\n")
        f.write(f"|------|----------|--------|\n")
        total_analyzed = result['total_analyzed']
        # すべての区分を表示（0件でも表示）
        for zone in ['upper', 'middle', 'lower', 'unknown']:
            count = zone_counts.get(zone, 0)
            zone_name = get_zone_display_name(zone)
            percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
            f.write(f"| {zone_name} | {count}回 | {percentage:.2f}% |\n")
        f.write(f"\n")
        
        # 各区分の並び型（0件でも表示）
        for zone in ['upper', 'middle', 'lower']:
            zone_name = get_zone_display_name(zone)
            zone_total = zone_counts.get(zone, 0)
            zone_patterns = zone_pattern_counts.get(zone, {})
            
            f.write(f"### {zone_name}の並び型\n\n")
            f.write(f"- **合計**: {zone_total}回\n\n")
            
            if zone_patterns:
                f.write(f"| 並び型 | 出現回数 | 出現率 |\n")
                f.write(f"|--------|----------|--------|\n")
                for pattern, count in sorted(zone_patterns.items(), key=lambda x: -x[1]):
                    percentage = (count / zone_total * 100) if zone_total > 0 else 0
                    f.write(f"| {pattern} | {count}回 | {percentage:.2f}% |\n")
            else:
                f.write(f"並び型の出現: なし（{zone_total}回）\n")
            f.write(f"\n")
        
        # 方向別集計（BOX/ストレート/逆ストレート）
        direction_agg = result.get('direction_aggregations', {})
        direction_counts = direction_agg.get('direction_counts', {})
        direction_pattern_counts = direction_agg.get('direction_pattern_counts', {})
        
        f.write(f"## 方向別集計（BOX/ストレート/逆ストレート）\n\n")
        f.write(f"百の位→十の位→一の位の順序で、位置がどの方向に向かっているかを判定しています。\n\n")
        f.write(f"- **ストレート**: 左→右 または 上→下（正方向）\n")
        f.write(f"- **逆ストレート**: 右→左 または 下→上（逆方向）\n")
        f.write(f"- **混合**: 一方向に定まらない配置\n\n")
        
        f.write(f"### 方向ごとの出現回数\n\n")
        f.write(f"| 方向 | 出現回数 | 出現率 |\n")
        f.write(f"|------|----------|--------|\n")
        direction_names = {
            'straight': 'ストレート（左→右/上→下）',
            'reverse': '逆ストレート（右→左/下→上）',
            'mixed': '混合',
            'unknown': '不明'
        }
        total_analyzed = result['total_analyzed']
        for direction in ['straight', 'reverse', 'mixed']:
            count = direction_counts.get(direction, 0)
            direction_name = direction_names.get(direction, direction)
            percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
            f.write(f"| {direction_name} | {count}回 | {percentage:.2f}% |\n")
        f.write(f"\n")
        
        # 各方向の並び型
        for direction in ['straight', 'reverse', 'mixed']:
            direction_name = direction_names.get(direction, direction)
            direction_total = direction_counts.get(direction, 0)
            dir_patterns = direction_pattern_counts.get(direction, {})
            
            if direction_total > 0:
                f.write(f"### {direction_name}の並び型\n\n")
                f.write(f"- **合計**: {direction_total}回\n\n")
                
                if dir_patterns:
                    f.write(f"| 並び型 | 出現回数 | 出現率 |\n")
                    f.write(f"|--------|----------|--------|\n")
                    for pattern, count in sorted(dir_patterns.items(), key=lambda x: -x[1]):
                        percentage = (count / direction_total * 100) if direction_total > 0 else 0
                        f.write(f"| {pattern} | {count}回 | {percentage:.2f}% |\n")
                f.write(f"\n")
        
        # 並び型の出現回数（全体 - BOX版）
        f.write(f"## 並び型の出現回数（BOX版 - 順不同）\n\n")
        if result['pattern_counts']:
            f.write(f"| 並び型 | 出現回数 | 出現率 |\n")
            f.write(f"|--------|----------|--------|\n")
            total_analyzed = result['total_analyzed']
            for pattern, count in sorted(result['pattern_counts'].items(), key=lambda x: -x[1]):
                percentage = (count / total_analyzed * 100) if total_analyzed > 0 else 0
                f.write(f"| {pattern} | {count}回 | {percentage:.2f}% |\n")
        else:
            f.write(f"並び型の出現回数: なし\n")
        f.write(f"\n")
        
        # 未分類パターン
        if result.get('unclassified_count', 0) > 0:
            f.write(f"## 未分類パターン\n\n")
            f.write(f"- **未分類パターン数**: {result['unclassified_count']}件\n")
            if result.get('unclassified_patterns_sample'):
                f.write(f"\n### 未分類パターン一覧\n\n")
                f.write(f"| 回号 | 当選数字 | 位置 |\n")
                f.write(f"|------|----------|------|\n")
                for pattern_info in result['unclassified_patterns_sample']:
                    pos_str = pattern_info.get('position_str', str(pattern_info['positions']))
                    f.write(f"| {pattern_info['round_number']} | {pattern_info['n3_winning']} | {pos_str} |\n")
            f.write(f"\n")
        
        # 曜日ごとの集計（月〜金すべて表示、全体・区分別）
        f.write(f"## 曜日ごとの並び型出現傾向\n\n")
        
        weekday_order = ['月', '火', '水', '木', '金']
        aggregations = result.get('aggregations', {})
        weekday_data = aggregations.get('by_weekday', {})
        zone_agg = result.get('zone_aggregations', {})
        zone_weekday_data = zone_agg.get('zone_weekday_counts', {})
        direction_agg = result.get('direction_aggregations', {})
        direction_weekday_data = direction_agg.get('direction_weekday_counts', {})
        
        # 全体の曜日別集計
        total_all = result['total_analyzed']
        f.write(f"### 全体\n\n")
        f.write(f"| 曜日 | 出現回数 | 出現率 | 主要な並び型 |\n")
        f.write(f"|------|----------|--------|-------------|\n")
        for weekday in weekday_order:
            weekday_key = weekday
            if weekday_key in weekday_data:
                counts = weekday_data[weekday_key]
                total = sum(counts.values())
                rate = (total / total_all * 100) if total_all > 0 else 0
                if counts:
                    top_patterns = sorted(counts.items(), key=lambda x: -x[1])[:3]
                    top_str = ", ".join([f"{p[0]}({p[1]}回)" for p in top_patterns])
                else:
                    top_str = "-"
            else:
                total = 0
                rate = 0
                top_str = "-"
            f.write(f"| {weekday}曜日 | {total}回 | {rate:.1f}% | {top_str} |\n")
        f.write(f"\n")
        
        # 方向別の曜日集計（ストレート/逆ストレート/混合）- 並び型傾向も表示
        direction_names = {
            'straight': 'ストレート（左→右/上→下）',
            'reverse': '逆ストレート（右→左/下→上）',
            'mixed': '混合'
        }
        
        f.write(f"### 方向別×曜日別の並び型出現傾向\n\n")
        f.write(f"※出現率は全分析対象（{total_all}回）に対する割合\n\n")
        for direction in ['straight', 'reverse', 'mixed']:
            direction_name = direction_names.get(direction, direction)
            dir_weekday = direction_weekday_data.get(direction, {})
            dir_total = direction_agg.get('direction_counts', {}).get(direction, 0)
            dir_rate_of_total = (dir_total / total_all * 100) if total_all > 0 else 0
            
            f.write(f"#### {direction_name}（{dir_total}回 / {dir_rate_of_total:.1f}%）\n\n")
            f.write(f"| 曜日 | 出現回数 | 出現率(全体比) | 主要な並び型 |\n")
            f.write(f"|------|----------|----------------|-------------|\n")
            for weekday in weekday_order:
                weekday_key = weekday
                if weekday_key in dir_weekday:
                    counts = dir_weekday[weekday_key]
                    total = sum(counts.values())
                    # 全分析対象に対する割合
                    rate = (total / total_all * 100) if total_all > 0 else 0
                    if counts:
                        top_patterns = sorted(counts.items(), key=lambda x: -x[1])[:3]
                        top_str = ", ".join([f"{p[0]}({p[1]}回)" for p in top_patterns])
                    else:
                        top_str = "-"
                else:
                    total = 0
                    rate = 0
                    top_str = "-"
                f.write(f"| {weekday}曜日 | {total}回 | {rate:.1f}% | {top_str} |\n")
            f.write(f"\n")
        
        # 区分別の曜日集計
        zone_names = {
            'upper': '上部（1,2,3行目）',
            'middle': '中部（2,3,4行目）',
            'lower': '下部（3,4,5行目）'
        }
        
        for zone in ['upper', 'middle', 'lower']:
            zone_name = zone_names.get(zone, zone)
            zone_data = zone_weekday_data.get(zone, {})
            zone_total = zone_agg.get('zone_counts', {}).get(zone, 0)
            zone_rate_of_total = (zone_total / total_all * 100) if total_all > 0 else 0
            
            f.write(f"### {zone_name}（{zone_total}回 / {zone_rate_of_total:.1f}%）\n\n")
            f.write(f"| 曜日 | 出現回数 | 出現率(全体比) | 主要な並び型 |\n")
            f.write(f"|------|----------|----------------|-------------|\n")
            for weekday in weekday_order:
                weekday_key = weekday
                if weekday_key in zone_data:
                    counts = zone_data[weekday_key]
                    total = sum(counts.values())
                    # 全分析対象に対する割合
                    rate = (total / total_all * 100) if total_all > 0 else 0
                    if counts:
                        top_patterns = sorted(counts.items(), key=lambda x: -x[1])[:3]
                        top_str = ", ".join([f"{p[0]}({p[1]}回)" for p in top_patterns])
                    else:
                        top_str = "-"
                else:
                    total = 0
                    rate = 0
                    top_str = "-"
                f.write(f"| {weekday}曜日 | {total}回 | {rate:.1f}% | {top_str} |\n")
            f.write(f"\n")
        
        # 月ごとの集計
        if 'aggregations' in result and result['aggregations'].get('by_month'):
            f.write(f"## 月ごとの並び型出現傾向\n\n")
            aggregations = result['aggregations']
            month_data = aggregations['by_month']
            
            for month in sorted(month_data.keys(), key=lambda x: int(x.replace('月', ''))):
                counts = month_data[month]
                total = sum(counts.values())
                f.write(f"### {month}\n\n")
                f.write(f"- **合計**: {total}回\n\n")
                f.write(f"| 並び型 | 出現回数 | 出現率 |\n")
                f.write(f"|--------|----------|--------|\n")
                for pattern, count in sorted(counts.items(), key=lambda x: -x[1])[:10]:  # 上位10件
                    percentage = (count / total * 100) if total > 0 else 0
                    f.write(f"| {pattern} | {count}回 | {percentage:.2f}% |\n")
                f.write(f"\n")
        
        # 統計的コメント
        f.write(f"## 統計的コメント\n\n")
        f.write(f"### 主要な知見\n\n")
        
        if result['pattern_counts']:
            # 最も出現頻度が高い型
            top_pattern = max(result['pattern_counts'].items(), key=lambda x: x[1])
            top_percentage = (top_pattern[1] / result['total_analyzed'] * 100) if result['total_analyzed'] > 0 else 0
            f.write(f"1. **最も出現頻度が高い並び型**: {top_pattern[0]}（{top_pattern[1]}回、{top_percentage:.2f}%）\n")
            
            # 期待値（均等に出現する場合）
            expected_count = result['total_analyzed'] / len(result['pattern_counts']) if result['pattern_counts'] else 0
            f.write(f"2. **期待値**: 各型が均等に出現する場合、各型の期待出現回数は {expected_count:.2f}回\n")
            
            # 期待値比が高い型
            high_ratio_patterns = []
            for pattern, count in result['pattern_counts'].items():
                if expected_count > 0:
                    ratio = count / expected_count
                    if ratio >= 1.2:  # 期待値の1.2倍以上
                        high_ratio_patterns.append((pattern, count, ratio))
            
            if high_ratio_patterns:
                f.write(f"3. **期待値比が高い並び型（期待値の1.2倍以上）**:\n")
                for pattern, count, ratio in sorted(high_ratio_patterns, key=lambda x: -x[2])[:5]:
                    f.write(f"   - {pattern}: {count}回（期待値の{ratio:.2f}倍）\n")
        
        f.write(f"\n### 注意事項\n\n")
        f.write(f"- 並び型の判定は、極CUBEの1〜5行目における当選数字（N3の3桁）の位置関係に基づいています。\n")
        f.write(f"- 区分は以下のルールで判定しています:\n")
        f.write(f"  - 1行目を含む → 上部\n")
        f.write(f"  - 5行目を含む → 下部\n")
        f.write(f"  - 2,3,4行のみ → 中部\n")
        f.write(f"- 統計的傾向は過去のデータに基づくものであり、将来の出現を保証するものではありません。\n")
        f.write(f"- ナンバーズ3は抽選によるランダムな結果であり、過去の傾向が将来も続くとは限りません。\n")
        f.write(f"\n")
        
        # 付録: つながっていない回のリスト（一番下に配置）
        failure_details = result.get('failure_details', {})
        not_connected_list = failure_details.get('not_connected', [])
        if not_connected_list:
            f.write(f"---\n\n")
            f.write(f"## 付録: つながっていない回のリスト\n\n")
            f.write(f"極CUBEの1〜5行目で当選数字がつながりを形成できなかった回の一覧です。\n")
            f.write(f"各桁の出現位置をすべて表示しています。\n\n")
            f.write(f"| 回号 | 当選数字 | 百の位の出現位置 | 十の位の出現位置 | 一の位の出現位置 |\n")
            f.write(f"|------|----------|------------------|------------------|------------------|\n")
            for item in not_connected_list:
                round_num = item.get('round_number', '?')
                n3 = item.get('n3_winning', '?')
                winning_digits = item.get('winning_digits', [])
                all_candidates = item.get('all_candidates', [])
                
                # 各桁の位置を整形
                pos_strs = []
                for i, candidates in enumerate(all_candidates):
                    digit = winning_digits[i] if i < len(winning_digits) else '?'
                    if candidates:
                        pos_list = [f"{p[0]}行{p[1]}列" for p in candidates]
                        pos_strs.append(f"'{digit}': " + ", ".join(pos_list))
                    else:
                        pos_strs.append(f"'{digit}': なし")
                
                while len(pos_strs) < 3:
                    pos_strs.append('-')
                f.write(f"| {round_num} | {n3} | {pos_strs[0]} | {pos_strs[1]} | {pos_strs[2]} |\n")
            f.write(f"\n")
        
        # 付録: データ不備（一番下に配置）
        validation_failed = result['failure_reasons'].get('validation_failed', 0)
        exception_count = result['failure_reasons'].get('exception', 0)
        if validation_failed + exception_count > 0:
            f.write(f"## 付録: データ不備について\n\n")
            if exception_count > 0:
                f.write(f"- **例外エラー**: {exception_count}回\n")
                exception_list = failure_details.get('exception', [])
                if exception_list:
                    f.write(f"  - 原因: 極CUBE生成に必要な過去の当選番号が未登録\n")
                    for item in exception_list:
                        f.write(f"  - 回号{item.get('round_number', '?')}: {item.get('error', '不明')}\n")
            if validation_failed > 0:
                f.write(f"- **検証失敗**: {validation_failed}回（データ不足）\n")
            f.write(f"\n")


if __name__ == '__main__':
    main()

