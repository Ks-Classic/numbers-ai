#!/usr/bin/env python3
"""
ナンバーズ過去当選番号・リハーサル番号取得スクリプト（シンプル版）

データソース: https://www.hpfree.com/numbers/rehearsal.html
最新の1件のみを取得してpast_results.csvに追加します。
"""

import sys
import re
from pathlib import Path
from typing import Optional, Dict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("エラー: 必要なパッケージがインストールされていません。")
    print("以下のコマンドを実行してください:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)

# データソースURL
LATEST_PAGE_URL = 'https://www.hpfree.com/numbers/rehearsal.html'

def fetch_page(url: str) -> Optional[str]:
    """WebページのHTMLを取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if response.encoding is None or response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding or 'shift-jis'
        
        return response.text
    except Exception as e:
        print(f"⚠ ページ取得エラー: {e}")
        return None

def extract_number_from_cell(cell_text: str) -> Optional[str]:
    """
    セルから数値を抽出（特殊表記に対応）
    
    対応する特殊表記:
    - 取り消し線: 8̶
    - 変更記号: 7→5, 8̶→0
    - 括弧付き注釈: (不), (落), (早)
    """
    if not cell_text:
        return None
    
    text = cell_text.strip()
    
    # 矢印の後の数字を取得（最終的な値）
    arrow_match = re.search(r'[→→→](\d+)', text)
    if arrow_match:
        return arrow_match.group(1)
    
    # 取り消し線を除去
    text = re.sub(r'[\u0336\u0335\u0332]', '', text)
    
    # 括弧付きの注釈を除去
    text = re.sub(r'\([^)]*\)', '', text)
    
    # 数字のみを抽出
    digits = re.findall(r'\d', text)
    if digits:
        return digits[0]
    
    return None

def parse_latest_data(html_content: str) -> Optional[Dict]:
    """最新のN4とN3データを抽出"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    n4_data = None
    n3_data = None
    
    # テーブルを探す
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # 回号を含むセルを探す
            row_text = row.get_text()
            round_match = re.search(r'第(\d+)回', row_text)
            if not round_match:
                continue
            
            round_number = int(round_match.group(1))
            
            # N4データ（10列: 回号 + リハーサル4桁 + リ/本 + 当選4桁）
            if len(cells) >= 10 and not n4_data:
                try:
                    # リハーサル数字（4桁）
                    n4_rehearsal_digits = []
                    for i in range(1, 5):
                        if i < len(cells):
                            cell_text = cells[i].get_text().strip()
                            digit = extract_number_from_cell(cell_text)
                            if digit:
                                n4_rehearsal_digits.append(digit)
                    
                    # 当選番号（4桁）
                    n4_winning_digits = []
                    for i in range(6, 10):
                        if i < len(cells):
                            cell_text = cells[i].get_text().strip()
                            digit = extract_number_from_cell(cell_text)
                            if digit:
                                n4_winning_digits.append(digit)
                    
                    if len(n4_rehearsal_digits) == 4:
                        n4_data = {
                            'round_number': round_number,
                            'n4_rehearsal': ''.join(n4_rehearsal_digits),
                            'n4_winning': ''.join(n4_winning_digits) if len(n4_winning_digits) == 4 else 'NULL',
                        }
                except:
                    pass
            
            # N3データ（8列: 回号 + リハーサル3桁 + リ/本 + 当選3桁）
            elif len(cells) >= 8 and not n3_data:
                try:
                    # リハーサル数字（3桁）
                    n3_rehearsal_digits = []
                    for i in range(1, 4):
                        if i < len(cells):
                            cell_text = cells[i].get_text().strip()
                            digit = extract_number_from_cell(cell_text)
                            if digit:
                                n3_rehearsal_digits.append(digit)
                    
                    # 当選番号（3桁）
                    n3_winning_digits = []
                    for i in range(5, 8):
                        if i < len(cells):
                            cell_text = cells[i].get_text().strip()
                            digit = extract_number_from_cell(cell_text)
                            if digit:
                                n3_winning_digits.append(digit)
                    
                    if len(n3_rehearsal_digits) == 3:
                        n3_data = {
                            'round_number': round_number,
                            'n3_rehearsal': ''.join(n3_rehearsal_digits),
                            'n3_winning': ''.join(n3_winning_digits) if len(n3_winning_digits) == 3 else 'NULL',
                        }
                except:
                    pass
            
            # 両方取得できたら終了
            if n4_data and n3_data:
                break
        
        if n4_data and n3_data:
            break
    
    # データを結合
    if n4_data and n3_data and n4_data['round_number'] == n3_data['round_number']:
        return {
            'round_number': n4_data['round_number'],
            'n3_rehearsal': n3_data['n3_rehearsal'],
            'n4_rehearsal': n4_data['n4_rehearsal'],
            'n3_winning': n3_data['n3_winning'],
            'n4_winning': n4_data['n4_winning'],
        }
    
    return None

def update_csv(data: Dict, csv_path: str) -> bool:
    """CSVファイルを更新"""
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        print(f"⚠ CSVファイルが見つかりません: {csv_path}")
        return False
    
    # 既存のCSVを読み込み
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # ヘッダー
    header = lines[0].strip()
    
    # 既存の回号をチェック
    existing_rounds = []
    for line in lines[1:]:
        if line.strip():
            cols = line.strip().split(',')
            if cols:
                try:
                    existing_rounds.append(int(cols[0]))
                except:
                    pass
    
    # 既に存在する場合はスキップ
    if data['round_number'] in existing_rounds:
        print(f"ℹ️  回号{data['round_number']}は既に存在します。スキップします。")
        return False
    
    # 新しい行を作成（日付とweekdayはNULL）
    new_row = f"{data['round_number']},NULL,NULL,{data['n3_rehearsal']},{data['n4_rehearsal']},{data['n3_winning']},{data['n4_winning']}\n"
    
    # 最新が一番上になるように挿入
    lines.insert(1, new_row)
    
    # ファイルに書き込み
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ 回号{data['round_number']}のデータを追加しました")
    return True

def main():
    print("📥 最新データを取得中...")
    
    # HTMLを取得
    html_content = fetch_page(LATEST_PAGE_URL)
    
    if not html_content:
        print("❌ ページの取得に失敗しました")
        sys.exit(1)
    
    # データを抽出
    data = parse_latest_data(html_content)
    
    if not data:
        print("❌ データの抽出に失敗しました")
        sys.exit(1)
    
    print(f"✓ 第{data['round_number']}回のデータを取得しました")
    print(f"  N3リハーサル: {data['n3_rehearsal']}")
    print(f"  N4リハーサル: {data['n4_rehearsal']}")
    print(f"  N3当選: {data['n3_winning']}")
    print(f"  N4当選: {data['n4_winning']}")
    
    # CSVを更新
    csv_path = Path(__file__).parent.parent.parent / 'data' / 'past_results.csv'
    success = update_csv(data, str(csv_path))
    
    if success:
        print("✅ データ更新完了")
    else:
        print("ℹ️  更新なし")

if __name__ == '__main__':
    main()
