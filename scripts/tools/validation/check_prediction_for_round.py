#!/usr/bin/env python3
"""
過去回号での予測結果を確認するCLIツール

特定の回号で予測を実行し、実際の当選番号と比較します。

使用方法:
    python check_prediction_for_round.py --round 6847                    # 6847回の予測結果を確認
    python check_prediction_for_round.py --round 6847 --n3-rehearsal 149 # N3リハーサル数字を指定
    python check_prediction_for_round.py --range 6840 6849              # 複数回号を一度に確認
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd

# プロジェクトルートのパスを設定
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.append(str(PROJECT_ROOT / 'core'))

from scripts.production.predict_cli import (
    load_data,
    predict_axis_digits,
    predict_combinations,
    load_model_loader
)


def get_winning_numbers(df: pd.DataFrame, round_number: int) -> Tuple[Optional[str], Optional[str]]:
    """指定回号の当選番号を取得"""
    row = df[df['round_number'] == round_number]
    if row.empty:
        return None, None
    
    n3_winning = str(row.iloc[0]['n3_winning']).replace('.0', '').zfill(3)
    n4_winning = str(row.iloc[0]['n4_winning']).replace('.0', '').zfill(4)
    
    return n3_winning, n4_winning


def check_prediction(
    df: pd.DataFrame,
    keisen_master: dict,
    model_loader,
    round_number: int,
    n3_rehearsal: Optional[str] = None,
    n4_rehearsal: Optional[str] = None
):
    """指定回号での予測結果を確認"""
    print("\n" + "="*80)
    print(f"回号 {round_number} の予測結果確認")
    print("="*80)
    
    # 実際の当選番号を取得
    n3_winning, n4_winning = get_winning_numbers(df, round_number)
    if n3_winning is None or n4_winning is None:
        print(f"エラー: 回号 {round_number} のデータが見つかりません")
        return
    
    print(f"\n実際の当選番号:")
    print(f"  N3: {n3_winning}")
    print(f"  N4: {n4_winning}")
    
    # リハーサル数字を取得（指定されていない場合はデータから取得）
    if n3_rehearsal is None:
        n3_rehearsal = str(df[df['round_number'] == round_number].iloc[0]['n3_rehearsal']).replace('.0', '').zfill(3) if 'n3_rehearsal' in df.columns else None
    if n4_rehearsal is None:
        n4_rehearsal = str(df[df['round_number'] == round_number].iloc[0]['n4_rehearsal']).replace('.0', '').zfill(4) if 'n4_rehearsal' in df.columns else None
    
    if n3_rehearsal:
        print(f"\nN3リハーサル: {n3_rehearsal}")
    if n4_rehearsal:
        print(f"N4リハーサル: {n4_rehearsal}")
    
    # N3の予測
    if n3_rehearsal:
        print("\n" + "-"*80)
        print("N3予測結果")
        print("-"*80)
        
        axis_results = predict_axis_digits(
            df, keisen_master, model_loader, round_number, 'n3', n3_rehearsal
        )
        
        # 最良パターンを特定
        best_pattern_n3 = None
        best_score_n3 = -1
        
        for pattern, digit_scores in axis_results.items():
            if digit_scores:
                max_score = max(s for _, s in digit_scores)
                if max_score > best_score_n3:
                    best_score_n3 = max_score
                    best_pattern_n3 = pattern
        
        if best_pattern_n3:
            # 軸数字ランキング
            all_axis_scores = {}
            for pattern, digit_scores in axis_results.items():
                for digit, score in digit_scores:
                    if digit not in all_axis_scores or score > all_axis_scores[digit][1]:
                        all_axis_scores[digit] = (pattern, score)
            
            axis_candidates = [(d, s) for d, (p, s) in sorted(all_axis_scores.items(), key=lambda x: x[1][1], reverse=True)]
            top_axis_digits = [d for d, _ in axis_candidates[:10]]
            
            print(f"\n最良パターン: {best_pattern_n3}")
            print("\n軸数字ランキング（上位10件）:")
            for i, (digit, score) in enumerate(axis_candidates[:10], 1):
                hit = "✅" if str(digit) in n3_winning else ""
                print(f"  {i:2d}. 数字{digit}: スコア{score:.0f} {hit}")
            
            # 実際の当選番号に含まれる数字を確認
            winning_digits = set(n3_winning)
            predicted_top5_digits = {d for d, _ in axis_candidates[:5]}
            hit_count = len(winning_digits & predicted_top5_digits)
            
            print(f"\n予測精度:")
            print(f"  上位5件中に当選数字が含まれる数: {hit_count}/{len(winning_digits)}")
            
            # 組み合わせ予測（ボックス）
            print("\n組み合わせ予測（BOX）:")
            combinations = predict_combinations(
                df, keisen_master, model_loader, round_number, 'n3',
                'box', best_pattern_n3, top_axis_digits, n3_rehearsal, max_combinations=20
            )
            
            print("  上位10件:")
            for i, (combo, score) in enumerate(combinations[:10], 1):
                # ボックスの場合は順序を無視して比較
                combo_sorted = ''.join(sorted(combo))
                winning_sorted = ''.join(sorted(n3_winning))
                hit = "✅" if combo_sorted == winning_sorted else ""
                print(f"  {i:2d}. {combo}: スコア{score:.0f} {hit}")
            
            # 上位10件中に当選番号が含まれるか確認
            top10_combos = [combo for combo, _ in combinations[:10]]
            top10_combos_sorted = [''.join(sorted(c)) for c in top10_combos]
            hit_in_top10 = winning_sorted in top10_combos_sorted
            
            print(f"\n  上位10件中に当選番号が含まれる: {'✅' if hit_in_top10 else '❌'}")
    
    # N4の予測
    if n4_rehearsal:
        print("\n" + "-"*80)
        print("N4予測結果")
        print("-"*80)
        
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
            # 軸数字ランキング
            all_axis_scores = {}
            for pattern, digit_scores in axis_results.items():
                for digit, score in digit_scores:
                    if digit not in all_axis_scores or score > all_axis_scores[digit][1]:
                        all_axis_scores[digit] = (pattern, score)
            
            axis_candidates = [(d, s) for d, (p, s) in sorted(all_axis_scores.items(), key=lambda x: x[1][1], reverse=True)]
            top_axis_digits = [d for d, _ in axis_candidates[:10]]
            
            print(f"\n最良パターン: {best_pattern_n4}")
            print("\n軸数字ランキング（上位10件）:")
            for i, (digit, score) in enumerate(axis_candidates[:10], 1):
                hit = "✅" if str(digit) in n4_winning else ""
                print(f"  {i:2d}. 数字{digit}: スコア{score:.0f} {hit}")
            
            # 実際の当選番号に含まれる数字を確認
            winning_digits = set(n4_winning)
            predicted_top5_digits = {d for d, _ in axis_candidates[:5]}
            hit_count = len(winning_digits & predicted_top5_digits)
            
            print(f"\n予測精度:")
            print(f"  上位5件中に当選数字が含まれる数: {hit_count}/{len(winning_digits)}")
            
            # 組み合わせ予測（ボックス）
            print("\n組み合わせ予測（BOX）:")
            combinations = predict_combinations(
                df, keisen_master, model_loader, round_number, 'n4',
                'box', best_pattern_n4, top_axis_digits, n4_rehearsal, max_combinations=20
            )
            
            print("  上位10件:")
            for i, (combo, score) in enumerate(combinations[:10], 1):
                # ボックスの場合は順序を無視して比較
                combo_sorted = ''.join(sorted(combo))
                winning_sorted = ''.join(sorted(n4_winning))
                hit = "✅" if combo_sorted == winning_sorted else ""
                print(f"  {i:2d}. {combo}: スコア{score:.0f} {hit}")
            
            # 上位10件中に当選番号が含まれるか確認
            top10_combos = [combo for combo, _ in combinations[:10]]
            top10_combos_sorted = [''.join(sorted(c)) for c in top10_combos]
            hit_in_top10 = winning_sorted in top10_combos_sorted
            
            print(f"\n  上位10件中に当選番号が含まれる: {'✅' if hit_in_top10 else '❌'}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='過去回号での予測結果確認CLIツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python check_prediction_for_round.py --round 6847
  python check_prediction_for_round.py --round 6847 --n3-rehearsal 149
  python check_prediction_for_round.py --range 6840 6849
        """
    )
    
    parser.add_argument(
        '--round',
        type=int,
        help='回号'
    )
    parser.add_argument(
        '--range',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        help='回号範囲（開始回号 終了回号）'
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
    
    if not args.round and not args.range:
        print("エラー: --round または --range を指定してください")
        sys.exit(1)
    
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
    if args.range:
        start_round, end_round = args.range
        for round_number in range(start_round, end_round + 1):
            check_prediction(
                df, keisen_master, model_loader, round_number,
                args.n3_rehearsal, args.n4_rehearsal
            )
    else:
        check_prediction(
            df, keisen_master, model_loader, args.round,
            args.n3_rehearsal, args.n4_rehearsal
        )


if __name__ == '__main__':
    main()

