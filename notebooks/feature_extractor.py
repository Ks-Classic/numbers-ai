"""
特徴量エンジニアリングモジュール

予測表から特徴量を抽出し、AIモデル用のベクトルを生成します。
"""

from typing import List, Optional, Tuple, Dict, Literal
import numpy as np
import math
from chart_generator import inverse

Pattern = Literal['A1', 'A2', 'B1', 'B2']
Target = Literal['n3', 'n4']


def get_digit_positions(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    digit: int
) -> List[Tuple[int, int]]:
    """指定された数字の位置を取得する（1-indexed座標）
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        digit: 対象数字（0-9）
    
    Returns:
        位置のリスト（(row, col)のタプル、1-indexed）
    """
    positions = []
    for row in range(1, rows + 1):
        for col in range(1, cols + 1):
            if grid[row][col] == digit:
                positions.append((row, col))
    return positions


def get_rehearsal_positions(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    rehearsal_digits: str
) -> List[Tuple[int, int]]:
    """リハーサル数字の位置を取得する（1-indexed座標）
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        rehearsal_digits: リハーサル数字の文字列（例: "147"）
    
    Returns:
        位置のリスト（(row, col)のタプル、1-indexed）
    """
    positions = []
    # 文字列型に変換（数値型の場合に備えて）
    rehearsal_digits_str = str(rehearsal_digits)
    # '.0'を除去（数値型の場合に備えて）
    rehearsal_digits_str = rehearsal_digits_str.replace('.0', '')
    
    for digit_str in rehearsal_digits_str:
        digit = int(digit_str)
        digit_positions = get_digit_positions(grid, rows, cols, digit)
        positions.extend(digit_positions)
    return positions


def get_rehearsal_digit_positions(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    rehearsal_digits: str,
    digit_index: int
) -> List[Tuple[int, int]]:
    """リハーサル数字の特定桁の位置を取得する（1-indexed座標）
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        rehearsal_digits: リハーサル数字の文字列（例: "631"）
        digit_index: 桁のインデックス（0始まり、例: 0=最初の桁、1=2番目の桁）
    
    Returns:
        位置のリスト（(row, col)のタプル、1-indexed）
    """
    # 文字列型に変換（数値型の場合に備えて）
    rehearsal_digits_str = str(rehearsal_digits)
    # '.0'を除去（数値型の場合に備えて）
    rehearsal_digits_str = rehearsal_digits_str.replace('.0', '')
    
    if digit_index < 0 or digit_index >= len(rehearsal_digits_str):
        return []
    
    digit = int(rehearsal_digits_str[digit_index])
    return get_digit_positions(grid, rows, cols, digit)


def get_direction(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """2つの位置から方向を計算する（0-7）
    
    8方向を以下のように定義:
    0: 北（上）
    1: 北東（右上）
    2: 東（右）
    3: 南東（右下）
    4: 南（下）
    5: 南西（左下）
    6: 西（左）
    7: 北西（左上）
    
    Args:
        pos1: 基準位置（(row, col)のタプル、1-indexed）
        pos2: 対象位置（(row, col)のタプル、1-indexed）
    
    Returns:
        方向（0-7）
    """
    row_diff = pos2[0] - pos1[0]  # 行の差分（下向きが正）
    col_diff = pos2[1] - pos1[1]  # 列の差分（右向きが正）
    
    # 同じ位置の場合
    if row_diff == 0 and col_diff == 0:
        return 0  # デフォルトで北
    
    # 角度を計算（ラジアン）
    angle = math.atan2(row_diff, col_diff)
    
    # 角度を0-2πの範囲に正規化
    if angle < 0:
        angle += 2 * math.pi
    
    # 8方向に分類（各方向はπ/4の範囲）
    # 北(0)は-π/8からπ/8の範囲
    direction_index = int((angle + math.pi / 8) / (math.pi / 4)) % 8
    
    # 方向のマッピング（角度→方向インデックス）
    # 北(0): -π/8 ~ π/8 → 0
    # 北東(1): π/8 ~ 3π/8 → 1
    # 東(2): 3π/8 ~ 5π/8 → 2
    # 南東(3): 5π/8 ~ 7π/8 → 3
    # 南(4): 7π/8 ~ 9π/8 → 4
    # 南西(5): 9π/8 ~ 11π/8 → 5
    # 西(6): 11π/8 ~ 13π/8 → 6
    # 北西(7): 13π/8 ~ 15π/8 → 7
    
    return direction_index


# ==================== カテゴリ1: 形状特徴 ====================

def calculate_max_line_length(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    digit: int
) -> int:
    """同じ数字が連続する最大長を計算する
    
    横方向と縦方向の両方をチェックします。
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        digit: 対象数字（0-9）
    
    Returns:
        最大連続長
    """
    max_length = 0
    
    # 横方向のチェック
    for row in range(1, rows + 1):
        current_length = 0
        for col in range(1, cols + 1):
            if grid[row][col] == digit:
                current_length += 1
                max_length = max(max_length, current_length)
            else:
                current_length = 0
    
    # 縦方向のチェック
    for col in range(1, cols + 1):
        current_length = 0
        for row in range(1, rows + 1):
            if grid[row][col] == digit:
                current_length += 1
                max_length = max(max_length, current_length)
            else:
                current_length = 0
    
    return max_length


def calculate_turn_count(
    positions: List[Tuple[int, int]]
) -> int:
    """数字の配置方向が変わる回数（曲がりの回数）を計算する
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
    
    Returns:
        曲がりの回数
    """
    if len(positions) < 3:
        return 0
    
    # 位置をソート（行優先、次に列優先）
    sorted_positions = sorted(positions)
    
    turn_count = 0
    for i in range(1, len(sorted_positions) - 1):
        prev_pos = sorted_positions[i - 1]
        curr_pos = sorted_positions[i]
        next_pos = sorted_positions[i + 1]
        
        # 方向ベクトルを計算
        dir1 = (curr_pos[0] - prev_pos[0], curr_pos[1] - prev_pos[1])
        dir2 = (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1])
        
        # 方向が変わったかチェック（外積が0でない場合）
        cross_product = dir1[0] * dir2[1] - dir1[1] * dir2[0]
        if cross_product != 0:
            turn_count += 1
    
    return turn_count


def calculate_straightness(
    positions: List[Tuple[int, int]]
) -> float:
    """配置が直線的かどうかの度合いを計算する（0-1、1が最も直線的）
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
    
    Returns:
        直線度（0-1）
    """
    if len(positions) < 2:
        return 1.0
    
    # 最小二乗法で直線を近似
    x_coords = [pos[1] for pos in positions]
    y_coords = [pos[0] for pos in positions]
    
    n = len(positions)
    sum_x = sum(x_coords)
    sum_y = sum(y_coords)
    sum_xy = sum(x * y for x, y in zip(x_coords, y_coords))
    sum_x2 = sum(x * x for x in x_coords)
    
    # 傾きと切片を計算
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        # すべての点が同じx座標（縦線）
        return 1.0
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    # 残差平方和を計算
    residuals = []
    for x, y in zip(x_coords, y_coords):
        predicted_y = slope * x + intercept
        residuals.append((y - predicted_y) ** 2)
    
    # 正規化（最大残差を1として正規化）
    max_residual = max(residuals) if residuals else 0
    if max_residual == 0:
        return 1.0
    
    # 直線度 = 1 - 正規化された残差
    avg_residual = sum(residuals) / len(residuals)
    straightness = max(0.0, 1.0 - (avg_residual / max_residual))
    
    return straightness


def calculate_density(
    positions: List[Tuple[int, int]],
    rows: int,
    cols: int,
    window_size: int = 2
) -> float:
    """特定エリアへの集中度合いを計算する（密集度）
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        window_size: ウィンドウサイズ
    
    Returns:
        密集度（0-1）
    """
    if len(positions) == 0:
        return 0.0
    
    # 各位置を中心としたウィンドウ内の点の数をカウント
    max_density = 0
    for center_pos in positions:
        count = 0
        for pos in positions:
            row_dist = abs(pos[0] - center_pos[0])
            col_dist = abs(pos[1] - center_pos[1])
            if row_dist <= window_size and col_dist <= window_size:
                count += 1
        max_density = max(max_density, count)
    
    # 正規化（最大密度を1として）
    max_possible = (2 * window_size + 1) ** 2
    return max_density / max_possible if max_possible > 0 else 0.0


def calculate_diagonal_line_length(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    digit: int
) -> int:
    """対角線方向の連続長を計算する
    
    左上から右下、右上から左下の両方向をチェックします。
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        digit: 対象数字（0-9）
    
    Returns:
        最大対角線連続長
    """
    max_length = 0
    
    # 左上から右下方向（主対角線）
    for start_row in range(1, rows + 1):
        for start_col in range(1, cols + 1):
            current_length = 0
            row, col = start_row, start_col
            while row <= rows and col <= cols:
                if grid[row][col] == digit:
                    current_length += 1
                    max_length = max(max_length, current_length)
                else:
                    current_length = 0
                row += 1
                col += 1
    
    # 右上から左下方向（副対角線）
    for start_row in range(1, rows + 1):
        for start_col in range(1, cols + 1):
            current_length = 0
            row, col = start_row, start_col
            while row <= rows and col >= 1:
                if grid[row][col] == digit:
                    current_length += 1
                    max_length = max(max_length, current_length)
                else:
                    current_length = 0
                row += 1
                col -= 1
    
    return max_length


def calculate_clustering_coefficient(
    positions: List[Tuple[int, int]]
) -> float:
    """クラスタリング係数を計算する（0-1、1が最もクラスタリングされている）
    
    各点から最も近いk個の点までの平均距離を計算し、クラスタリング度を評価します。
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
    
    Returns:
        クラスタリング係数（0-1）
    """
    if len(positions) < 2:
        return 1.0
    
    # 各点から最も近い点までの距離を計算
    min_distances = []
    for i, pos1 in enumerate(positions):
        min_dist = float('inf')
        for j, pos2 in enumerate(positions):
            if i != j:
                dist = np.sqrt(
                    (pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2
                )
                min_dist = min(min_dist, dist)
        if min_dist != float('inf'):
            min_distances.append(min_dist)
    
    if len(min_distances) == 0:
        return 1.0
    
    # 平均最小距離を計算
    avg_min_dist = sum(min_distances) / len(min_distances)
    
    # 全点対の平均距離を計算（正規化のため）
    all_distances = []
    for i, pos1 in enumerate(positions):
        for j, pos2 in enumerate(positions[i+1:], start=i+1):
            dist = np.sqrt(
                (pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2
            )
            all_distances.append(dist)
    
    if len(all_distances) == 0:
        return 1.0
    
    avg_all_dist = sum(all_distances) / len(all_distances)
    
    # クラスタリング係数 = 1 - (正規化された平均最小距離)
    if avg_all_dist == 0:
        return 1.0
    
    coefficient = 1.0 - (avg_min_dist / avg_all_dist)
    return max(0.0, min(1.0, coefficient))


def calculate_shape_complexity(
    positions: List[Tuple[int, int]]
) -> float:
    """形状の複雑度を計算する（0-1、1が最も複雑）
    
    点の配置の複雑さを評価します。曲がり回数と分散度を組み合わせます。
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
    
    Returns:
        形状複雑度（0-1）
    """
    if len(positions) < 3:
        return 0.0
    
    # 曲がり回数を計算
    turn_count = calculate_turn_count(positions)
    
    # 正規化された曲がり回数（最大は位置数-2）
    max_turns = len(positions) - 2
    normalized_turns = turn_count / max_turns if max_turns > 0 else 0.0
    
    # 分散度を計算（簡易版）
    if len(positions) < 2:
        dispersion = 0.0
    else:
        centroid_x, centroid_y = calculate_centroid(positions)
        distances = [
            np.sqrt((pos[0] - centroid_y) ** 2 + (pos[1] - centroid_x) ** 2)
            for pos in positions
        ]
        avg_dist = sum(distances) / len(distances)
        max_dist = max(distances) if distances else 0.0
        dispersion = avg_dist / max_dist if max_dist > 0 else 0.0
    
    # 複雑度 = (正規化された曲がり回数 + 分散度) / 2
    complexity = (normalized_turns + dispersion) / 2.0
    return max(0.0, min(1.0, complexity))


# ==================== カテゴリ2: 位置特徴 ====================

def calculate_centroid(
    positions: List[Tuple[int, int]]
) -> Tuple[float, float]:
    """重心座標を計算する
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
    
    Returns:
        (重心X座標, 重心Y座標) のタプル
    """
    if len(positions) == 0:
        return (0.0, 0.0)
    
    sum_x = sum(pos[1] for pos in positions)
    sum_y = sum(pos[0] for pos in positions)
    count = len(positions)
    
    return (sum_x / count, sum_y / count)


def calculate_edge_distances(
    positions: List[Tuple[int, int]],
    rows: int,
    cols: int
) -> Dict[str, float]:
    """端からの距離を計算する
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        端からの距離の辞書
    """
    if len(positions) == 0:
        return {
            'left': 0.0,
            'right': 0.0,
            'top': 0.0,
            'bottom': 0.0
        }
    
    col_positions = [pos[1] for pos in positions]
    row_positions = [pos[0] for pos in positions]
    
    return {
        'left': min(col_positions) - 1,  # 1-indexedなので-1
        'right': cols - max(col_positions),
        'top': min(row_positions) - 1,
        'bottom': rows - max(row_positions)
    }


def calculate_center_distance(
    positions: List[Tuple[int, int]],
    rows: int,
    cols: int
) -> float:
    """表の中心からの平均距離を計算する
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        中心からの平均距離
    """
    if len(positions) == 0:
        return 0.0
    
    center_row = (rows + 1) / 2
    center_col = (cols + 1) / 2
    
    distances = []
    for pos in positions:
        dist = np.sqrt(
            (pos[0] - center_row) ** 2 + (pos[1] - center_col) ** 2
        )
        distances.append(dist)
    
    return sum(distances) / len(distances)


def calculate_quadrant_distribution(
    positions: List[Tuple[int, int]],
    rows: int,
    cols: int
) -> Dict[str, float]:
    """象限別の分布を計算する
    
    表を4つの象限に分割し、各象限の点の割合を計算します。
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        象限別の割合の辞書: {'quadrant_top_left', 'quadrant_top_right', 'quadrant_bottom_left', 'quadrant_bottom_right'}
    """
    if len(positions) == 0:
        return {
            'quadrant_top_left': 0.0,
            'quadrant_top_right': 0.0,
            'quadrant_bottom_left': 0.0,
            'quadrant_bottom_right': 0.0
        }
    
    center_row = (rows + 1) / 2
    center_col = (cols + 1) / 2
    
    quadrant_counts = [0, 0, 0, 0]  # 左上、右上、左下、右下
    
    for pos in positions:
        row, col = pos[0], pos[1]
        if row <= center_row:
            if col <= center_col:
                quadrant_counts[0] += 1  # 左上
            else:
                quadrant_counts[1] += 1  # 右上
        else:
            if col <= center_col:
                quadrant_counts[2] += 1  # 左下
            else:
                quadrant_counts[3] += 1  # 右下
    
    total = len(positions)
    return {
        'quadrant_top_left': quadrant_counts[0] / total if total > 0 else 0.0,
        'quadrant_top_right': quadrant_counts[1] / total if total > 0 else 0.0,
        'quadrant_bottom_left': quadrant_counts[2] / total if total > 0 else 0.0,
        'quadrant_bottom_right': quadrant_counts[3] / total if total > 0 else 0.0
    }


def calculate_edge_proximity(
    positions: List[Tuple[int, int]],
    rows: int,
    cols: int
) -> float:
    """エッジへの近接度を計算する（0-1、1が最もエッジに近い）
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        エッジ近接度（0-1）
    """
    if len(positions) == 0:
        return 0.0
    
    # 各位置から最も近いエッジまでの距離を計算
    edge_distances = []
    for pos in positions:
        row, col = pos[0], pos[1]
        dist_to_left = col - 1
        dist_to_right = cols - col
        dist_to_top = row - 1
        dist_to_bottom = rows - row
        min_edge_dist = min(dist_to_left, dist_to_right, dist_to_top, dist_to_bottom)
        edge_distances.append(min_edge_dist)
    
    # 平均エッジ距離を計算
    avg_edge_dist = sum(edge_distances) / len(edge_distances) if edge_distances else 0.0
    
    # 正規化（最大エッジ距離は rows/2 または cols/2 の小さい方）
    max_possible_dist = min(rows, cols) / 2.0
    if max_possible_dist == 0:
        return 0.0
    
    # エッジ近接度 = 1 - (正規化された平均距離)
    proximity = 1.0 - (avg_edge_dist / max_possible_dist)
    return max(0.0, min(1.0, proximity))


# ==================== カテゴリ3: 関係性特徴 ====================

def calculate_rehearsal_distance_mean(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> float:
    """リハーサルとの平均距離を計算する（既存のcalculate_rehearsal_distanceをリネーム）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        平均距離（候補が存在しない場合は大きな値）
    """
    if len(candidate_positions) == 0:
        return 999.0  # 大きな値
    
    if len(rehearsal_positions) == 0:
        return 999.0  # 大きな値
    
    total_distance = 0.0
    for c_pos in candidate_positions:
        min_dist = float('inf')
        for r_pos in rehearsal_positions:
            dist = np.sqrt(
                (c_pos[0] - r_pos[0]) ** 2 + (c_pos[1] - r_pos[1]) ** 2
            )
            min_dist = min(min_dist, dist)
        total_distance += min_dist
    
    return total_distance / len(candidate_positions)


def calculate_rehearsal_distance_stats(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> Dict[str, float]:
    """距離の統計量を計算（平均、中央値、Q25、Q75、最小、最大、標準偏差、トリム平均）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        統計量の辞書: {'mean', 'median', 'q25', 'q75', 'min', 'max', 'std', 'trimmed_mean'}
    """
    if len(candidate_positions) == 0:
        return {
            'mean': 999.0,
            'median': 999.0,
            'q25': 999.0,
            'q75': 999.0,
            'min': 999.0,
            'max': 999.0,
            'std': 0.0,
            'trimmed_mean': 999.0
        }
    
    if len(rehearsal_positions) == 0:
        return {
            'mean': 999.0,
            'median': 999.0,
            'q25': 999.0,
            'q75': 999.0,
            'min': 999.0,
            'max': 999.0,
            'std': 0.0,
            'trimmed_mean': 999.0
        }
    
    # 各候補位置から最も近いリハーサル位置までの距離を計算
    distances = []
    for c_pos in candidate_positions:
        min_dist = float('inf')
        for r_pos in rehearsal_positions:
            dist = np.sqrt(
                (c_pos[0] - r_pos[0]) ** 2 + (c_pos[1] - r_pos[1]) ** 2
            )
            min_dist = min(min_dist, dist)
        distances.append(min_dist)
    
    distances_array = np.array(distances)
    
    # 統計量を計算
    mean = float(np.mean(distances_array))
    median = float(np.median(distances_array))
    q25 = float(np.percentile(distances_array, 25))
    q75 = float(np.percentile(distances_array, 75))
    min_dist = float(np.min(distances_array))
    max_dist = float(np.max(distances_array))
    std = float(np.std(distances_array))
    
    # トリム平均（最大値を除外）
    if len(distances) > 1:
        trimmed_distances = distances_array[distances_array < max_dist]
        trimmed_mean = float(np.mean(trimmed_distances)) if len(trimmed_distances) > 0 else mean
    else:
        trimmed_mean = mean
    
    return {
        'mean': mean,
        'median': median,
        'q25': q25,
        'q75': q75,
        'min': min_dist,
        'max': max_dist,
        'std': std,
        'trimmed_mean': trimmed_mean
    }


def calculate_rehearsal_distance(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> float:
    """リハーサルとの平均距離を計算する（後方互換性のためのラッパー）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        平均距離（候補が存在しない場合は大きな値）
    """
    return calculate_rehearsal_distance_mean(candidate_positions, rehearsal_positions)


def calculate_overlap_count(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> int:
    """候補とリハーサルが同じ位置にある回数を計算する
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        重なり回数
    """
    candidate_set = set(candidate_positions)
    rehearsal_set = set(rehearsal_positions)
    return len(candidate_set & rehearsal_set)


def calculate_rehearsal_overlap_by_digit(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_digits: str,
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> Dict[str, float]:
    """リハーサル数字の各桁に対して、候補数字が重なっているかどうかを計算
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_digits: リハーサル数字の文字列（例: "631"）
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        重なり情報の辞書: {'overlap_count': int, 'overlap_ratio': float, 'overlap_by_digit': List[int]}
    """
    # 文字列型に変換
    rehearsal_digits_str = str(rehearsal_digits).replace('.0', '')
    
    if len(candidate_positions) == 0 or len(rehearsal_digits_str) == 0:
        return {
            'overlap_count': 0,
            'overlap_ratio': 0.0,
            'overlap_by_digit': [0] * len(rehearsal_digits_str) if rehearsal_digits_str else []
        }
    
    candidate_set = set(candidate_positions)
    overlap_by_digit = []
    
    # 各桁について重なりを計算
    for digit_index in range(len(rehearsal_digits_str)):
        digit_positions = get_rehearsal_digit_positions(
            grid, rows, cols, rehearsal_digits_str, digit_index
        )
        digit_set = set(digit_positions)
        overlap_count_for_digit = len(candidate_set & digit_set)
        overlap_by_digit.append(overlap_count_for_digit)
    
    total_overlap_count = sum(overlap_by_digit)
    overlap_ratio = total_overlap_count / len(rehearsal_digits_str) if len(rehearsal_digits_str) > 0 else 0.0
    
    return {
        'overlap_count': total_overlap_count,
        'overlap_ratio': overlap_ratio,
        'overlap_by_digit': overlap_by_digit
    }


def calculate_rehearsal_full_match(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_digits: str,
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> float:
    """リハーサル数字の全桁が候補数字に重なっているか（1 or 0）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_digits: リハーサル数字の文字列（例: "631"）
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        1.0 if 全桁が重なっている、0.0 otherwise
    """
    overlap_info = calculate_rehearsal_overlap_by_digit(
        candidate_positions, rehearsal_digits, grid, rows, cols
    )
    
    # 各桁が少なくとも1つ重なっているかチェック
    overlap_by_digit = overlap_info['overlap_by_digit']
    if len(overlap_by_digit) == 0:
        return 0.0
    
    # すべての桁が重なっている場合、各桁の重なり数が1以上
    if all(count > 0 for count in overlap_by_digit):
        return 1.0
    else:
        return 0.0


def calculate_rehearsal_partial_match(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_digits: str,
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> int:
    """リハーサル数字の何桁が候補数字に重なっているか（桁数として）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_digits: リハーサル数字の文字列（例: "631"）
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        重なっている桁数（0-3 for N3, 0-4 for N4）
    """
    overlap_info = calculate_rehearsal_overlap_by_digit(
        candidate_positions, rehearsal_digits, grid, rows, cols
    )
    
    # 各桁が少なくとも1つ重なっているかチェック
    overlap_by_digit = overlap_info['overlap_by_digit']
    return sum(1 for count in overlap_by_digit if count > 0)


def calculate_inverse_ratio(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]],
    grid: List[List[Optional[int]]]
) -> float:
    """候補がリハーサルの裏数字である割合を計算する
    
    修正版: リハーサル位置と候補位置が同じ座標にないと計算されない問題を修正
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
        grid: 予測表グリッド（1-indexed）
    
    Returns:
        裏数字の割合（0-1）
    """
    if len(candidate_positions) == 0:
        return 0.0
    
    if len(rehearsal_positions) == 0:
        return 0.0
    
    # リハーサル位置から、リハーサル数字の各桁の裏数字の位置を取得
    inverse_positions = set()
    processed_digits = set()
    
    for r_pos in rehearsal_positions:
        rehearsal_digit = grid[r_pos[0]][r_pos[1]]
        if rehearsal_digit is not None:
            # 同じリハーサル数字を複数回処理しないように
            if rehearsal_digit not in processed_digits:
                processed_digits.add(rehearsal_digit)
                inverse_digit = inverse(rehearsal_digit)
                # グリッド内で裏数字の位置を検索
                for row in range(1, len(grid)):
                    if row < len(grid):
                        for col in range(1, len(grid[row])):
                            if grid[row][col] == inverse_digit:
                                inverse_positions.add((row, col))
    
    # 候補位置と裏数字位置の重なりを計算
    candidate_set = set(candidate_positions)
    overlap_count = len(candidate_set & inverse_positions)
    
    return overlap_count / len(candidate_positions) if len(candidate_positions) > 0 else 0.0


def calculate_rehearsal_direction_histogram(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> List[int]:
    """リハーサル数字の各位置から見て、候補数字がどの方向にあるかを8方向で分類
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        8要素のリスト（各方向の候補数字の数）
    """
    histogram = [0] * 8
    
    if len(candidate_positions) == 0 or len(rehearsal_positions) == 0:
        return histogram
    
    # 各リハーサル位置から各候補位置への方向を計算
    for r_pos in rehearsal_positions:
        for c_pos in candidate_positions:
            direction = get_direction(r_pos, c_pos)
            histogram[direction] += 1
    
    return histogram


def calculate_rehearsal_primary_direction(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> int:
    """最も多い方向を返す（0-7）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        最も多い方向（0-7）、同数の場合は最初に見つかったもの
    """
    histogram = calculate_rehearsal_direction_histogram(
        candidate_positions, rehearsal_positions
    )
    
    if sum(histogram) == 0:
        return 0  # デフォルトで北
    
    return int(np.argmax(histogram))


def calculate_rehearsal_direction_concentration(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> float:
    """方向の集中度（エントロピーベース）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        集中度（0-1、1に近いほど集中している）
    """
    histogram = calculate_rehearsal_direction_histogram(
        candidate_positions, rehearsal_positions
    )
    
    total = sum(histogram)
    if total == 0:
        return 0.0
    
    # 正規化
    probabilities = [count / total for count in histogram]
    
    # エントロピーを計算
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log2(p)
    
    # 最大エントロピーはlog2(8) = 3
    max_entropy = math.log2(8)
    
    # 集中度 = 1 - (正規化されたエントロピー)
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    concentration = 1.0 - normalized_entropy
    
    return max(0.0, min(1.0, concentration))  # 0-1の範囲に制限


def calculate_rehearsal_direction_ratio(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> List[float]:
    """各方向の割合（正規化されたヒストグラム）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        8要素のリスト（各方向の割合、0-1）
    """
    histogram = calculate_rehearsal_direction_histogram(
        candidate_positions, rehearsal_positions
    )
    
    total = sum(histogram)
    if total == 0:
        return [0.0] * 8
    
    return [count / total for count in histogram]


def calculate_rehearsal_distance_bins(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> Dict[str, float]:
    """距離帯別の特徴量を計算する（0-1, 1-2, 2-3, 3+）
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        距離帯別の割合の辞書: {'bin_0_1', 'bin_1_2', 'bin_2_3', 'bin_3_plus'}
    """
    if len(candidate_positions) == 0 or len(rehearsal_positions) == 0:
        return {
            'rehearsal_distance_bin_0_1': 0.0,
            'rehearsal_distance_bin_1_2': 0.0,
            'rehearsal_distance_bin_2_3': 0.0,
            'rehearsal_distance_bin_3_plus': 0.0
        }
    
    # 各候補位置から最も近いリハーサル位置までの距離を計算
    distances = []
    for c_pos in candidate_positions:
        min_dist = float('inf')
        for r_pos in rehearsal_positions:
            dist = np.sqrt(
                (c_pos[0] - r_pos[0]) ** 2 + (c_pos[1] - r_pos[1]) ** 2
            )
            min_dist = min(min_dist, dist)
        distances.append(min_dist)
    
    # 距離帯別にカウント
    bin_0_1 = sum(1 for d in distances if 0 <= d < 1)
    bin_1_2 = sum(1 for d in distances if 1 <= d < 2)
    bin_2_3 = sum(1 for d in distances if 2 <= d < 3)
    bin_3_plus = sum(1 for d in distances if d >= 3)
    
    total = len(distances)
    if total == 0:
        return {
            'rehearsal_distance_bin_0_1': 0.0,
            'rehearsal_distance_bin_1_2': 0.0,
            'rehearsal_distance_bin_2_3': 0.0,
            'rehearsal_distance_bin_3_plus': 0.0
        }
    
    return {
        'rehearsal_distance_bin_0_1': bin_0_1 / total,
        'rehearsal_distance_bin_1_2': bin_1_2 / total,
        'rehearsal_distance_bin_2_3': bin_2_3 / total,
        'rehearsal_distance_bin_3_plus': bin_3_plus / total
    }


def calculate_rehearsal_angle(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> float:
    """候補ラインとリハーサルラインの角度差を計算する
    
    候補数字の重心とリハーサル数字の重心を結ぶ線の角度を計算します。
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
    
    Returns:
        角度（ラジアン、0-πの範囲）
    """
    if len(candidate_positions) == 0 or len(rehearsal_positions) == 0:
        return 0.0
    
    # 重心を計算
    candidate_centroid = calculate_centroid(candidate_positions)
    rehearsal_centroid = calculate_centroid(rehearsal_positions)
    
    # ベクトルを計算
    dx = candidate_centroid[0] - rehearsal_centroid[0]
    dy = candidate_centroid[1] - rehearsal_centroid[1]
    
    if dx == 0 and dy == 0:
        return 0.0
    
    # 角度を計算（ラジアン）
    angle = math.atan2(dy, dx)
    
    # 0-πの範囲に正規化
    if angle < 0:
        angle += math.pi
    
    return angle


def calculate_rehearsal_digit_distance_stats(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_digits: str,
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> Dict[str, float]:
    """リハーサル数字の各桁ごとの距離統計を計算する
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_digits: リハーサル数字の文字列（例: "631"）
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        各桁ごとの平均距離の辞書: {'digit_0_mean_dist', 'digit_1_mean_dist', ...}
    """
    rehearsal_digits_str = str(rehearsal_digits).replace('.0', '')
    
    if len(candidate_positions) == 0 or len(rehearsal_digits_str) == 0:
        result = {}
        for i in range(4):  # 最大4桁（N4の場合）
            result[f'rehearsal_digit_{i}_mean_distance'] = 999.0
        return result
    
    result = {}
    
    # 各桁について距離を計算
    for digit_index in range(len(rehearsal_digits_str)):
        digit_positions = get_rehearsal_digit_positions(
            grid, rows, cols, rehearsal_digits_str, digit_index
        )
        
        if len(digit_positions) == 0:
            result[f'rehearsal_digit_{digit_index}_mean_distance'] = 999.0
        else:
            # 各候補位置から最も近い当該桁の位置までの距離を計算
            distances = []
            for c_pos in candidate_positions:
                min_dist = float('inf')
                for d_pos in digit_positions:
                    dist = np.sqrt(
                        (c_pos[0] - d_pos[0]) ** 2 + (c_pos[1] - d_pos[1]) ** 2
                    )
                    min_dist = min(min_dist, dist)
                distances.append(min_dist)
            
            mean_dist = sum(distances) / len(distances) if distances else 999.0
            result[f'rehearsal_digit_{digit_index}_mean_distance'] = mean_dist
    
    # 残りの桁（N3の場合は3-4=0個、N4の場合は4-4=0個）は999.0で埋める
    for i in range(len(rehearsal_digits_str), 4):
        result[f'rehearsal_digit_{i}_mean_distance'] = 999.0
    
    return result


# ==================== カテゴリ4: 集約特徴 ====================

def calculate_combination_frequency(
    combination: str,
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> int:
    """表内での組み合わせの出現回数を計算する
    
    注意: この実装は簡易版です。実際の組み合わせ検出はより複雑なロジックが必要です。
    
    Args:
        combination: 組み合わせ文字列（例: "147"）
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        出現回数
    """
    # 文字列型に変換（数値型の場合に備えて）
    combination_str = str(combination).replace('.0', '')
    digits = [int(d) for d in combination_str]
    digit_positions = []
    for digit in digits:
        positions = get_digit_positions(grid, rows, cols, digit)
        digit_positions.append(len(positions))
    
    # 最小出現回数を返す（すべての桁が存在する場合の最小値）
    return min(digit_positions) if digit_positions else 0


def calculate_dispersion(
    positions: List[Tuple[int, int]]
) -> float:
    """数字の配置の分散度を計算する
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
    
    Returns:
        分散度
    """
    if len(positions) < 2:
        return 0.0
    
    centroid_x, centroid_y = calculate_centroid(positions)
    
    variances = []
    for pos in positions:
        var = (pos[0] - centroid_y) ** 2 + (pos[1] - centroid_x) ** 2
        variances.append(var)
    
    return np.var(variances)


def calculate_bias(
    positions: List[Tuple[int, int]],
    rows: int,
    cols: int
) -> float:
    """表の特定エリアへの偏り度を計算する
    
    Args:
        positions: 数字の位置リスト（(row, col)のタプル）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
    
    Returns:
        偏り度（0-1、1が最も偏っている）
    """
    if len(positions) == 0:
        return 0.0
    
    # 表を4つのエリアに分割（左上、右上、左下、右下）
    center_row = (rows + 1) / 2
    center_col = (cols + 1) / 2
    
    area_counts = [0, 0, 0, 0]  # 左上、右上、左下、右下
    
    for pos in positions:
        row, col = pos[0], pos[1]
        if row <= center_row:
            if col <= center_col:
                area_counts[0] += 1  # 左上
            else:
                area_counts[1] += 1  # 右上
        else:
            if col <= center_col:
                area_counts[2] += 1  # 左下
            else:
                area_counts[3] += 1  # 右下
    
    # 最大エリアの割合を計算
    max_count = max(area_counts)
    total = len(positions)
    
    return max_count / total if total > 0 else 0.0


# ==================== 統合特徴量計算 ====================

def calculate_n3_n4_rehearsal_common_digits(
    n3_rehearsal: Optional[str],
    n4_rehearsal: Optional[str]
) -> set:
    """N3とN4のリハーサル数字の共通部分（同じ数字が両方に含まれているか）を計算する
    
    Args:
        n3_rehearsal: N3のリハーサル数字（例: "631"）
        n4_rehearsal: N4のリハーサル数字（例: "8218"）
    
    Returns:
        共通部分の数字のセット（例: {1, 8}）
    """
    if not n3_rehearsal or not n4_rehearsal:
        return set()
    
    n3_rehearsal_str = str(n3_rehearsal).replace('.0', '')
    n4_rehearsal_str = str(n4_rehearsal).replace('.0', '')
    
    n3_digits = set(n3_rehearsal_str)
    n4_digits = set(n4_rehearsal_str)
    
    # 共通部分を計算
    common_digits = n3_digits & n4_digits
    
    return common_digits


def extract_digit_features(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    digit: int,
    rehearsal_positions: Optional[List[Tuple[int, int]]] = None,
    rehearsal_digits: Optional[str] = None,
    n3_n4_common_rehearsal_digits: Optional[set] = None  # N3/N4リハーサル数字の共通部分
) -> Dict[str, float]:
    """1つの数字に関する特徴量を抽出する
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        digit: 対象数字（0-9）
        rehearsal_positions: リハーサル数字の位置リスト（オプション）
        rehearsal_digits: リハーサル数字の文字列（オプション、例: "631"）
        n3_n4_common_rehearsal_digits: N3/N4リハーサル数字の共通部分（オプション）
    
    Returns:
        特徴量の辞書
    """
    positions = get_digit_positions(grid, rows, cols, digit)
    
    features = {}
    
    # カテゴリ1: 形状特徴
    features['max_line_length'] = calculate_max_line_length(grid, rows, cols, digit)
    features['turn_count'] = calculate_turn_count(positions)
    features['straightness'] = calculate_straightness(positions)
    features['density'] = calculate_density(positions, rows, cols)
    # 追加: 形状特徴量
    features['diagonal_line_length'] = calculate_diagonal_line_length(grid, rows, cols, digit)
    features['clustering_coefficient'] = calculate_clustering_coefficient(positions)
    features['shape_complexity'] = calculate_shape_complexity(positions)
    
    # カテゴリ2: 位置特徴
    centroid_x, centroid_y = calculate_centroid(positions)
    features['centroid_x'] = centroid_x
    features['centroid_y'] = centroid_y
    
    edge_distances = calculate_edge_distances(positions, rows, cols)
    features['edge_left'] = edge_distances['left']
    features['edge_right'] = edge_distances['right']
    features['edge_top'] = edge_distances['top']
    features['edge_bottom'] = edge_distances['bottom']
    
    features['center_distance'] = calculate_center_distance(positions, rows, cols)
    # 追加: 位置特徴量
    quadrant_dist = calculate_quadrant_distribution(positions, rows, cols)
    features['quadrant_top_left'] = quadrant_dist['quadrant_top_left']
    features['quadrant_top_right'] = quadrant_dist['quadrant_top_right']
    features['quadrant_bottom_left'] = quadrant_dist['quadrant_bottom_left']
    features['quadrant_bottom_right'] = quadrant_dist['quadrant_bottom_right']
    features['edge_proximity'] = calculate_edge_proximity(positions, rows, cols)
    
    # カテゴリ3: 関係性特徴（リハーサルがある場合のみ）
    if rehearsal_positions is not None:
        # 既存の特徴量
        features['rehearsal_distance'] = calculate_rehearsal_distance(
            positions, rehearsal_positions
        )
        features['overlap_count'] = calculate_overlap_count(
            positions, rehearsal_positions
        )
        features['inverse_ratio'] = calculate_inverse_ratio(
            positions, rehearsal_positions, grid
        )
        
        # 距離統計特徴量
        distance_stats = calculate_rehearsal_distance_stats(
            positions, rehearsal_positions
        )
        features['rehearsal_distance_mean'] = distance_stats['mean']
        features['rehearsal_distance_median'] = distance_stats['median']
        features['rehearsal_distance_q25'] = distance_stats['q25']
        features['rehearsal_distance_q75'] = distance_stats['q75']
        features['rehearsal_distance_min'] = distance_stats['min']
        features['rehearsal_distance_max'] = distance_stats['max']
        features['rehearsal_distance_std'] = distance_stats['std']
        features['rehearsal_distance_trimmed_mean'] = distance_stats['trimmed_mean']
        
        # 方向性特徴量
        direction_histogram = calculate_rehearsal_direction_histogram(
            positions, rehearsal_positions
        )
        features['rehearsal_direction_0'] = float(direction_histogram[0])  # 北
        features['rehearsal_direction_1'] = float(direction_histogram[1])  # 北東
        features['rehearsal_direction_2'] = float(direction_histogram[2])  # 東
        features['rehearsal_direction_3'] = float(direction_histogram[3])  # 南東
        features['rehearsal_direction_4'] = float(direction_histogram[4])  # 南
        features['rehearsal_direction_5'] = float(direction_histogram[5])  # 南西
        features['rehearsal_direction_6'] = float(direction_histogram[6])  # 西
        features['rehearsal_direction_7'] = float(direction_histogram[7])  # 北西
        
        features['rehearsal_primary_direction'] = float(calculate_rehearsal_primary_direction(
            positions, rehearsal_positions
        ))
        features['rehearsal_direction_concentration'] = calculate_rehearsal_direction_concentration(
            positions, rehearsal_positions
        )
        
        direction_ratio = calculate_rehearsal_direction_ratio(
            positions, rehearsal_positions
        )
        features['rehearsal_direction_ratio_0'] = direction_ratio[0]  # 北
        features['rehearsal_direction_ratio_1'] = direction_ratio[1]  # 北東
        features['rehearsal_direction_ratio_2'] = direction_ratio[2]  # 東
        features['rehearsal_direction_ratio_3'] = direction_ratio[3]  # 南東
        features['rehearsal_direction_ratio_4'] = direction_ratio[4]  # 南
        features['rehearsal_direction_ratio_5'] = direction_ratio[5]  # 南西
        features['rehearsal_direction_ratio_6'] = direction_ratio[6]  # 西
        features['rehearsal_direction_ratio_7'] = direction_ratio[7]  # 北西
        
        # 追加: 距離帯別特徴量
        distance_bins = calculate_rehearsal_distance_bins(positions, rehearsal_positions)
        features.update(distance_bins)
        
        # 追加: 角度特徴量
        features['rehearsal_angle'] = calculate_rehearsal_angle(positions, rehearsal_positions)
        
        # 桁ごとの重なり特徴量（rehearsal_digitsが必要）
        if rehearsal_digits is not None:
            overlap_info = calculate_rehearsal_overlap_by_digit(
                positions, rehearsal_digits, grid, rows, cols
            )
            features['rehearsal_overlap_by_digit_count'] = float(overlap_info['overlap_count'])
            features['rehearsal_overlap_by_digit_ratio'] = overlap_info['overlap_ratio']
            
            # 各桁の重なり数（N3の場合は3つ、N4の場合は4つ）
            overlap_by_digit = overlap_info['overlap_by_digit']
            for i, count in enumerate(overlap_by_digit):
                features[f'rehearsal_overlap_digit_{i}'] = float(count)
            
            # 残りの桁（N3の場合は3-3=0個、N4の場合は4-4=0個）は0で埋める
            digit_count = len(rehearsal_digits)
            for i in range(digit_count, 4):
                features[f'rehearsal_overlap_digit_{i}'] = 0.0
            
            features['rehearsal_full_match'] = calculate_rehearsal_full_match(
                positions, rehearsal_digits, grid, rows, cols
            )
            features['rehearsal_partial_match'] = float(calculate_rehearsal_partial_match(
                positions, rehearsal_digits, grid, rows, cols
            ))
            
            # 追加: 各桁ごとの距離統計特徴量
            digit_distance_stats = calculate_rehearsal_digit_distance_stats(
                positions, rehearsal_digits, grid, rows, cols
            )
            features.update(digit_distance_stats)
        else:
            # rehearsal_digitsがない場合のデフォルト値（全ての桁を0で埋める）
            features['rehearsal_overlap_by_digit_count'] = 0.0
            features['rehearsal_overlap_by_digit_ratio'] = 0.0
            # 全ての桁（0-3）を0で埋める
            for i in range(4):
                features[f'rehearsal_overlap_digit_{i}'] = 0.0
            features['rehearsal_full_match'] = 0.0
            features['rehearsal_partial_match'] = 0.0
            # 追加: 各桁ごとの距離統計特徴量のデフォルト値
            for i in range(4):
                features[f'rehearsal_digit_{i}_mean_distance'] = 999.0
    else:
        # リハーサルがない場合のデフォルト値
        features['rehearsal_distance'] = 999.0
        features['overlap_count'] = 0
        features['inverse_ratio'] = 0.0
        
        # 距離統計特徴量のデフォルト値
        features['rehearsal_distance_mean'] = 999.0
        features['rehearsal_distance_median'] = 999.0
        features['rehearsal_distance_q25'] = 999.0
        features['rehearsal_distance_q75'] = 999.0
        features['rehearsal_distance_min'] = 999.0
        features['rehearsal_distance_max'] = 999.0
        features['rehearsal_distance_std'] = 0.0
        features['rehearsal_distance_trimmed_mean'] = 999.0
        
        # 方向性特徴量のデフォルト値
        for i in range(8):
            features[f'rehearsal_direction_{i}'] = 0.0
            features[f'rehearsal_direction_ratio_{i}'] = 0.0
        features['rehearsal_primary_direction'] = 0.0
        features['rehearsal_direction_concentration'] = 0.0
        
        # 桁ごとの重なり特徴量のデフォルト値（全ての桁を0で埋める）
        features['rehearsal_overlap_by_digit_count'] = 0.0
        features['rehearsal_overlap_by_digit_ratio'] = 0.0
        # 全ての桁（0-3）を0で埋める
        for i in range(4):
            features[f'rehearsal_overlap_digit_{i}'] = 0.0
        features['rehearsal_full_match'] = 0.0
        features['rehearsal_partial_match'] = 0.0
        
        # 追加特徴量のデフォルト値
        features['rehearsal_distance_bin_0_1'] = 0.0
        features['rehearsal_distance_bin_1_2'] = 0.0
        features['rehearsal_distance_bin_2_3'] = 0.0
        features['rehearsal_distance_bin_3_plus'] = 0.0
        features['rehearsal_angle'] = 0.0
        for i in range(4):
            features[f'rehearsal_digit_{i}_mean_distance'] = 999.0
    
    # カテゴリ4: 集約特徴
    features['dispersion'] = calculate_dispersion(positions)
    features['bias'] = calculate_bias(positions, rows, cols)
    
    # 追加: N3/N4リハーサル数字の共通部分特徴量
    if n3_n4_common_rehearsal_digits is not None:
        # 候補数字が共通部分に含まれているか（1 or 0）
        features['n3_n4_common_rehearsal_contains'] = 1.0 if str(digit) in n3_n4_common_rehearsal_digits else 0.0
        # 共通部分のサイズ（0-10）
        features['n3_n4_common_rehearsal_size'] = float(len(n3_n4_common_rehearsal_digits))
    else:
        features['n3_n4_common_rehearsal_contains'] = 0.0
        features['n3_n4_common_rehearsal_size'] = 0.0
    
    return features


def extract_combination_features(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    combination: str,
    rehearsal_positions: Optional[List[Tuple[int, int]]] = None
) -> Dict[str, float]:
    """組み合わせに関する特徴量を抽出する
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        combination: 組み合わせ文字列（例: "147"）
        rehearsal_positions: リハーサル数字の位置リスト（オプション）
    
    Returns:
        特徴量の辞書
    """
    # 文字列型に変換（数値型の場合に備えて）
    combination_str = str(combination).replace('.0', '')
    digits = [int(d) for d in combination_str]
    
    # 各桁の位置を取得
    all_positions = []
    for digit in digits:
        positions = get_digit_positions(grid, rows, cols, digit)
        all_positions.extend(positions)
    
    features = {}
    
    # カテゴリ4: 集約特徴
    features['combination_frequency'] = calculate_combination_frequency(
        combination, grid, rows, cols
    )
    features['combination_dispersion'] = calculate_dispersion(all_positions)
    features['combination_bias'] = calculate_bias(all_positions, rows, cols)
    
    # 各桁の特徴量も追加
    for i, digit in enumerate(digits):
        digit_features = extract_digit_features(
            grid, rows, cols, digit, rehearsal_positions
        )
        for key, value in digit_features.items():
            features[f'digit_{i}_{key}'] = value
    
    return features


def add_pattern_id_features(
    features: Dict[str, float],
    pattern: Pattern
) -> Dict[str, float]:
    """パターンIDを特徴量として追加する（one-hot encoding）
    
    Args:
        features: 既存の特徴量辞書
        pattern: パターン（'A1' | 'A2' | 'B1' | 'B2'）
    
    Returns:
        パターンID特徴量を追加した特徴量辞書
    """
    # パターンIDのマッピング: A1=0, A2=1, B1=2, B2=3
    pattern_id_map = {
        'A1': 0,
        'A2': 1,
        'B1': 2,
        'B2': 3
    }
    
    pattern_id = pattern_id_map[pattern]
    
    # One-hot encoding（4次元）
    features['pattern_id'] = float(pattern_id)
    features['pattern_A1'] = 1.0 if pattern == 'A1' else 0.0
    features['pattern_A2'] = 1.0 if pattern == 'A2' else 0.0
    features['pattern_B1'] = 1.0 if pattern == 'B1' else 0.0
    features['pattern_B2'] = 1.0 if pattern == 'B2' else 0.0
    
    return features


def features_to_vector(features: Dict[str, float], feature_keys: Optional[List[str]] = None) -> np.ndarray:
    """特徴量辞書をベクトルに変換する
    
    Args:
        features: 特徴量辞書
        feature_keys: 使用する特徴量キーのリスト（指定された場合、この順序でベクトル化）
    
    Returns:
        特徴量ベクトル（numpy配列）
    """
    if feature_keys is not None:
        # 指定された特徴量キーの順序でベクトル化
        return np.array([features.get(key, 0.0) for key in feature_keys])
    else:
        # キーをソートして順序を固定
        sorted_keys = sorted(features.keys())
        return np.array([features[key] for key in sorted_keys])

