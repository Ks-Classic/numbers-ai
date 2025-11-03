#!/usr/bin/env python3
"""
ナンバーズ過去当選番号・リハーサル番号取得スクリプト

Webページから直接データを取得して、past_results.csvを作成します。

データソース: https://www.hpfree.com/numbers/rehearsal2025-1.html
基準点: 第6758回（2025年6月30日）
取得件数: 300件（第6758回から第6459回まで）

注意: N3とN4のリハーサルは別々の表に表示されています。

使い方:
    python fetch_past_results.py [output_file] [--limit N]

出力:
    data/past_results.csv (デフォルト)
"""

import sys
import csv
import re
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    print("エラー: 必要なパッケージがインストールされていません。")
    print("以下のコマンドを実行してください:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)


# 基準点の定義
BASE_ROUND = 6758
BASE_DATE = datetime(2025, 6, 30)


def fetch_page(url: str, max_retries: int = 3) -> Optional[str]:
    """
    WebページのHTMLを取得
    
    Args:
        url: 取得するURL
        max_retries: 最大リトライ回数
        
    Returns:
        HTMLコンテンツ、またはNone
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # エンコーディングを自動検出
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'shift-jis'
            
            return response.text
        except Exception as e:
            print(f"⚠ 取得エラー (試行 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
            else:
                return None
    
    return None


def parse_n4_table(soup: BeautifulSoup) -> Dict[int, Dict[str, str]]:
    """
    N4の表データを抽出（4桁）
    
    Args:
        soup: BeautifulSoupオブジェクト
        
    Returns:
        回号をキーとした辞書
    """
    results = {}
    
    # 表を探す（N4リハーサル表）
    # ページ内の「ナンバーズ4 リハーサル」というテキストを含む表を探す
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 10:
                continue
            
            # 回号を含むセルを探す
            row_text = row.get_text()
            round_match = re.search(r'第(\d+)回', row_text)
            if not round_match:
                continue
            
            round_number = int(round_match.group(1))
            
            # セルから数字を抽出
            # 表の構造: 回号 | 千位(リ) | 百位(リ) | 十位(リ) | 一位(リ) | リ/本 | 千位(本) | 百位(本) | 十位(本) | 一位(本)
            try:
                # リハーサル数字（4桁）
                n4_rehearsal_digits = []
                for i in range(1, 5):  # 1-4番目のセル
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        # 特殊な記号を除去
                        cell_text = re.sub(r'\([^)]*\)', '', cell_text).strip()
                        if cell_text.isdigit():
                            n4_rehearsal_digits.append(cell_text)
                
                if len(n4_rehearsal_digits) != 4:
                    continue
                
                n4_rehearsal = ''.join(n4_rehearsal_digits)
                
                # 当選番号（4桁）
                n4_winning_digits = []
                for i in range(6, 10):  # 6-9番目のセル
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        # 特殊な記号を除去
                        cell_text = re.sub(r'\([^)]*\)', '', cell_text).strip()
                        if cell_text.isdigit():
                            n4_winning_digits.append(cell_text)
                
                if len(n4_winning_digits) != 4:
                    continue
                
                n4_winning = ''.join(n4_winning_digits)
                
                results[round_number] = {
                    'n4_winning': n4_winning,
                    'n4_rehearsal': n4_rehearsal,
                }
            except (ValueError, IndexError) as e:
                continue
    
    return results


def parse_n3_table(soup: BeautifulSoup) -> Dict[int, Dict[str, str]]:
    """
    N3の表データを抽出（3桁）
    
    Args:
        soup: BeautifulSoupオブジェクト
        
    Returns:
        回号をキーとした辞書
    """
    results = {}
    
    # 表を探す（N3リハーサル表）
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 8:
                continue
            
            # 回号を含むセルを探す
            row_text = row.get_text()
            round_match = re.search(r'第(\d+)回', row_text)
            if not round_match:
                continue
            
            round_number = int(round_match.group(1))
            
            # セルから数字を抽出
            # 表の構造: 回号 | 百位(リ) | 十位(リ) | 一位(リ) | リ/本 | 百位(本) | 十位(本) | 一位(本)
            try:
                # リハーサル数字（3桁）
                n3_rehearsal_digits = []
                for i in range(1, 4):  # 1-3番目のセル
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        # 特殊な記号を除去
                        cell_text = re.sub(r'\([^)]*\)', '', cell_text).strip()
                        if cell_text.isdigit():
                            n3_rehearsal_digits.append(cell_text)
                
                if len(n3_rehearsal_digits) != 3:
                    continue
                
                n3_rehearsal = ''.join(n3_rehearsal_digits)
                
                # 当選番号（3桁）
                n3_winning_digits = []
                for i in range(5, 8):  # 5-7番目のセル
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        # 特殊な記号を除去
                        cell_text = re.sub(r'\([^)]*\)', '', cell_text).strip()
                        if cell_text.isdigit():
                            n3_winning_digits.append(cell_text)
                
                if len(n3_winning_digits) != 3:
                    continue
                
                n3_winning = ''.join(n3_winning_digits)
                
                results[round_number] = {
                    'n3_winning': n3_winning,
                    'n3_rehearsal': n3_rehearsal,
                }
            except (ValueError, IndexError) as e:
                continue
    
    return results


def combine_data(n4_data: Dict[int, Dict[str, str]], n3_data: Dict[int, Dict[str, str]], max_rounds: int = 300) -> List[Dict[str, str]]:
    """
    N4とN3のデータを結合
    
    Args:
        n4_data: N4のデータ辞書
        n3_data: N3のデータ辞書
        max_rounds: 取得する最大件数
        
    Returns:
        結合したデータのリスト
    """
    results = []
    
    # 基準点から指定件数分の回号を生成
    target_rounds = set(range(BASE_ROUND - max_rounds + 1, BASE_ROUND + 1))
    
    # 取得したデータの回号と一致するものを使用
    available_rounds = set(n4_data.keys()) | set(n3_data.keys())
    
    # デバッグ情報
    if available_rounds:
        min_round = min(available_rounds)
        max_round = max(available_rounds)
        print(f"   取得データ範囲: 第{min_round}回 ～ 第{max_round}回（{len(available_rounds)}件）")
        print(f"   目標範囲: 第{min(target_rounds)}回 ～ 第{max(target_rounds)}回（{len(target_rounds)}件）")
    
    target_rounds = target_rounds & available_rounds
    
    print(f"   一致するデータ: {len(target_rounds)}件")
    
    # N4データがない回号を確認
    missing_n4 = [r for r in target_rounds if r not in n4_data.keys()]
    if missing_n4:
        print(f"   N4データがない回号: {sorted(missing_n4)[:10]}...（{len(missing_n4)}件）")
    
    for round_number in sorted(target_rounds, reverse=True):
        # N4データを取得
        n4_info = n4_data.get(round_number, {})
        n4_winning = n4_info.get('n4_winning', '')
        n4_rehearsal = n4_info.get('n4_rehearsal', '')
        
        # N3データを取得
        n3_info = n3_data.get(round_number, {})
        n3_winning = n3_info.get('n3_winning', '')
        n3_rehearsal = n3_info.get('n3_rehearsal', '')
        
        # N4のデータがなければスキップ
        if not n4_winning:
            continue
        
        # 日付を計算（基準点から逆算）
        days_back = BASE_ROUND - round_number
        draw_date = BASE_DATE - timedelta(days=days_back)
        
        results.append({
            'round_number': round_number,
            'draw_date': draw_date.strftime('%Y-%m-%d'),
            'n3_winning': n3_winning if n3_winning else '',
            'n4_winning': n4_winning,
            'n3_rehearsal': n3_rehearsal if n3_rehearsal else '',
            'n4_rehearsal': n4_rehearsal if n4_rehearsal else '',
        })
    
    return results


def save_to_csv(data: List[Dict[str, str]], output_file: Path):
    """
    CSVファイルに保存
    
    Args:
        data: 保存するデータのリスト
        output_file: 出力ファイルパス
    """
    # ディレクトリを作成
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'round_number',
        'draw_date',
        'n3_winning',
        'n4_winning',
        'n3_rehearsal',
        'n4_rehearsal'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            # NULL値の処理（空文字列をNULLに変換）
            csv_row = {}
            for key in fieldnames:
                value = row.get(key, '')
                csv_row[key] = value if value else 'NULL'
            
            writer.writerow(csv_row)
    
    print(f"✓ CSVファイルを保存しました: {output_file}")
    print(f"  データ件数: {len(data)}件")


def fetch_multiple_pages(base_url: str, max_rounds: int) -> tuple[Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
    """
    複数のページからデータを取得
    
    Args:
        base_url: ベースURL
        max_rounds: 取得する最大件数
        
    Returns:
        (n4_data, n3_data) のタプル
    """
    n4_data = {}
    n3_data = {}
    
    # 複数のページを試行
    # 300件取得するには、第6459回までのデータが必要
    # 基準点からさかのぼるため、より古いページも取得
    page_patterns = []
    
    # 2025年分
    for i in range(1, 5):
        page_patterns.append(f'rehearsal2025-{i}.html')
    
    # 2024年分
    for i in range(1, 5):
        page_patterns.append(f'rehearsal2024-{i}.html')
    
    # 2023年分
    for i in range(1, 5):
        page_patterns.append(f'rehearsal2023-{i}.html')
    
    # 2022年分
    for i in range(1, 5):
        page_patterns.append(f'rehearsal2022-{i}.html')
    
    # 2021年分
    for i in range(1, 5):
        page_patterns.append(f'rehearsal2021-{i}.html')
    
    base_path = '/'.join(base_url.split('/')[:-1])
    
    for page_pattern in page_patterns:
        url = f"{base_path}/{page_pattern}"
        
        print(f"\n📥 ページを取得中: {page_pattern}...")
        html_content = fetch_page(url)
        
        if not html_content:
            print(f"⚠ ページの取得に失敗しました: {page_pattern}")
            continue
        
        print(f"✓ ページを取得しました ({len(html_content)}文字)")
        
        # HTMLをパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # N4データを抽出
        page_n4_data = parse_n4_table(soup)
        n4_data.update(page_n4_data)
        print(f"✓ {len(page_n4_data)}件のN4データを抽出しました（累計: {len(n4_data)}件）")
        
        # N3データを抽出
        page_n3_data = parse_n3_table(soup)
        n3_data.update(page_n3_data)
        print(f"✓ {len(page_n3_data)}件のN3データを抽出しました（累計: {len(n3_data)}件）")
        
        # 必要な件数に達したか、目標範囲内のデータが十分に取得できたか確認
        # 目標範囲: 第6459回～第6758回（300件）
        target_min_round = BASE_ROUND - max_rounds + 1
        target_rounds_in_data = [r for r in n4_data.keys() if target_min_round <= r <= BASE_ROUND]
        
        if len(target_rounds_in_data) >= max_rounds:
            print(f"\n✓ 目標範囲内のデータが十分に取得できました（{len(target_rounds_in_data)}件 >= {max_rounds}件）")
            break
        
        # 次のページに進む前に少し待機
        time.sleep(1)
    
    return n4_data, n3_data


def main():
    if not HAS_DEPS:
        sys.exit(1)
    
    # 引数解析
    output_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'
    max_rounds = 300
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--limit' and len(sys.argv) > 2:
            max_rounds = int(sys.argv[2])
        elif not sys.argv[1].startswith('--'):
            output_file = Path(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[1] != '--limit':
        try:
            max_rounds = int(sys.argv[2])
        except ValueError:
            pass
    
    # ベースURL
    base_url = 'https://www.hpfree.com/numbers/rehearsal2025-1.html'
    
    print("=" * 80)
    print("ナンバーズ過去当選番号・リハーサル番号取得スクリプト")
    print("=" * 80)
    print(f"\n基準点: 第{BASE_ROUND}回 ({BASE_DATE.strftime('%Y-%m-%d')})")
    print(f"取得件数: {max_rounds}件（第{BASE_ROUND}回から第{BASE_ROUND - max_rounds + 1}回まで）")
    print(f"出力先: {output_file}\n")
    
    # 複数ページからデータを取得
    n4_data, n3_data = fetch_multiple_pages(base_url, max_rounds)
    
    if not n4_data:
        print("✗ データが取得できませんでした")
        sys.exit(1)
    
    # データを結合
    print("\n🔗 データを結合中...")
    data = combine_data(n4_data, n3_data, max_rounds)
    print(f"✓ {len(data)}件のデータを結合しました")
    
    if not data:
        print("⚠ データが抽出できませんでした")
        print("\nデバッグ情報:")
        print("HTMLの一部を表示します...")
        print(html_content[:2000])
        sys.exit(1)
    
    # 抽出結果を表示（最初の5件）
    print("\n【抽出結果（最初の5件）】")
    print("-" * 80)
    for i, row in enumerate(data[:5]):
        print(f"第{row['round_number']}回 ({row['draw_date']}): "
              f"N3={row['n3_winning']}(リ:{row['n3_rehearsal'] or 'なし'}), "
              f"N4={row['n4_winning']}(リ:{row['n4_rehearsal'] or 'なし'})")
    
    if len(data) > 5:
        print(f"... 他 {len(data) - 5}件")
    
    # CSVファイルに保存
    print("\n💾 CSVファイルに保存中...")
    save_to_csv(data, output_file)
    
    print("\n" + "=" * 80)
    print("✓ 処理完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
