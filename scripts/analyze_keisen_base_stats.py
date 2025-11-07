#!/usr/bin/env python3
"""
keisen基礎集計スクリプト
4801-6850回のデータから、前々回・前回パターンごとの当選数字の出現頻度とランキングを集計し、
新keisenマスターデータを生成する。
"""

import pandas as pd
import json
import numpy as np
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# データディレクトリのパス
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR

# N3とN4の桁定義
N3_COLUMNS = ["百の位", "十の位", "一の位"]
N4_COLUMNS = ["千の位", "百の位", "十の位", "一の位"]

def load_past_results() -> pd.DataFrame:
    """past_results.csvを読み込む"""
    file_path = DATA_DIR / "past_results.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"データファイルが見つかりません: {file_path}")
    
    # NULL文字列をNaNとして読み込む
    df = pd.read_csv(file_path, na_values=['NULL', 'null', ''])
    
    # 当選番号を文字列型に変換（数値型で読み込まれる可能性があるため）
    df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
    df['n4_winning'] = df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
    
    # NULL値やNaNを除外
    df['n3_winning'] = df['n3_winning'].replace('nan', pd.NA).replace('NULL', pd.NA)
    df['n4_winning'] = df['n4_winning'].replace('nan', pd.NA).replace('NULL', pd.NA)
    
    # 先頭0を補完（数値型として読み込まれた場合、先頭0が失われるため）
    df['n3_winning'] = df['n3_winning'].apply(
        lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'nan' and str(x) != 'NULL' else x
    )
    df['n4_winning'] = df['n4_winning'].apply(
        lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'nan' and str(x) != 'NULL' else x
    )
    
    print(f"データ読み込み完了: {len(df)}行")
    return df

def filter_data_range(df: pd.DataFrame, start_round: int = 4801, end_round: int = 6850) -> pd.DataFrame:
    """指定範囲のデータをフィルタリング"""
    filtered = df[(df['round_number'] >= start_round) & (df['round_number'] <= end_round)].copy()
    filtered = filtered.sort_values('round_number')
    print(f"フィルタリング完了: {len(filtered)}行 (回号 {start_round}-{end_round})")
    return filtered

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """データクリーニング"""
    df = df.copy()
    
    # NULL値の除去
    original_len = len(df)
    df = df.dropna(subset=['n3_winning', 'n4_winning'])
    if len(df) < original_len:
        print(f"NULL値除去: {original_len - len(df)}行を削除")
    
    # 形式チェック（文字列型であることを確認）
    df = df[df['n3_winning'].astype(str).str.len() == 3]
    df = df[df['n4_winning'].astype(str).str.len() == 4]
    
    print(f"データクリーニング完了: {len(df)}行")
    return df

def extract_previous_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """前回・前々回の当選番号を抽出"""
    df = df.copy()
    df['prev_n3'] = df['n3_winning'].shift(1)
    df['prev2_n3'] = df['n3_winning'].shift(2)
    df['prev_n4'] = df['n4_winning'].shift(1)
    df['prev2_n4'] = df['n4_winning'].shift(2)
    
    # 前回・前々回が存在しない行を除外
    df = df.dropna(subset=['prev_n3', 'prev2_n3', 'prev_n4', 'prev2_n4'])
    
    print(f"前回・前々回データ抽出完了: {len(df)}行")
    return df

def extract_digits(number_str, num_digits: int) -> List[int]:
    """数字文字列から各桁を抽出"""
    # 文字列型に変換
    if pd.isna(number_str):
        raise ValueError(f"数値がNULLです: {number_str}")
    str_value = str(number_str)
    if len(str_value) != num_digits:
        raise ValueError(f"数値の桁数が不正です: {str_value} (期待値: {num_digits})")
    return [int(str_value[i]) for i in range(num_digits)]

def count_pattern_frequency(df: pd.DataFrame, columns: List[str], prev_col: str, prev2_col: str, winning_col: str) -> Dict:
    """パターン出現頻度を集計"""
    pattern_counts = defaultdict(int)
    digit_counts = defaultdict(lambda: defaultdict(int))
    
    for _, row in df.iterrows():
        prev = row[prev_col]
        prev2 = row[prev2_col]
        winning = row[winning_col]
        
        # 各桁を抽出
        prev_digits = extract_digits(prev, len(columns))
        prev2_digits = extract_digits(prev2, len(columns))
        winning_digits = extract_digits(winning, len(columns))
        
        # 各桁ごとにパターンを集計
        for i, column in enumerate(columns):
            prev_digit = str(prev_digits[i])
            prev2_digit = str(prev2_digits[i])
            winning_digit = winning_digits[i]
            
            # パターン出現回数をカウント
            # keisen_master.jsonの構造は[前々回][前回]なので、pattern_keyも(column, 前々回, 前回)の順序にする
            pattern_key = (column, prev2_digit, prev_digit)
            pattern_counts[pattern_key] += 1
            
            # 当選数字の出現回数をカウント
            digit_counts[pattern_key][winning_digit] += 1
    
    return pattern_counts, digit_counts

def calculate_rankings_with_rule(digit_counts: Dict, pattern_counts: Dict) -> Dict:
    """ランキングを作成（既存のkeisen_master.jsonと同じルールを適用）
    
    ルールの適用順序:
    1. 上位3位の最小出現回数 > 4位以降の最大出現回数 の場合 → 上位3位のみ（3桁）
    2. 上位3位の最小出現回数 = 4位以降の最大出現回数 の場合（同率） → ルール2を適用（4桁以上）
    3. 上位3位の最小出現回数 < 4位以降の最大出現回数 の場合 → ルール2を適用（4桁以上）
    
    ルール2: 予測出目の最小出現回数 >= 除外された数字の最大出現回数
    """
    rankings = {}
    
    for pattern_key, digit_count_dict in digit_counts.items():
        # 出現回数の降順でソート、同率の場合は数字の昇順でソート
        sorted_digits = sorted(
            digit_count_dict.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        if len(sorted_digits) == 0:
            rankings[pattern_key] = {
                'ranking': [],
                'counts': {},
                'total_samples': 0
            }
            continue
        
        # 上位3位の情報
        top3_digits = [digit for digit, count in sorted_digits[:3]]
        top3_counts = [count for _, count in sorted_digits[:3]]
        top3_min_count = min(top3_counts) if top3_counts else 0
        
        # 4位以降の情報
        if len(sorted_digits) > 3:
            remaining_counts = [count for _, count in sorted_digits[3:]]
            remaining_max_count = max(remaining_counts) if remaining_counts else 0
        else:
            remaining_max_count = 0
        
        # ルール1をチェック: 上位3位の最小出現回数 > 4位以降の最大出現回数
        if top3_min_count > remaining_max_count:
            # ルール1を満たす場合: 上位3位のみを予測出目とする（3桁）
            predictions = top3_digits
        else:
            # ルール1を満たさない場合（同率または小さい）: 上位3位 + 上位3位の最小出現回数と同じ（同率）の4位以降の数字
            predictions = top3_digits.copy()
            
            # 4位以降の数字で、上位3位の最小出現回数と同じ（同率）の数字を追加
            if len(sorted_digits) > 3:
                for digit, count in sorted_digits[3:]:
                    if count == top3_min_count:
                        predictions.append(digit)
                    elif count < top3_min_count:
                        # 上位3位の最小出現回数より小さい場合は追加しない
                        break
        
        counts_dict = {str(digit): count for digit, count in sorted_digits}
        
        rankings[pattern_key] = {
            'ranking': predictions,
            'counts': counts_dict,
            'total_samples': sum(digit_count_dict.values())
        }
    
    return rankings

def calculate_rankings(digit_counts: Dict) -> Dict:
    """ランキングを作成（旧バージョン - 上位3位まで）"""
    rankings = {}
    
    for pattern_key, digit_count_dict in digit_counts.items():
        # 出現回数の降順でソート、同率の場合は数字の昇順でソート
        sorted_digits = sorted(
            digit_count_dict.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        # 上位3位までの数字リストを抽出
        top3 = [digit for digit, count in sorted_digits[:3]]
        rankings[pattern_key] = {
            'ranking': top3,
            'counts': {str(digit): count for digit, count in sorted_digits}
        }
    
    return rankings

def calculate_reliability_stats(pattern_counts: Dict, digit_counts: Dict) -> Dict:
    """統計的信頼性指標を計算"""
    reliability_stats = {}
    
    for pattern_key in pattern_counts.keys():
        n = pattern_counts[pattern_key]
        digit_count_dict = digit_counts.get(pattern_key, {})
        
        if n == 0:
            continue
        
        # 各数字の出現回数リスト
        counts = [digit_count_dict.get(d, 0) for d in range(10)]
        
        # 標準偏差を計算
        if n > 1:
            std_dev = np.std(counts, ddof=1)
        else:
            std_dev = 0.0
        
        # 各数字の出現率と95%信頼区間
        digit_stats = {}
        for digit in range(10):
            count = digit_count_dict.get(digit, 0)
            rate = (count / n) * 100 if n > 0 else 0.0
            
            # 95%信頼区間（正規分布を仮定）
            if n > 0:
                se = np.sqrt((rate / 100) * (1 - rate / 100) / n)
                ci_lower = max(0, rate - 1.96 * se * 100)
                ci_upper = min(100, rate + 1.96 * se * 100)
            else:
                ci_lower = ci_upper = 0.0
            
            digit_stats[str(digit)] = {
                'count': count,
                'rate': rate,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper
            }
        
        # 信頼性スコア（サンプル数に基づく）
        if n >= 10:
            reliability_score = 1.0
        elif n >= 5:
            reliability_score = 0.7
        else:
            reliability_score = 0.3
        
        reliability_stats[pattern_key] = {
            'sample_size': n,
            'std_dev': float(std_dev),
            'reliability_score': reliability_score,
            'digit_stats': digit_stats
        }
    
    return reliability_stats

def generate_keisen_master(rankings: Dict, pattern_counts: Dict, n3_rankings: Dict, n4_rankings: Dict) -> Dict:
    """新keisenマスターデータを生成"""
    master = {
        'n3': {},
        'n4': {}
    }
    
    # N3のマスターデータを生成（keisen_master.jsonの構造は[前々回][前回]）
    for column in N3_COLUMNS:
        master['n3'][column] = {}
        for prev2_digit in range(10):
            prev2_str = str(prev2_digit)  # 前々回
            master['n3'][column][prev2_str] = {}
            for prev_digit in range(10):
                prev_str = str(prev_digit)  # 前回
                pattern_key = (column, prev2_str, prev_str)  # (column, 前々回, 前回)
                
                if pattern_key in n3_rankings:
                    ranking = n3_rankings[pattern_key]['ranking']
                    sample_size = pattern_counts.get(pattern_key, 0)
                    
                    # サンプル数が不足している場合は空配列または警告
                    if sample_size < 5:
                        master['n3'][column][prev2_str][prev_str] = []
                    else:
                        master['n3'][column][prev2_str][prev_str] = ranking
                else:
                    master['n3'][column][prev2_str][prev_str] = []
    
    # N4のマスターデータを生成（keisen_master.jsonの構造は[前々回][前回]）
    for column in N4_COLUMNS:
        master['n4'][column] = {}
        for prev2_digit in range(10):
            prev2_str = str(prev2_digit)  # 前々回
            master['n4'][column][prev2_str] = {}
            for prev_digit in range(10):
                prev_str = str(prev_digit)  # 前回
                pattern_key = (column, prev2_str, prev_str)  # (column, 前々回, 前回)
                
                if pattern_key in n4_rankings:
                    ranking = n4_rankings[pattern_key]['ranking']
                    sample_size = pattern_counts.get(pattern_key, 0)
                    
                    # サンプル数が不足している場合は空配列または警告
                    if sample_size < 5:
                        master['n4'][column][prev2_str][prev_str] = []
                    else:
                        master['n4'][column][prev2_str][prev_str] = ranking
                else:
                    master['n4'][column][prev2_str][prev_str] = []
    
    return master

def validate_keisen_master(master: Dict) -> Tuple[bool, List[str]]:
    """keisenマスターデータの検証"""
    errors = []
    
    # N3の検証
    expected_n3_patterns = len(N3_COLUMNS) * 10 * 10
    actual_n3_patterns = 0
    for column in N3_COLUMNS:
        if column not in master['n3']:
            errors.append(f"N3: 桁 '{column}' が存在しません")
            continue
        for prev_str in master['n3'][column]:
            if prev_str not in [str(i) for i in range(10)]:
                errors.append(f"N3: 前回の数字 '{prev_str}' が無効です")
            for prev2_str in master['n3'][column][prev_str]:
                if prev2_str not in [str(i) for i in range(10)]:
                    errors.append(f"N3: 前々回の数字 '{prev2_str}' が無効です")
                actual_n3_patterns += 1
                predictions = master['n3'][column][prev_str][prev2_str]
                if not isinstance(predictions, list):
                    errors.append(f"N3: 予測出目が配列ではありません: {column}/{prev_str}/{prev2_str}")
                else:
                    for pred in predictions:
                        if not isinstance(pred, int) or pred < 0 or pred > 9:
                            errors.append(f"N3: 予測出目が無効です: {pred} (0-9の範囲外)")
    
    if actual_n3_patterns != expected_n3_patterns:
        errors.append(f"N3: パターン数が不正です。期待値: {expected_n3_patterns}, 実際: {actual_n3_patterns}")
    
    # N4の検証
    expected_n4_patterns = len(N4_COLUMNS) * 10 * 10
    actual_n4_patterns = 0
    for column in N4_COLUMNS:
        if column not in master['n4']:
            errors.append(f"N4: 桁 '{column}' が存在しません")
            continue
        for prev_str in master['n4'][column]:
            if prev_str not in [str(i) for i in range(10)]:
                errors.append(f"N4: 前回の数字 '{prev_str}' が無効です")
            for prev2_str in master['n4'][column][prev_str]:
                if prev2_str not in [str(i) for i in range(10)]:
                    errors.append(f"N4: 前々回の数字 '{prev2_str}' が無効です")
                actual_n4_patterns += 1
                predictions = master['n4'][column][prev_str][prev2_str]
                if not isinstance(predictions, list):
                    errors.append(f"N4: 予測出目が配列ではありません: {column}/{prev_str}/{prev2_str}")
                else:
                    for pred in predictions:
                        if not isinstance(pred, int) or pred < 0 or pred > 9:
                            errors.append(f"N4: 予測出目が無効です: {pred} (0-9の範囲外)")
    
    if actual_n4_patterns != expected_n4_patterns:
        errors.append(f"N4: パターン数が不正です。期待値: {expected_n4_patterns}, 実際: {actual_n4_patterns}")
    
    return len(errors) == 0, errors

def save_json(data: Dict, filepath: Path):
    """JSONファイルを保存"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSONファイル保存完了: {filepath}")

def save_csv_from_dict(data: Dict, filepath: Path):
    """辞書データをCSV形式で保存"""
    rows = []
    for key, value in data.items():
        if isinstance(key, tuple):
            column, prev, prev2 = key
            row = {
                'column': column,
                'prev': prev,
                'prev2': prev2,
                **value
            }
        else:
            row = {'key': str(key), **value}
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"CSVファイル保存完了: {filepath}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("keisen基礎集計スクリプト開始")
    print("=" * 60)
    
    try:
        # Phase 1: データ準備
        print("\n[Phase 1] データ準備")
        df = load_past_results()
        df = filter_data_range(df, start_round=4801, end_round=6850)
        df = clean_data(df)
        df = extract_previous_numbers(df)
        
        # Phase 2 & 3: パターン出現頻度と当選数字の分布を集計
        print("\n[Phase 2-3] パターン出現頻度と当選数字の分布を集計")
        n3_pattern_counts, n3_digit_counts = count_pattern_frequency(
            df, N3_COLUMNS, 'prev_n3', 'prev2_n3', 'n3_winning'
        )
        n4_pattern_counts, n4_digit_counts = count_pattern_frequency(
            df, N4_COLUMNS, 'prev_n4', 'prev2_n4', 'n4_winning'
        )
        
        # ランキングを作成（既存のkeisen_master.jsonと同じルールを適用）
        print("\n[Phase 3] ランキングを作成（既存ルール適用）")
        n3_rankings = calculate_rankings_with_rule(n3_digit_counts, n3_pattern_counts)
        n4_rankings = calculate_rankings_with_rule(n4_digit_counts, n4_pattern_counts)
        
        # Phase 4: 統計的信頼性指標を計算
        print("\n[Phase 4] 統計的信頼性指標を計算")
        n3_reliability = calculate_reliability_stats(n3_pattern_counts, n3_digit_counts)
        n4_reliability = calculate_reliability_stats(n4_pattern_counts, n4_digit_counts)
        
        # 結果を出力
        print("\n[出力] 集計結果を出力")
        
        # パターン出現頻度
        n3_frequency_data = {
            f"{col}/{prev}/{prev2}": {'count': count}
            for (col, prev, prev2), count in n3_pattern_counts.items()
        }
        n4_frequency_data = {
            f"{col}/{prev}/{prev2}": {'count': count}
            for (col, prev, prev2), count in n4_pattern_counts.items()
        }
        
        save_json({
            'n3': n3_frequency_data,
            'n4': n4_frequency_data
        }, OUTPUT_DIR / "keisen_pattern_frequency.json")
        
        # ランキング結果
        n3_ranking_data = {
            f"{col}/{prev}/{prev2}": ranking_data
            for (col, prev, prev2), ranking_data in n3_rankings.items()
        }
        n4_ranking_data = {
            f"{col}/{prev}/{prev2}": ranking_data
            for (col, prev, prev2), ranking_data in n4_rankings.items()
        }
        
        save_json({
            'n3': n3_ranking_data,
            'n4': n4_ranking_data
        }, OUTPUT_DIR / "keisen_digit_ranking.json")
        
        # 信頼性統計
        n3_reliability_data = {
            f"{col}/{prev}/{prev2}": stats
            for (col, prev, prev2), stats in n3_reliability.items()
        }
        n4_reliability_data = {
            f"{col}/{prev}/{prev2}": stats
            for (col, prev, prev2), stats in n4_reliability.items()
        }
        
        save_json({
            'n3': n3_reliability_data,
            'n4': n4_reliability_data
        }, OUTPUT_DIR / "keisen_reliability_stats.json")
        
        # Phase 5: 新keisenマスターデータを生成
        print("\n[Phase 5] 新keisenマスターデータを生成")
        all_pattern_counts = {**n3_pattern_counts, **n4_pattern_counts}
        master = generate_keisen_master(
            {}, all_pattern_counts, n3_rankings, n4_rankings
        )
        
        # 検証
        print("\n[検証] keisenマスターデータの検証")
        is_valid, errors = validate_keisen_master(master)
        if not is_valid:
            print("警告: 検証エラーが見つかりました:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("検証成功: 全てのパターンが正しく定義されています")
        
        # 保存
        save_json(master, OUTPUT_DIR / "keisen_master_new.json")
        
        # 統計サマリー
        print("\n[統計サマリー]")
        print(f"N3パターン総数: {len(n3_pattern_counts)}")
        print(f"N4パターン総数: {len(n4_pattern_counts)}")
        print(f"N3平均出現回数: {np.mean(list(n3_pattern_counts.values())):.2f}")
        print(f"N4平均出現回数: {np.mean(list(n4_pattern_counts.values())):.2f}")
        
        # サンプル数が不足しているパターン
        n3_low_sample = [k for k, v in n3_pattern_counts.items() if v < 5]
        n4_low_sample = [k for k, v in n4_pattern_counts.items() if v < 5]
        print(f"N3サンプル数5未満: {len(n3_low_sample)}パターン")
        print(f"N4サンプル数5未満: {len(n4_low_sample)}パターン")
        
        print("\n" + "=" * 60)
        print("処理完了")
        print("=" * 60)
        
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

