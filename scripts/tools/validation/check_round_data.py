#!/usr/bin/env python3
"""
汎用データ確認ツール

特定の回号のデータを確認します。check_6847.pyの汎用版です。

使用方法:
    python check_round_data.py --round 6847  # 6847回のデータを確認
    python check_round_data.py --round 6847 --detailed  # 詳細なデバッグ情報を表示
"""
import argparse
import pandas as pd
import re
import sys
from pathlib import Path

# プロジェクトルートのパスを設定
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()

DATA_DIR = PROJECT_ROOT / 'data'


def check_round_data(round_number: int, detailed: bool = False):
    """指定回号のデータを確認する"""
    csv_path = DATA_DIR / 'past_results.csv'
    
    if not csv_path.exists():
        print(f"エラー: データファイルが見つかりません: {csv_path}")
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    row = df[df['round_number'] == round_number]
    
    if row.empty:
        print(f"エラー: 回号 {round_number} のデータが見つかりません")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"回号 {round_number} のデータ確認")
    print(f"{'='*80}\n")
    
    print('生データ:')
    print(row[['round_number', 'draw_date', 'n3_winning', 'n4_winning']])
    
    if detailed:
        # 文字列型に変換
        n3_val = str(row.iloc[0]['n3_winning']).replace('.0', '')
        n4_val = str(row.iloc[0]['n4_winning']).replace('.0', '')
        
        print(f'\nn3_winning変換後: {repr(n3_val)}')
        print(f'n4_winning変換後: {repr(n4_val)}')
        
        # 正規表現チェック
        n3_match = re.match(r'^\d{3}$', n3_val)
        n4_match = re.match(r'^\d{4}$', n4_val)
        
        print(f'\nn3_winning正規表現マッチ: {n3_match is not None}')
        print(f'n4_winning正規表現マッチ: {n4_match is not None}')
        
        if n4_match is None:
            print(f'\n問題: n4_winningが4桁の正規表現にマッチしません')
            print(f'  値: {repr(n4_val)}')
            print(f'  長さ: {len(n4_val)}')
            print(f'  文字コード: {[ord(c) for c in n4_val]}')
        
        # リハーサル数字の確認
        if 'n3_rehearsal' in df.columns and pd.notna(row.iloc[0]['n3_rehearsal']):
            print(f'\nN3リハーサル: {row.iloc[0]["n3_rehearsal"]}')
        if 'n4_rehearsal' in df.columns and pd.notna(row.iloc[0]['n4_rehearsal']):
            print(f'N4リハーサル: {row.iloc[0]["n4_rehearsal"]}')
    
    # 学習データに含まれているか確認（存在する場合）
    train_data_1000 = DATA_DIR / 'train_data_1000.csv'
    if train_data_1000.exists():
        df_train = pd.read_csv(train_data_1000)
        in_train_data = round_number in df_train['round_number'].values
        print(f'\n学習データ（train_data_1000.csv）に含まれる: {in_train_data}')


def main():
    parser = argparse.ArgumentParser(
        description='特定回号のデータを確認するツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python check_round_data.py --round 6847
  python check_round_data.py --round 6847 --detailed
        """
    )
    
    parser.add_argument(
        '--round',
        type=int,
        required=True,
        help='確認する回号'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='詳細なデバッグ情報を表示'
    )
    
    args = parser.parse_args()
    check_round_data(args.round, args.detailed)


if __name__ == '__main__':
    main()

