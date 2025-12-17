"""
極CUBE生成スクリプト

既存のCUBE生成ロジック（notebooks/chart_generator.py）をベースに、
5行目の余りマスを0で埋める処理を追加した極CUBEを生成する。
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Literal
from datetime import datetime

import pandas as pd

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / 'core'))

from chart_generator import (
    load_keisen_master,
    generate_chart,
    ChartGenerationError,
    extract_predicted_digits,
    apply_pattern_expansion,
    build_main_rows,
    apply_vertical_inverse,
    apply_horizontal_inverse
)

# Pattern と Target の型定義は不要（極CUBEはN3のみ、1パターンのみ）
# Pattern = Literal['A1', 'A2', 'B1', 'B2']
# Target = Literal['n3', 'n4']

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_extreme_cube(
    df: pd.DataFrame,
    keisen_master: dict,
    round_number: int
) -> Tuple[List[List[Optional[int]]], int, int]:
    """極CUBEを生成する（専用ロジック）
    
    極CUBEの仕様:
    - N3のみ（N4は対象外）
    - B1パターンと同じ（欠番補足なし、中心0配置なし）
    - 最大5行まで（メイン行1,3,5行目）
    - 2行目と4行目に裏数字を配置（6行目は不要）
    - 5行目の余りマスを0で埋める（極CUBE固有）
    
    Args:
        df: 過去当選番号データ（DataFrame）
        keisen_master: 罫線マスターデータ
        round_number: 回号
    
    Returns:
        (grid, rows, cols) のタプル
    
    Raises:
        ChartGenerationError: CUBE生成に失敗した場合
    """
    try:
        # ステップ1: 予測出目の抽出
        source_list = extract_predicted_digits(df, keisen_master, round_number, 'n3')
        
        # ステップ2: パターン別の元数字リスト作成（B1: 欠番補足なし）
        nums = apply_pattern_expansion(source_list, 'B1')
        
        # ステップ3: メイン行の組み立て
        main_rows, _ = build_main_rows(nums)
        
        # 極CUBEは最大3本のメイン行まで（1,3,5行目）
        # N3の当選番号から取得した数字は5行目で使い切る
        if len(main_rows) > 3:
            # 4本目以降の数字を3本目に統合
            # 最後のメイン行に残りの数字を追加
            remaining_digits = []
            for i in range(3, len(main_rows)):
                remaining_digits.extend(main_rows[i])
            if remaining_digits:
                main_rows[2].extend(remaining_digits)
            main_rows = main_rows[:3]
        
        # ステップ4: グリッド初期配置
        # 極CUBEは最大5行（メイン行3本の場合: 1,2,3,4,5行目）
        rows = min(len(main_rows) * 2, 5)  # 最大5行まで
        cols = 8
        grid = [[None] * (cols + 1) for _ in range(rows + 1)]  # 1-indexed
        
        # メイン行を奇数行の奇数列に配置
        for i, main_row in enumerate(main_rows):
            row = i * 2 + 1  # 1, 3, 5行目
            for j, val in enumerate(main_row):
                col = j * 2 + 1  # 1, 3, 5, 7列目
                if col <= cols:
                    grid[row][col] = val
        
        # ステップ5: グリッド初期配置時の余りマスを0で埋める（極CUBE固有）
        # メイン行配置後、裏数字適用前に実行
        # 対象: 奇数行（メイン行）の奇数列（1, 3, 5, 7列目）で空いているマス
        for row in range(1, rows + 1, 2):  # 奇数行（1, 3, 5行目）
            for col in range(1, cols + 1, 2):  # 奇数列（1, 3, 5, 7列目）
                if grid[row][col] is None:
                    grid[row][col] = 0
        
        # ステップ6: 裏数字ルール（通常CUBEと同じロジックを再利用）
        # 極CUBEの仕様: 2行目と4行目に裏数字を配置（6行目は不要）
        # 通常CUBEの裏数字ルールを適用すると、極CUBEの5行目までの範囲では
        # メイン行（奇数行）の偶数列と偶数行（2,4行目）に裏数字が配置され、
        # 結果は極CUBE専用ルールと同じになる
        apply_vertical_inverse(grid, rows, cols)
        apply_horizontal_inverse(grid, rows, cols)
        
        # ステップ7: 5行目の余りマスを0で埋める（極CUBE固有）
        if rows >= 5:
            for col in range(1, cols + 1):
                if grid[5][col] is None:
                    grid[5][col] = 0
        
        return grid, rows, cols
    
    except Exception as e:
        if isinstance(e, ChartGenerationError):
            raise
        raise ChartGenerationError(f"極CUBE生成エラー（回号{round_number}）: {e}")


def load_past_results(data_dir: Path) -> pd.DataFrame:
    """過去当選番号データを読み込む
    
    Args:
        data_dir: データディレクトリ
    
    Returns:
        過去当選番号データ（DataFrame）
    """
    csv_path = data_dir / 'past_results.csv'
    
    if not csv_path.exists():
        raise FileNotFoundError(f"過去当選番号データが見つかりません: {csv_path}")
    
    # dtype指定で当選番号を文字列として読み込む（先頭0の欠落を防ぐ）
    df = pd.read_csv(csv_path, encoding='utf-8', dtype={
        'n3_winning': str,
        'n4_winning': str,
        'n3_rehearsal': str,
        'n4_rehearsal': str
    })

    # データクリーニング
    # round_numberが数値型であることを確認
    if 'round_number' not in df.columns:
        raise ValueError("past_results.csvに'round_number'列がありません")

    df['round_number'] = pd.to_numeric(df['round_number'], errors='coerce')
    df = df.dropna(subset=['round_number'])
    df['round_number'] = df['round_number'].astype(int)

    return df


def validate_round_number(
    df: pd.DataFrame,
    round_number: int
) -> bool:
    """回号の妥当性を検証する
    
    Args:
        df: 過去当選番号データ
        round_number: 回号
    
    Returns:
        妥当な場合True、そうでない場合False
    """
    # 回号1, 2は前回・前々回のデータが存在しないため生成不可
    if round_number < 3:
        return False
    
    # 回号がデータに存在するか確認
    if round_number not in df['round_number'].values:
        return False
    
    # 前回（round_number-1）と前々回（round_number-2）のデータが存在するか確認
    previous_round = round_number - 1
    previous_previous_round = round_number - 2
    
    if previous_round not in df['round_number'].values:
        return False
    
    if previous_previous_round not in df['round_number'].values:
        return False
    
    return True


def save_extreme_cube(
    grid: List[List[Optional[int]]],
    round_number: int,
    output_dir: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """極CUBEをJSON形式で保存する（N3のみ、1パターンのみ）
    
    Args:
        grid: グリッド（1-indexed）
        round_number: 回号
        output_dir: 出力ディレクトリ
        metadata: 追加メタデータ（オプション）
    
    Returns:
        保存されたファイルのパス
    """
    # 出力ディレクトリの作成（N3のみ、パターンサブディレクトリなし）
    target_dir = output_dir / 'n3'
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル名: round_{回号:04d}.json
    filename = f"round_{round_number:04d}.json"
    file_path = target_dir / filename
    
    # グリッドを0-indexedの配列に変換（JSON用）
    # gridは1-indexedなので、grid[1]からgrid[rows]までを使用
    rows = len(grid) - 1  # grid[0]は未使用
    cols = len(grid[1]) - 1  # grid[1][0]は未使用
    
    grid_array = []
    for row in range(1, rows + 1):
        row_array = []
        for col in range(1, cols + 1):
            value = grid[row][col]
            # Noneの場合はnullとして保存
            row_array.append(value if value is not None else None)
        grid_array.append(row_array)
    
    # JSONデータを作成
    json_data = {
        "round_number": round_number,
        "target": "n3",  # 極CUBEはN3のみ
        "pattern": "extreme",  # 極CUBEは1パターンのみ
        "grid": grid_array,
        "grid_size": {
            "rows": rows,
            "cols": cols
        },
        "metadata": {
            "generated_at": datetime.now().isoformat() + "Z",
            "keisen_version": "1.0",
            **(metadata or {})
        }
    }
    
    # JSONファイルに保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    return file_path


def generate_batch_extreme_cubes(
    df: pd.DataFrame,
    keisen_master: dict,
    start_round: int = 3,
    end_round: Optional[int] = None,
    rounds: Optional[List[int]] = None,
    output_dir: Path = None,
    save_interval: int = 100
) -> Dict[str, Any]:
    """複数の回号の極CUBEを一括生成する（N3のみ、1パターンのみ）
    
    Args:
        df: 過去当選番号データ
        keisen_master: 罫線マスターデータ
        start_round: 開始回号（デフォルト: 3）
        end_round: 終了回号（デフォルト: None、最新回まで）
        rounds: 指定回号リスト（指定された場合、start_round/end_roundより優先）
        output_dir: 出力ディレクトリ（デフォルト: data/extreme_cubes/）
        save_interval: 進捗表示間隔（デフォルト: 100回ごと）
    
    Returns:
        生成結果の統計情報
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / 'data' / 'extreme_cubes'
    
    # 回号リストを決定
    if rounds is not None:
        round_list = sorted(set(rounds))
    else:
        if end_round is None:
            end_round = int(df['round_number'].max())
        round_list = list(range(start_round, end_round + 1))
    
    # 統計情報（極CUBEはN3のみ、1パターンのみ）
    stats = {
        "total_rounds": len(round_list),
        "success_count": 0,
        "failure_count": 0,
        "failed_rounds": [],
        "start_time": datetime.now().isoformat(),
        "end_time": None
    }
    
    processed_count = 0
    
    logger.info(f"極CUBE生成を開始します（N3のみ、1パターンのみ）")
    logger.info(f"回号範囲: {round_list[0]} - {round_list[-1]} ({len(round_list)}回)")
    
    # 各回号でCUBEを生成（N3のみ、1パターンのみ）
    for round_number in round_list:
        # 回号の妥当性を検証
        if not validate_round_number(df, round_number):
            logger.warning(f"回号{round_number}はスキップします（前回・前々回のデータが不足）")
            stats["failure_count"] += 1
            if round_number not in stats["failed_rounds"]:
                stats["failed_rounds"].append(round_number)
            continue
        
        try:
            # 極CUBEを生成（N3のみ、1パターンのみ）
            grid, rows, cols = generate_extreme_cube(
                df, keisen_master, round_number
            )
            
            # JSON形式で保存
            save_extreme_cube(grid, round_number, output_dir)
            
            stats["success_count"] += 1
            processed_count += 1
            
            # 進捗表示
            if processed_count % save_interval == 0:
                progress = (processed_count / len(round_list)) * 100
                logger.info(
                    f"進捗: {processed_count}/{len(round_list)} "
                    f"({progress:.1f}%) - "
                    f"成功: {stats['success_count']}, "
                    f"失敗: {stats['failure_count']}"
                )
        
        except ChartGenerationError as e:
            logger.error(f"回号{round_number}の極CUBE生成に失敗: {e}")
            stats["failure_count"] += 1
            if round_number not in stats["failed_rounds"]:
                stats["failed_rounds"].append(round_number)
            processed_count += 1
        
        except Exception as e:
            logger.error(f"回号{round_number}の極CUBE生成で予期しないエラー: {e}", exc_info=True)
            stats["failure_count"] += 1
            if round_number not in stats["failed_rounds"]:
                stats["failed_rounds"].append(round_number)
            processed_count += 1
    
    stats["end_time"] = datetime.now().isoformat()
    
    logger.info("極CUBE生成が完了しました")
    logger.info(f"成功: {stats['success_count']}, 失敗: {stats['failure_count']}")
    if stats["failed_rounds"]:
        logger.warning(f"失敗した回号: {sorted(stats['failed_rounds'])}")
    
    return stats


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='極CUBEを生成するスクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 回号指定（オプション）
    parser.add_argument(
        '--rounds',
        type=str,
        help='指定回号（カンマ区切り、例: 6783,6784,6785）'
    )
    
    # 回号範囲指定（--rounds未指定時）
    parser.add_argument(
        '--start-round',
        type=int,
        default=3,
        help='開始回号（デフォルト: 3）'
    )
    
    parser.add_argument(
        '--end-round',
        type=int,
        help='終了回号（未指定の場合は最新回まで）'
    )
    
    # パターン指定（極CUBEは不要、削除予定）
    # parser.add_argument(
    #     '--patterns',
    #     type=str,
    #     default='A1,A2,B1,B2',
    #     help='パターン（カンマ区切り、デフォルト: A1,A2,B1,B2）'
    # )
    
    # 対象指定（極CUBEはN3のみ、削除予定）
    # parser.add_argument(
    #     '--targets',
    #     type=str,
    #     default='n3,n4',
    #     help='対象（カンマ区切り、デフォルト: n3,n4）'
    # )
    
    # 出力ディレクトリ
    parser.add_argument(
        '--output-dir',
        type=str,
        help='出力ディレクトリ（デフォルト: data/extreme_cubes）'
    )
    
    # データディレクトリ
    parser.add_argument(
        '--data-dir',
        type=str,
        default=str(PROJECT_ROOT / 'data'),
        help='データディレクトリ（デフォルト: data）'
    )
    
    args = parser.parse_args()
    
    # パターンと対象をパース（極CUBEは不要、N3のみ、1パターンのみ）
    
    # 回号リストをパース
    rounds: Optional[List[int]] = None
    if args.rounds:
        rounds = [int(r.strip()) for r in args.rounds.split(',')]
    
    # 出力ディレクトリ
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = PROJECT_ROOT / 'data' / 'extreme_cubes'
    
    data_dir = Path(args.data_dir)
    
    try:
        # データ読み込み
        logger.info("データを読み込んでいます...")
        df = load_past_results(data_dir)
        keisen_master = load_keisen_master(data_dir)
        logger.info(f"データ読み込み完了（{len(df)}回分）")
        
        # 極CUBE生成（N3のみ、1パターンのみ）
        stats = generate_batch_extreme_cubes(
            df=df,
            keisen_master=keisen_master,
            start_round=args.start_round,
            end_round=args.end_round,
            rounds=rounds,
            output_dir=output_dir
        )
        
        # 統計情報を表示
        print("\n=== 生成結果 ===")
        print(f"総回数: {stats['total_rounds']}")
        print(f"成功: {stats['success_count']}")
        print(f"失敗: {stats['failure_count']}")
        if stats["failed_rounds"]:
            print(f"失敗した回号: {sorted(stats['failed_rounds'])}")
        print(f"開始時刻: {stats['start_time']}")
        print(f"終了時刻: {stats['end_time']}")
        
        # 統計情報をJSONファイルに保存
        stats_file = output_dir / 'generation_stats.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logger.info(f"統計情報を保存しました: {stats_file}")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

