"""
CUBE HTML出力スクリプト

既存CUBEと極CUBEの両方をHTML形式で出力し、
Excelに貼り付け可能な形式で提供する。
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Literal
from datetime import datetime

import pandas as pd

# プロジェクトルートをパスに追加
# scripts/tools/visualization/ から見て、プロジェクトルートは parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / 'core'))

from chart_generator import (
    load_keisen_master,
    generate_chart,
    ChartGenerationError
)

# 極CUBE生成スクリプトからインポート
sys.path.append(str(PROJECT_ROOT / 'scripts' / 'production'))
from generate_extreme_cube import (
    load_past_results,
    generate_extreme_cube
)

Pattern = Literal['A1', 'A2', 'B1', 'B2']
Target = Literal['n3', 'n4']
CubeType = Literal['normal', 'extreme']

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_cube_data(
    df: pd.DataFrame,
    keisen_master: dict,
    round_number: int,
    pattern: Optional[str],
    target: str,
    cube_type: CubeType
) -> Tuple[List[List[Optional[int]]], int, int]:
    """CUBEデータを読み込む（既存CUBEまたは極CUBE）
    
    Args:
        df: 過去当選番号データ
        keisen_master: 罫線マスターデータ
        round_number: 回号
        pattern: パターン（既存CUBEの場合のみ必要、極CUBEの場合はNone）
        target: 対象（既存CUBEの場合のみ必要、極CUBEの場合は無視）
        cube_type: CUBEタイプ（'normal' または 'extreme'）
    
    Returns:
        (grid, rows, cols) のタプル
    
    Raises:
        ChartGenerationError: CUBE生成に失敗した場合
    """
    if cube_type == 'extreme':
        # 極CUBEはN3のみ、1パターンのみ（pattern引数不要）
        return generate_extreme_cube(df, keisen_master, round_number)
    else:
        # 既存CUBEはpatternとtargetが必要
        if pattern is None:
            raise ValueError("既存CUBEの場合はpattern引数が必要です")
        return generate_chart(df, keisen_master, round_number, pattern, target)


def generate_html_table(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int
) -> str:
    """CUBEグリッドをHTMLテーブル形式に変換する
    
    Args:
        grid: グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed、常に8）
    
    Returns:
        HTMLテーブル文字列
    """
    html = ['<table id="cubeTable" border="1" cellpadding="4" cellspacing="0" style="border-collapse: collapse;">']
    
    # ヘッダー行（列番号）
    html.append('    <thead>')
    html.append('        <tr>')
    html.append('            <th></th>')  # 左上の空セル
    for col in range(1, cols + 1):
        html.append(f'            <th>{col}</th>')
    html.append('        </tr>')
    html.append('    </thead>')
    
    # データ行
    html.append('    <tbody>')
    for row in range(1, rows + 1):
        html.append('        <tr>')
        html.append(f'            <th>{row}</th>')  # 行番号
        for col in range(1, cols + 1):
            value = grid[row][col]
            if value is None:
                html.append('            <td></td>')
            else:
                html.append(f'            <td>{value}</td>')
        html.append('        </tr>')
    html.append('    </tbody>')
    
    html.append('</table>')
    
    return '\n'.join(html)


def generate_html_page(
    grid: List[List[Optional[int]]],
    rows: int,
    cols: int,
    round_number: int,
    pattern: str,
    target: str,
    cube_type: CubeType
) -> str:
    """完全なHTMLページを生成する（コピーボタン付き）
    
    Args:
        grid: グリッド（1-indexed）
        rows: 行数（1-indexed）
        cols: 列数（1-indexed）
        round_number: 回号
        pattern: パターン
        target: 対象
        cube_type: CUBEタイプ
    
    Returns:
        HTMLページ文字列
    """
    table_html = generate_html_table(grid, rows, cols)
    
    cube_type_label = '極CUBE' if cube_type == 'extreme' else 'CUBE'
    target_label = 'N3' if target == 'n3' else 'N4'
    
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{cube_type_label} - {target_label} {pattern} 回号{round_number}</title>
    <style>
        body {{
            font-family: 'MS Gothic', 'MS PGothic', sans-serif;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .info {{
            color: #666;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .button-container {{
            margin-bottom: 20px;
        }}
        button {{
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 4px;
            transition: background-color 0.3s;
        }}
        button:hover {{
            background-color: #45a049;
        }}
        button:active {{
            background-color: #3d8b40;
        }}
        table {{
            margin: 0 auto;
            border-collapse: collapse;
        }}
        th, td {{
            text-align: center;
            min-width: 40px;
            height: 40px;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        .message {{
            margin-top: 20px;
            padding: 10px;
            background-color: #e7f3ff;
            border-left: 4px solid #2196F3;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{cube_type_label} - {target_label} {pattern}</h1>
        <div class="info">
            <p>回号: {round_number}</p>
            <p>生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div class="button-container">
            <button onclick="copyTableToClipboard()">テーブルをコピー</button>
        </div>
        <div id="message" class="message"></div>
        {table_html}
    </div>
    
    <script>
        function copyTableToClipboard() {{
            const table = document.getElementById('cubeTable');
            const range = document.createRange();
            range.selectNode(table);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            
            try {{
                const successful = document.execCommand('copy');
                if (successful) {{
                    showMessage('テーブルをクリップボードにコピーしました。Excelに貼り付けてください。', 'success');
                }} else {{
                    showMessage('コピーに失敗しました。手動でテーブルを選択してコピーしてください。', 'error');
                }}
            }} catch (err) {{
                showMessage('コピーに失敗しました: ' + err, 'error');
            }}
            
            window.getSelection().removeAllRanges();
        }}
        
        function showMessage(text, type) {{
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = text;
            messageDiv.style.display = 'block';
            messageDiv.style.backgroundColor = type === 'success' ? '#d4edda' : '#f8d7da';
            messageDiv.style.borderLeftColor = type === 'success' ? '#28a745' : '#dc3545';
            
            setTimeout(function() {{
                messageDiv.style.display = 'none';
            }}, 3000);
        }}
    </script>
</body>
</html>"""
    
    return html


def export_cube_to_html(
    df: pd.DataFrame,
    keisen_master: dict,
    round_number: int,
    pattern: Optional[str],
    target: str,
    cube_type: CubeType,
    output_dir: Path
) -> Path:
    """CUBEをHTML形式で出力する
    
    Args:
        df: 過去当選番号データ
        keisen_master: 罫線マスターデータ
        round_number: 回号
        pattern: パターン（既存CUBEの場合のみ必要、極CUBEの場合はNone）
        target: 対象（既存CUBEの場合のみ必要、極CUBEの場合は無視）
        cube_type: CUBEタイプ
        output_dir: 出力ディレクトリ
    
    Returns:
        保存されたHTMLファイルのパス
    
    Raises:
        ChartGenerationError: CUBE生成に失敗した場合
    """
    # CUBEデータを読み込む
    grid, rows, cols = load_cube_data(
        df, keisen_master, round_number, pattern, target, cube_type
    )
    
    # HTMLページを生成
    # 極CUBEの場合はpatternとtargetを固定値で表示
    display_pattern = pattern if pattern else "extreme"
    display_target = target if cube_type == 'normal' else "n3"
    
    html_content = generate_html_page(
        grid, rows, cols, round_number, display_pattern, display_target, cube_type
    )
    
    # 出力ディレクトリを作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル名を生成
    if cube_type == 'extreme':
        filename = f"cube_extreme_n3_extreme_round_{round_number:04d}.html"
    else:
        filename = f"cube_normal_{target}_{pattern}_round_{round_number:04d}.html"
    file_path = output_dir / filename
    
    # HTMLファイルを保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"HTMLファイルを保存しました: {file_path}")
    
    return file_path


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='CUBEをHTML形式で出力するスクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--round',
        type=int,
        required=True,
        help='回号（必須）'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        required=False,
        choices=['A1', 'A2', 'B1', 'B2'],
        help='パターン（既存CUBEの場合のみ必須、極CUBEの場合は不要）'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        required=False,
        choices=['n3', 'n4'],
        help='対象（既存CUBEの場合のみ必須、極CUBEの場合は不要）'
    )
    
    parser.add_argument(
        '--cube-type',
        type=str,
        default='normal',
        choices=['normal', 'extreme'],
        help='CUBEタイプ（normal/extreme、デフォルト: normal）'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=str(PROJECT_ROOT / 'docs' / 'report'),
        help='出力ディレクトリ（デフォルト: docs/report）'
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default=str(PROJECT_ROOT / 'data'),
        help='データディレクトリ（デフォルト: data）'
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    data_dir = Path(args.data_dir)
    
    # 既存CUBEの場合はpatternとtargetが必須
    if args.cube_type == 'normal':
        if not args.pattern:
            parser.error("既存CUBEの場合は--pattern引数が必要です")
        if not args.target:
            parser.error("既存CUBEの場合は--target引数が必要です")
    
    try:
        # データ読み込み
        logger.info("データを読み込んでいます...")
        df = load_past_results(data_dir)
        keisen_master = load_keisen_master(data_dir)
        logger.info(f"データ読み込み完了（{len(df)}回分）")
        
        # HTML出力
        file_path = export_cube_to_html(
            df=df,
            keisen_master=keisen_master,
            round_number=args.round,
            pattern=args.pattern,
            target=args.target,
            cube_type=args.cube_type,
            output_dir=output_dir
        )
        
        print(f"\n=== HTML出力完了 ===")
        print(f"ファイル: {file_path}")
        print(f"回号: {args.round}")
        if args.pattern:
            print(f"パターン: {args.pattern}")
        if args.target:
            print(f"対象: {args.target}")
        print(f"CUBEタイプ: {args.cube_type}")
        print(f"\nブラウザで開いて、コピーボタンでExcelに貼り付けてください。")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

