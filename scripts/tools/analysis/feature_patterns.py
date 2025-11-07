"""
特徴量エンジニアリング実験用モジュール

異なる特徴量セットを比較し、最適な特徴量セットを決定するための機能を提供します。
"""

from typing import Dict, List, Optional, Tuple, Literal
import numpy as np
from feature_extractor import (
    extract_digit_features,
    extract_combination_features,
    add_pattern_id_features,
    get_rehearsal_positions
)

Pattern = Literal['A1', 'A2', 'B1', 'B2']
Target = Literal['n3', 'n4']

# 特徴量セットのパターン定義
FEATURE_PATTERNS = {
    'shape_only': {
        'name': '形状特徴のみ',
        'categories': ['shape'],
        'include_pattern_id': False
    },
    'position_only': {
        'name': '位置特徴のみ',
        'categories': ['position'],
        'include_pattern_id': False
    },
    'relationship_only': {
        'name': '関係性特徴のみ',
        'categories': ['relationship'],
        'include_pattern_id': False
    },
    'aggregate_only': {
        'name': '集約特徴のみ',
        'categories': ['aggregate'],
        'include_pattern_id': False
    },
    'shape_position': {
        'name': '形状+位置特徴',
        'categories': ['shape', 'position'],
        'include_pattern_id': False
    },
    'shape_position_relationship': {
        'name': '形状+位置+関係性特徴',
        'categories': ['shape', 'position', 'relationship'],
        'include_pattern_id': False
    },
    'all_features': {
        'name': '全特徴量（既存）',
        'categories': ['shape', 'position', 'relationship', 'aggregate'],
        'include_pattern_id': False
    },
    'all_with_pattern_id': {
        'name': '全特徴量+パターンID',
        'categories': ['shape', 'position', 'relationship', 'aggregate'],
        'include_pattern_id': True
    },
    'shape_position_pattern_id': {
        'name': '形状+位置+パターンID',
        'categories': ['shape', 'position'],
        'include_pattern_id': True
    },
    'all_no_pattern_id': {
        'name': '全特徴量（パターンIDなし）',
        'categories': ['shape', 'position', 'relationship', 'aggregate'],
        'include_pattern_id': False
    }
}

# 注意: 'all_features'と'all_no_pattern_id'は同じ特徴量セットですが、
# 将来的な拡張のため両方定義しています


def extract_digit_features_by_pattern(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    digit: int,
    pattern: Pattern,
    rehearsal_positions: Optional[List[Tuple[int, int]]] = None,
    feature_pattern: str = 'all_features'
) -> Dict[str, float]:
    """指定された特徴量パターンで数字の特徴量を抽出する
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        digit: 対象数字（0-9）
        pattern: パターン（'A1' | 'A2' | 'B1' | 'B2'）
        rehearsal_positions: リハーサル数字の位置リスト（オプション）
        feature_pattern: 特徴量パターン名（FEATURE_PATTERNSのキー）
    
    Returns:
        特徴量の辞書
    """
    # まず全特徴量を抽出
    all_features = extract_digit_features(
        grid, rows, cols, digit, rehearsal_positions
    )
    
    # パターン定義を取得
    pattern_def = FEATURE_PATTERNS.get(feature_pattern, FEATURE_PATTERNS['all_features'])
    categories = pattern_def['categories']
    include_pattern_id = pattern_def['include_pattern_id']
    
    # 特徴量カテゴリのマッピング
    category_mapping = {
        'shape': [
            'max_line_length',
            'turn_count',
            'straightness',
            'density'
        ],
        'position': [
            'centroid_x',
            'centroid_y',
            'edge_left',
            'edge_right',
            'edge_top',
            'edge_bottom',
            'center_distance'
        ],
        'relationship': [
            'rehearsal_distance',
            'overlap_count',
            'inverse_ratio'
        ],
        'aggregate': [
            'dispersion',
            'bias'
        ]
    }
    
    # 選択された特徴量のみを抽出
    selected_features = {}
    for category in categories:
        if category in category_mapping:
            for feature_name in category_mapping[category]:
                if feature_name in all_features:
                    selected_features[feature_name] = all_features[feature_name]
    
    # パターンID特徴量を追加（指定された場合）
    if include_pattern_id:
        selected_features = add_pattern_id_features(selected_features, pattern)
    
    return selected_features


def extract_combination_features_by_pattern(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    combination: str,
    pattern: Pattern,
    rehearsal_positions: Optional[List[Tuple[int, int]]] = None,
    feature_pattern: str = 'all_features'
) -> Dict[str, float]:
    """指定された特徴量パターンで組み合わせの特徴量を抽出する
    
    Args:
        grid: 予測表グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        combination: 組み合わせ文字列（例: "147"）
        pattern: パターン（'A1' | 'A2' | 'B1' | 'B2'）
        rehearsal_positions: リハーサル数字の位置リスト（オプション）
        feature_pattern: 特徴量パターン名（FEATURE_PATTERNSのキー）
    
    Returns:
        特徴量の辞書
    """
    # まず全特徴量を抽出
    all_features = extract_combination_features(
        grid, rows, cols, combination, rehearsal_positions
    )
    
    # パターン定義を取得
    pattern_def = FEATURE_PATTERNS.get(feature_pattern, FEATURE_PATTERNS['all_features'])
    categories = pattern_def['categories']
    include_pattern_id = pattern_def['include_pattern_id']
    
    # 特徴量カテゴリのマッピング（組み合わせ用）
    # 注意: 組み合わせ特徴量は各桁の特徴量から構成されるため、
    # ここでは全特徴量を含む（各桁の特徴量カテゴリは既に適用済み）
    selected_features = {}
    
    # 全特徴量から選択（各桁の特徴量名に基づいてフィルタリング）
    # 簡易実装: 全ての特徴量を含める（実装の詳細に応じて調整が必要）
    for key, value in all_features.items():
        selected_features[key] = value
    
    # パターンID特徴量を追加（指定された場合）
    if include_pattern_id:
        selected_features = add_pattern_id_features(selected_features, pattern)
    
    return selected_features


def get_feature_pattern_names() -> List[str]:
    """利用可能な特徴量パターン名のリストを取得する"""
    return list(FEATURE_PATTERNS.keys())


def get_feature_pattern_info(pattern_name: str) -> Dict:
    """特徴量パターンの情報を取得する"""
    return FEATURE_PATTERNS.get(pattern_name, {})

