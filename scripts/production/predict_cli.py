#!/usr/bin/env python3
"""
予測実行CLIツール

回号とリハーサル数字を入力して、AI予測結果を表示します。

使用方法:
    python predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782
    または
    python predict_cli.py
    (対話的に入力を受け取る)
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import numpy as np
import pandas as pd

# プロジェクトルートのパスを設定
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    # Jupyter Notebookなどで実行される場合
    PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.append(str(PROJECT_ROOT / 'core'))

from chart_generator import (
    load_keisen_master,
    generate_chart,
    Pattern,
    Target
)
from feature_extractor import (
    extract_digit_features,
    extract_combination_features,
    add_pattern_id_features,
    features_to_vector,
    get_rehearsal_positions
)
from model_loader import load_model_loader


def load_data(data_dir: Path) -> Tuple[pd.DataFrame, dict]:
    """過去データと罫線マスターデータを読み込む
    
    Args:
        data_dir: データディレクトリ
    
    Returns:
        (過去データDataFrame, 罫線マスターデータ)
    """
    csv_path = data_dir / 'past_results.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f"データファイルが見つかりません: {csv_path}")
    
    df = pd.read_csv(csv_path)
    df = df.sort_values('round_number', ascending=False).reset_index(drop=True)
    
    keisen_master = load_keisen_master(data_dir)
    
    return df, keisen_master


def predict_axis_digits(
    df: pd.DataFrame,
    keisen_master: dict,
    model_loader,
    round_number: int,
    target: Target,
    rehearsal_digits: Optional[str] = None
) -> Dict[Pattern, List[Tuple[int, float]]]:
    """軸数字を予測する
    
    Args:
        df: 過去データ
        keisen_master: 罫線マスターデータ
        model_loader: モデルローダー
        round_number: 回号
        target: 対象（'n3' または 'n4'）
        rehearsal_digits: リハーサル数字（オプション）
    
    Returns:
        パターン別の軸数字予測結果（(数字, スコア)のリスト）
    """
    patterns: List[Pattern] = ['A1', 'A2', 'B1', 'B2']
    results = {}
    
    for pattern in patterns:
        try:
            # 予測表を生成
            grid, rows, cols = generate_chart(
                df, keisen_master, round_number, pattern, target
            )
            
            # リハーサル位置を取得
            rehearsal_positions = None
            if rehearsal_digits:
                rehearsal_positions = get_rehearsal_positions(
                    grid, rows, cols, rehearsal_digits
                )
            
            # 各数字（0-9）の特徴量を抽出
            digit_scores = []
            for digit in range(10):
                features = extract_digit_features(
                    grid, rows, cols, digit, rehearsal_positions
                )
                features = add_pattern_id_features(features, pattern)
                
                # 特徴量辞書から直接予測（自動次元調整対応）
                proba = model_loader.predict_axis_from_dict(
                    target, features
                )
                
                # スコア算出（確率 × 1000）
                score = proba * 1000
                digit_scores.append((digit, score))
            
            # スコア順にソート（降順）
            digit_scores.sort(key=lambda x: x[1], reverse=True)
            results[pattern] = digit_scores
            
        except Exception as e:
            print(f"エラー: パターン{pattern}の予測に失敗しました: {e}")
            results[pattern] = []
    
    return results


def predict_combinations(
    df: pd.DataFrame,
    keisen_master: dict,
    model_loader,
    round_number: int,
    target: Target,
    combo_type: str,
    best_pattern: Pattern,
    top_axis_digits: List[int],
    rehearsal_digits: Optional[str] = None,
    max_combinations: int = 100
) -> List[Tuple[str, float]]:
    """組み合わせを予測する
    
    Args:
        df: 過去データ
        keisen_master: 罫線マスターデータ
        model_loader: モデルローダー
        round_number: 回号
        target: 対象（'n3' または 'n4'）
        combo_type: 組み合わせタイプ（'box' または 'straight'）
        best_pattern: 最良パターン
        top_axis_digits: 上位軸数字のリスト
        rehearsal_digits: リハーサル数字（オプション）
        max_combinations: 最大組み合わせ数
    
    Returns:
        組み合わせ予測結果（(組み合わせ, スコア)のリスト）
    """
    try:
        # 予測表を生成
        grid, rows, cols = generate_chart(
            df, keisen_master, round_number, best_pattern, target
        )
        
        # リハーサル位置を取得
        rehearsal_positions = None
        if rehearsal_digits:
            rehearsal_positions = get_rehearsal_positions(
                grid, rows, cols, rehearsal_digits
            )
        
        # 組み合わせを生成（軸数字を含む組み合わせを優先）
        digit_count = 3 if target == 'n3' else 4
        combinations = []
        
        # 軸数字を含む組み合わせを生成
        for axis_digit in top_axis_digits[:5]:  # 上位5つの軸数字を使用
            other_digits = [d for d in range(10) if d != axis_digit]
            
            if target == 'n3':
                # N3: 軸数字 + 他の2数字
                for i, d1 in enumerate(other_digits):
                    for d2 in other_digits[i+1:]:
                        combo = ''.join(map(str, sorted([axis_digit, d1, d2])))
                        if combo not in combinations:
                            combinations.append(combo)
            else:
                # N4: 軸数字 + 他の3数字
                for i, d1 in enumerate(other_digits):
                    for j, d2 in enumerate(other_digits[i+1:]):
                        for d3 in other_digits[i+j+2:]:
                            combo = ''.join(map(str, sorted([axis_digit, d1, d2, d3])))
                            if combo not in combinations:
                                combinations.append(combo)
            
            if len(combinations) >= max_combinations:
                break
        
        # 特徴量を抽出して予測
        combo_scores = []
        for combo in combinations[:max_combinations]:
            features = extract_combination_features(
                grid, rows, cols, combo, rehearsal_positions
            )
            features = add_pattern_id_features(features, best_pattern)
            
            # 特徴量辞書から直接予測（自動次元調整対応）
            proba = model_loader.predict_combination_from_dict(
                target, combo_type, features
            )
            
            # スコア算出（確率 × 1000）
            score = proba * 1000
            combo_scores.append((combo, score))
        
        # スコア順にソート（降順）
        combo_scores.sort(key=lambda x: x[1], reverse=True)
        return combo_scores
        
    except Exception as e:
        print(f"エラー: 組み合わせ予測に失敗しました: {e}")
        return []


def print_results(
    round_number: int,
    n3_rehearsal: Optional[str],
    n4_rehearsal: Optional[str],
    n3_results: Dict[str, Dict],
    n4_results: Dict[str, Dict]
):
    """結果を表示する
    
    Args:
        round_number: 回号
        n3_rehearsal: N3リハーサル数字
        n4_rehearsal: N4リハーサル数字
        n3_results: N3の予測結果
        n4_results: N4の予測結果
    """
    print("\n" + "="*80)
    print(f"予測結果 - 回号: {round_number}")
    print("="*80)
    
    if n3_rehearsal:
        print(f"N3リハーサル: {n3_rehearsal}")
    if n4_rehearsal:
        print(f"N4リハーサル: {n4_rehearsal}")
    
    # N3の結果を表示
    print("\n" + "-"*80)
    print("N3予測結果")
    print("-"*80)
    
    for combo_type in ['box', 'straight']:
        print(f"\n[{combo_type.upper()}]")
        
        if combo_type in n3_results:
            result = n3_results[combo_type]
            
            # 軸数字予測結果
            print("\n軸数字予測（パターン別）:")
            for pattern in ['A1', 'A2', 'B1', 'B2']:
                if pattern in result.get('axis_by_pattern', {}):
                    axis_scores = result['axis_by_pattern'][pattern]
                    print(f"  {pattern}: {', '.join([f'{d}({s:.0f})' for d, s in axis_scores[:5]])}")
            
            # 最良パターン
            if 'best_pattern' in result:
                print(f"\n最良パターン: {result['best_pattern']}")
            
            # 軸数字ランキング
            if 'axis_candidates' in result:
                print("\n軸数字ランキング:")
                for i, (digit, score) in enumerate(result['axis_candidates'][:10], 1):
                    print(f"  {i:2d}. 数字{digit}: スコア{score:.0f}")
            
            # 組み合わせランキング
            if 'combinations' in result:
                print("\n組み合わせランキング（上位10件）:")
                for i, (combo, score) in enumerate(result['combinations'][:10], 1):
                    print(f"  {i:2d}. {combo}: スコア{score:.0f}")
    
    # N4の結果を表示
    print("\n" + "-"*80)
    print("N4予測結果")
    print("-"*80)
    
    for combo_type in ['box', 'straight']:
        print(f"\n[{combo_type.upper()}]")
        
        if combo_type in n4_results:
            result = n4_results[combo_type]
            
            # 軸数字予測結果
            print("\n軸数字予測（パターン別）:")
            for pattern in ['A1', 'A2', 'B1', 'B2']:
                if pattern in result.get('axis_by_pattern', {}):
                    axis_scores = result['axis_by_pattern'][pattern]
                    print(f"  {pattern}: {', '.join([f'{d}({s:.0f})' for d, s in axis_scores[:5]])}")
            
            # 最良パターン
            if 'best_pattern' in result:
                print(f"\n最良パターン: {result['best_pattern']}")
            
            # 軸数字ランキング
            if 'axis_candidates' in result:
                print("\n軸数字ランキング:")
                for i, (digit, score) in enumerate(result['axis_candidates'][:10], 1):
                    print(f"  {i:2d}. 数字{digit}: スコア{score:.0f}")
            
            # 組み合わせランキング
            if 'combinations' in result:
                print("\n組み合わせランキング（上位10件）:")
                for i, (combo, score) in enumerate(result['combinations'][:10], 1):
                    print(f"  {i:2d}. {combo}: スコア{score:.0f}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='ナンバーズAI予測CLIツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782
  python predict_cli.py --round 6758 --n3-rehearsal 149
  python predict_cli.py
        """
    )
    
    parser.add_argument(
        '--round',
        type=int,
        help='回号'
    )
    parser.add_argument(
        '--n3-rehearsal',
        type=str,
        help='N3リハーサル数字（3桁）'
    )
    parser.add_argument(
        '--n4-rehearsal',
        type=str,
        help='N4リハーサル数字（4桁）'
    )
    
    args = parser.parse_args()
    
    # 対話的に入力を受け取る
    if args.round is None:
        try:
            round_number = int(input("回号を入力してください: "))
        except ValueError:
            print("エラー: 有効な回号を入力してください")
            sys.exit(1)
    else:
        round_number = args.round
    
    n3_rehearsal = args.n3_rehearsal
    n4_rehearsal = args.n4_rehearsal
    
    if n3_rehearsal is None:
        n3_rehearsal = input("N3リハーサル数字を入力してください（3桁、Enterでスキップ）: ").strip()
        if not n3_rehearsal:
            n3_rehearsal = None
    
    if n4_rehearsal is None:
        n4_rehearsal = input("N4リハーサル数字を入力してください（4桁、Enterでスキップ）: ").strip()
        if not n4_rehearsal:
            n4_rehearsal = None
    
    # データとモデルを読み込む
    print("\nデータとモデルを読み込み中...")
    try:
        DATA_DIR = PROJECT_ROOT / 'data'
        MODELS_DIR = DATA_DIR / 'models'
        
        df, keisen_master = load_data(DATA_DIR)
        model_loader = load_model_loader(MODELS_DIR)
        
        print("✓ データとモデルの読み込み完了")
    except Exception as e:
        print(f"エラー: データまたはモデルの読み込みに失敗しました: {e}")
        sys.exit(1)
    
    # 予測実行
    print("\n予測を実行中...")
    n3_results = {}
    n4_results = {}
    
    # N3の予測
    if n3_rehearsal:
        print("\nN3予測中...")
        axis_results = predict_axis_digits(
            df, keisen_master, model_loader, round_number, 'n3', n3_rehearsal
        )
        
        # 最良パターンを特定（軸数字の最高スコアが最も高いパターン）
        best_pattern_n3 = None
        best_score_n3 = -1
        
        for pattern, digit_scores in axis_results.items():
            if digit_scores:
                max_score = max(s for _, s in digit_scores)
                if max_score > best_score_n3:
                    best_score_n3 = max_score
                    best_pattern_n3 = pattern
        
        if best_pattern_n3:
            # 軸数字ランキング（全パターン統合）
            all_axis_scores = {}
            for pattern, digit_scores in axis_results.items():
                for digit, score in digit_scores:
                    if digit not in all_axis_scores or score > all_axis_scores[digit][1]:
                        all_axis_scores[digit] = (pattern, score)
            
            axis_candidates = [(d, s) for d, (p, s) in sorted(all_axis_scores.items(), key=lambda x: x[1][1], reverse=True)]
            top_axis_digits = [d for d, _ in axis_candidates[:10]]
            
            # 組み合わせ予測
            for combo_type in ['box', 'straight']:
                combinations = predict_combinations(
                    df, keisen_master, model_loader, round_number, 'n3',
                    combo_type, best_pattern_n3, top_axis_digits, n3_rehearsal
                )
                
                n3_results[combo_type] = {
                    'axis_by_pattern': axis_results,
                    'best_pattern': best_pattern_n3,
                    'axis_candidates': axis_candidates,
                    'combinations': combinations
                }
    
    # N4の予測
    if n4_rehearsal:
        print("\nN4予測中...")
        axis_results = predict_axis_digits(
            df, keisen_master, model_loader, round_number, 'n4', n4_rehearsal
        )
        
        # 最良パターンを特定
        best_pattern_n4 = None
        best_score_n4 = -1
        
        for pattern, digit_scores in axis_results.items():
            if digit_scores:
                max_score = max(s for _, s in digit_scores)
                if max_score > best_score_n4:
                    best_score_n4 = max_score
                    best_pattern_n4 = pattern
        
        if best_pattern_n4:
            # 軸数字ランキング（全パターン統合）
            all_axis_scores = {}
            for pattern, digit_scores in axis_results.items():
                for digit, score in digit_scores:
                    if digit not in all_axis_scores or score > all_axis_scores[digit][1]:
                        all_axis_scores[digit] = (pattern, score)
            
            axis_candidates = [(d, s) for d, (p, s) in sorted(all_axis_scores.items(), key=lambda x: x[1][1], reverse=True)]
            top_axis_digits = [d for d, _ in axis_candidates[:10]]
            
            # 組み合わせ予測
            for combo_type in ['box', 'straight']:
                combinations = predict_combinations(
                    df, keisen_master, model_loader, round_number, 'n4',
                    combo_type, best_pattern_n4, top_axis_digits, n4_rehearsal
                )
                
                n4_results[combo_type] = {
                    'axis_by_pattern': axis_results,
                    'best_pattern': best_pattern_n4,
                    'axis_candidates': axis_candidates,
                    'combinations': combinations
                }
    
    # 結果を表示
    print_results(round_number, n3_rehearsal, n4_rehearsal, n3_results, n4_results)


if __name__ == '__main__':
    main()

