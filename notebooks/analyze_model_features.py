#!/usr/bin/env python3
"""
特徴量重要度分析スクリプト

学習済みモデルから特徴量重要度を抽出し、特徴量名とマッピングして分析します。
"""

import pickle
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # バックエンドを設定（GUIが不要な場合）

# プロジェクトルートのパスを設定
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()

DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'
DOCS_REPORT_DIR = PROJECT_ROOT / 'docs' / 'report'

# 出力ディレクトリを作成
DOCS_REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_model_and_features(model_name: str) -> Tuple:
    """モデルと特徴量キーを読み込む
    
    Args:
        model_name: モデル名（例: 'n3_axis', 'n4_axis'）
    
    Returns:
        (model, feature_keys) のタプル
    """
    model_path = MODELS_DIR / f'{model_name}.pkl'
    data_path = MODELS_DIR / f'{model_name}_data.pkl'
    
    # モデルを読み込む
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    # モデルデータが辞書の場合は、モデルと特徴量キーを分離
    if isinstance(model_data, dict):
        model = model_data.get('model', model_data)
        feature_keys = model_data.get('feature_keys', [])
    else:
        model = model_data
        feature_keys = []
    
    # データファイルから特徴量キーを取得（モデルファイルにない場合）
    if not feature_keys and data_path.exists():
        with open(data_path, 'rb') as f:
            data = pickle.load(f)
            feature_keys = data.get('feature_keys', [])
    
    return model, feature_keys


def categorize_features(feature_name: str) -> str:
    """特徴量をカテゴリに分類する
    
    Args:
        feature_name: 特徴量名
    
    Returns:
        カテゴリ名
    """
    # 新規特徴量の識別
    if 'diagonal_line_length' in feature_name or 'clustering_coefficient' in feature_name or 'shape_complexity' in feature_name:
        return '形状特徴（新規）'
    elif 'quadrant' in feature_name or 'edge_proximity' in feature_name:
        return '位置特徴（新規）'
    elif 'rehearsal_distance_bin' in feature_name or 'rehearsal_angle' in feature_name or 'rehearsal_digit_' in feature_name and 'mean_distance' in feature_name:
        return '関係性特徴（新規）'
    
    # 既存特徴量の分類
    if 'length' in feature_name or 'curvature' in feature_name or 'straightness' in feature_name or 'density' in feature_name:
        return '形状特徴'
    elif 'center' in feature_name or 'edge' in feature_name or 'centroid' in feature_name:
        return '位置特徴'
    elif 'distance' in feature_name or 'overlap' in feature_name or 'direction' in feature_name or 'rehearsal' in feature_name:
        return '関係性特徴'
    elif 'variance' in feature_name or 'skewness' in feature_name or 'dispersion' in feature_name or 'bias' in feature_name:
        return '集約特徴'
    elif 'pattern' in feature_name.lower():
        return 'パターンID'
    else:
        return 'その他'


def extract_feature_importance(model, feature_keys: List[str]) -> Dict:
    """特徴量重要度を抽出する
    
    Args:
        model: XGBoostモデル
        feature_keys: 特徴量キーのリスト
    
    Returns:
        特徴量重要度の辞書
    """
    # XGBoostのfeature_importances_を取得（gainタイプ）
    importances = model.feature_importances_
    
    # 特徴量キーが空の場合は、インデックスを使用
    if not feature_keys:
        feature_keys = [f'feature_{i}' for i in range(len(importances))]
    
    # 特徴量名と重要度をマッピング
    feature_importance_dict = {}
    for i, (key, importance) in enumerate(zip(feature_keys, importances)):
        feature_importance_dict[key] = {
            'importance': float(importance),
            'rank': 0,  # 後で設定
            'category': categorize_features(key)
        }
    
    # 重要度でソートしてランクを設定
    sorted_features = sorted(
        feature_importance_dict.items(),
        key=lambda x: x[1]['importance'],
        reverse=True
    )
    
    for rank, (key, _) in enumerate(sorted_features, 1):
        feature_importance_dict[key]['rank'] = rank
    
    return feature_importance_dict


def aggregate_by_category(feature_importance_dict: Dict) -> Dict[str, float]:
    """カテゴリ別に重要度を集計する
    
    Args:
        feature_importance_dict: 特徴量重要度の辞書
    
    Returns:
        カテゴリ別の重要度合計
    """
    category_importance = {}
    for key, data in feature_importance_dict.items():
        category = data['category']
        if category not in category_importance:
            category_importance[category] = 0.0
        category_importance[category] += data['importance']
    
    return category_importance


def save_feature_importance_json(feature_importance_dict: Dict, output_path: Path):
    """特徴量重要度をJSONファイルに保存する
    
    Args:
        feature_importance_dict: 特徴量重要度の辞書
        output_path: 出力ファイルパス
    """
    # JSON形式に変換（ランク順にソート）
    sorted_features = sorted(
        feature_importance_dict.items(),
        key=lambda x: x[1]['rank']
    )
    
    output_data = {
        'features': [
            {
                'name': key,
                'importance': data['importance'],
                'rank': data['rank'],
                'category': data['category']
            }
            for key, data in sorted_features
        ],
        'category_summary': aggregate_by_category(feature_importance_dict)
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def visualize_feature_importance(feature_importance_dict: Dict, output_path: Path, top_n: int = 20):
    """特徴量重要度を可視化する
    
    Args:
        feature_importance_dict: 特徴量重要度の辞書
        output_path: 出力ファイルパス
        top_n: 上位N件を表示
    """
    # 上位N件を取得
    sorted_features = sorted(
        feature_importance_dict.items(),
        key=lambda x: x[1]['importance'],
        reverse=True
    )[:top_n]
    
    # データを準備
    feature_names = [key for key, _ in sorted_features]
    importances = [data['importance'] for _, data in sorted_features]
    categories = [data['category'] for _, data in sorted_features]
    
    # 日本語フォントの設定（Windows環境）
    plt.rcParams['font.family'] = 'DejaVu Sans'
    
    # 棒グラフを作成
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = plt.cm.Set3(np.linspace(0, 1, len(set(categories))))
    category_color_map = {cat: colors[i] for i, cat in enumerate(set(categories))}
    bar_colors = [category_color_map[cat] for cat in categories]
    
    bars = ax.barh(range(len(feature_names)), importances, color=bar_colors)
    ax.set_yticks(range(len(feature_names)))
    ax.set_yticklabels(feature_names)
    ax.set_xlabel('Feature Importance', fontsize=12)
    ax.set_title(f'Top {top_n} Feature Importances', fontsize=14, fontweight='bold')
    ax.invert_yaxis()  # 重要度が高い順に上から表示
    
    # 凡例を追加
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=category_color_map[cat], label=cat)
        for cat in set(categories)
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def visualize_category_importance(category_importance_dict: Dict, output_path: Path):
    """カテゴリ別重要度を円グラフで可視化する
    
    Args:
        category_importance_dict: カテゴリ別重要度の辞書
        output_path: 出力ファイルパス
    """
    # データを準備
    categories = list(category_importance_dict.keys())
    importances = list(category_importance_dict.values())
    
    # 日本語フォントの設定
    plt.rcParams['font.family'] = 'DejaVu Sans'
    
    # 円グラフを作成
    fig, ax = plt.subplots(figsize=(8, 8))
    colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
    
    wedges, texts, autotexts = ax.pie(
        importances,
        labels=categories,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors
    )
    
    ax.set_title('Feature Importance by Category', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def main():
    """メイン関数"""
    print("="*80)
    print("特徴量重要度分析スクリプト")
    print("="*80)
    
    # N3とN4の軸数字予測モデルを分析
    for model_name in ['n3_axis', 'n4_axis']:
        print(f"\n{'='*80}")
        print(f"分析中: {model_name}")
        print(f"{'='*80}")
        
        try:
            # モデルと特徴量キーを読み込む
            model, feature_keys = load_model_and_features(model_name)
            
            print(f"モデル読み込み完了")
            print(f"特徴量数: {len(feature_keys) if feature_keys else model.n_features_in_}")
            
            # 特徴量重要度を抽出
            feature_importance_dict = extract_feature_importance(model, feature_keys)
            
            print(f"特徴量重要度抽出完了")
            print(f"特徴量数: {len(feature_importance_dict)}")
            
            # カテゴリ別集計
            category_importance = aggregate_by_category(feature_importance_dict)
            print(f"\nカテゴリ別重要度:")
            for category, importance in sorted(category_importance.items(), key=lambda x: x[1], reverse=True):
                print(f"  {category}: {importance:.6f}")
            
            # 上位10位の特徴量を表示
            sorted_features = sorted(
                feature_importance_dict.items(),
                key=lambda x: x[1]['importance'],
                reverse=True
            )[:10]
            
            print(f"\n上位10位の特徴量:")
            for rank, (key, data) in enumerate(sorted_features, 1):
                print(f"  {rank}. {key}: {data['importance']:.6f} ({data['category']})")
            
            # JSONファイルに保存
            output_json_path = DOCS_REPORT_DIR / f'feature_importance_{model_name}.json'
            save_feature_importance_json(feature_importance_dict, output_json_path)
            print(f"\n特徴量重要度を保存しました: {output_json_path}")
            
            # 可視化
            try:
                output_img_path = DOCS_REPORT_DIR / f'feature_importance_{model_name}.png'
                visualize_feature_importance(feature_importance_dict, output_img_path, top_n=20)
                print(f"特徴量重要度グラフを保存しました: {output_img_path}")
                
                output_category_path = DOCS_REPORT_DIR / f'category_importance_{model_name}.png'
                visualize_category_importance(category_importance, output_category_path)
                print(f"カテゴリ別重要度グラフを保存しました: {output_category_path}")
            except Exception as e:
                print(f"警告: 可視化中にエラーが発生しました: {e}")
            
        except Exception as e:
            print(f"エラー: {model_name}の分析に失敗しました: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("分析完了")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()

