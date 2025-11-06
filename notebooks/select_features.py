#!/usr/bin/env python3
"""
特徴量重要度分析と削除スクリプト

重要度の低い特徴量を特定し、削除リストを生成します。
"""

import json
from pathlib import Path
from typing import List, Set, Dict

PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
DOCS_REPORT_DIR = PROJECT_ROOT / 'docs' / 'report'

def load_feature_importance(model_name: str) -> Dict[str, float]:
    """特徴量重要度を読み込む"""
    json_path = DOCS_REPORT_DIR / f'feature_importance_{model_name}.json'
    
    if not json_path.exists():
        return {}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    feature_importance = {}
    for feature in data.get('features', []):
        feature_importance[feature['name']] = feature['importance']
    
    return feature_importance

def select_features_by_importance(
    n3_importance: Dict[str, float],
    n4_importance: Dict[str, float],
    importance_threshold: float = 0.010  # 重要度が0.010未満の特徴量を削除
) -> List[str]:
    """重要度に基づいて特徴量を選択する
    
    Args:
        n3_importance: N3モデルの特徴量重要度
        n4_importance: N4モデルの特徴量重要度
        importance_threshold: 重要度の閾値（これ未満の特徴量を削除）
    
    Returns:
        選択された特徴量のリスト
    """
    all_features = set(list(n3_importance.keys()) + list(n4_importance.keys()))
    selected_features = set()
    
    # 各特徴量の最大重要度を計算
    feature_max_importance = {}
    for feature_name in all_features:
        n3_imp = n3_importance.get(feature_name, 0.0)
        n4_imp = n4_importance.get(feature_name, 0.0)
        feature_max_importance[feature_name] = max(n3_imp, n4_imp)
    
    # 重要度が閾値を超えている特徴量を選択
    for feature_name in all_features:
        max_imp = feature_max_importance[feature_name]
        
        # 重要度が閾値を超えている場合、選択
        if max_imp >= importance_threshold:
            selected_features.add(feature_name)
    
    # パターンIDは常に保持（カテゴリとして重要）
    for feature_name in all_features:
        if 'pattern' in feature_name.lower():
            selected_features.add(feature_name)
    
    # 新規追加した特徴量（N3/N4共通リハーサル特徴量）は常に保持
    for feature_name in all_features:
        if 'n3_n4_common_rehearsal' in feature_name:
            selected_features.add(feature_name)
    
    return sorted(list(selected_features))

def main():
    """メイン関数"""
    print("="*80)
    print("特徴量選択スクリプト")
    print("="*80)
    
    # 特徴量重要度を読み込む
    print("\n特徴量重要度を読み込み中...")
    n3_importance = load_feature_importance('n3_axis')
    n4_importance = load_feature_importance('n4_axis')
    
    print(f"N3モデルの特徴量数: {len(n3_importance)}")
    print(f"N4モデルの特徴量数: {len(n4_importance)}")
    
    # 各特徴量の最大重要度を計算して表示
    all_features = set(list(n3_importance.keys()) + list(n4_importance.keys()))
    feature_max_importance = {}
    for feature_name in all_features:
        n3_imp = n3_importance.get(feature_name, 0.0)
        n4_imp = n4_importance.get(feature_name, 0.0)
        feature_max_importance[feature_name] = max(n3_imp, n4_imp)
    
    sorted_features = sorted(feature_max_importance.items(), key=lambda x: x[1])
    
    print(f"\n重要度の低い特徴量（下位20個）:")
    for i, (name, imp) in enumerate(sorted_features[:20], 1):
        print(f"  {i:2d}. {name}: {imp:.6f}")
    
    # 重要度が0.010未満の特徴量数をカウント
    low_importance_count = sum(1 for imp in feature_max_importance.values() if imp < 0.010)
    print(f"\n重要度 < 0.010 の特徴量数: {low_importance_count}")
    
    # 重要度に基づいて特徴量を選択
    print("\n重要度に基づいて特徴量を選択中...")
    selected_features = select_features_by_importance(
        n3_importance, n4_importance,
        importance_threshold=0.010  # 重要度が0.010未満の特徴量を削除
    )
    
    print(f"\n選択された特徴量数: {len(selected_features)}")
    print(f"削除された特徴量数: {len(all_features) - len(selected_features)}")
    
    # 削除された特徴量を表示
    removed_features = sorted(all_features - set(selected_features))
    
    if removed_features:
        print(f"\n削除された特徴量:")
        for feature in removed_features:
            max_imp = feature_max_importance[feature]
            print(f"  {feature}: {max_imp:.6f}")
    
    # 選択された特徴量をJSONファイルに保存
    output_path = DOCS_REPORT_DIR / 'selected_features.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'selected_features': selected_features,
            'removed_features': removed_features,
            'total_features': len(all_features),
            'selected_count': len(selected_features),
            'removed_count': len(removed_features),
            'importance_threshold': 0.010
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n選択された特徴量を保存しました: {output_path}")
    
    # 選択された特徴量をテキストファイルにも保存
    output_txt_path = DOCS_REPORT_DIR / 'selected_features.txt'
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        for feature in selected_features:
            f.write(f"{feature}\n")
    
    print(f"選択された特徴量をテキストファイルに保存しました: {output_txt_path}")

if __name__ == '__main__':
    main()
