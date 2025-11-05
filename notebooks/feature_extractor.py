"""
特徴量エンジニアリングモジュール

予測表から特徴量を抽出し、AIモデル用のベクトルを生成します。
"""

from typing import List, Optional, Tuple, Dict, Literal
import numpy as np
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


# ==================== カテゴリ3: 関係性特徴 ====================

def calculate_rehearsal_distance(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]]
) -> float:
    """リハーサルとの平均距離を計算する
    
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


def calculate_inverse_ratio(
    candidate_positions: List[Tuple[int, int]],
    rehearsal_positions: List[Tuple[int, int]],
    grid: List[List[Optional[int]]]
) -> float:
    """候補がリハーサルの裏数字である割合を計算する
    
    Args:
        candidate_positions: 候補数字の位置リスト
        rehearsal_positions: リハーサル数字の位置リスト
        grid: 予測表グリッド（1-indexed）
    
    Returns:
        裏数字の割合（0-1）
    """
    if len(candidate_positions) == 0:
        return 0.0
    
    inverse_count = 0
    for r_pos in rehearsal_positions:
        rehearsal_digit = grid[r_pos[0]][r_pos[1]]
        if rehearsal_digit is not None:
            inverse_digit = inverse(rehearsal_digit)
            if (r_pos[0], r_pos[1]) in candidate_positions:
                # 同じ位置の候補が裏数字かチェック
                candidate_digit = grid[r_pos[0]][r_pos[1]]
                if candidate_digit == inverse_digit:
                    inverse_count += 1
    
    return inverse_count / len(candidate_positions) if len(candidate_positions) > 0 else 0.0


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

def extract_digit_features(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    digit: int,
    rehearsal_positions: Optional[List[Tuple[int, int]]] = None
) -> Dict[str, float]:
    """1つの数字に関する特徴量を抽出する
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        digit: 対象数字（0-9）
        rehearsal_positions: リハーサル数字の位置リスト（オプション）
    
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
    
    # カテゴリ3: 関係性特徴（リハーサルがある場合のみ）
    if rehearsal_positions is not None:
        features['rehearsal_distance'] = calculate_rehearsal_distance(
            positions, rehearsal_positions
        )
        features['overlap_count'] = calculate_overlap_count(
            positions, rehearsal_positions
        )
        features['inverse_ratio'] = calculate_inverse_ratio(
            positions, rehearsal_positions, grid
        )
    else:
        features['rehearsal_distance'] = 999.0
        features['overlap_count'] = 0
        features['inverse_ratio'] = 0.0
    
    # カテゴリ4: 集約特徴
    features['dispersion'] = calculate_dispersion(positions)
    features['bias'] = calculate_bias(positions, rows, cols)
    
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


def features_to_vector(features: Dict[str, float]) -> np.ndarray:
    """特徴量辞書をベクトルに変換する
    
    Args:
        features: 特徴量辞書
    
    Returns:
        特徴量ベクトル（numpy配列）
    """
    # キーをソートして順序を固定
    sorted_keys = sorted(features.keys())
    return np.array([features[key] for key in sorted_keys])

