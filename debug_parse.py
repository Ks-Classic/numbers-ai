#!/usr/bin/env python3
"""
parsePage関数のロジックをテストするスクリプト
"""

import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.hpfree.com/numbers/rehearsal.html"

def extract_number_from_cell(cell_text):
    """セル文字列から数値を抽出（取り消し線・括弧・矢印に対応）"""
    if not cell_text:
        return None
    
    txt = cell_text.strip()
    
    # 矢印（→）の後の数字を取得（例: 8→0）
    arrow_match = re.search(r'[→→→](\d+)', txt)
    if arrow_match:
        return arrow_match.group(1)
    
    # 取り消し線を除去（U+0336 など）
    txt = re.sub(r'[\u0336\u0335\u0332]', '', txt)
    # 括弧付き注釈を除去 (例: (不), (落))
    txt = re.sub(r'\([^)]*\)', '', txt)
    # 数字だけ抽出
    digits = re.findall(r'\d', txt)
    if digits and len(digits) > 0:
        return digits[0]
    
    return None

def parse_page(html):
    """hpfree.comのページをパースして回号ごとのデータを取得"""
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables\n")
    
    for table_idx, table in enumerate(tables):
        print(f"=== Processing Table {table_idx + 1} ===")
        rows = table.find_all('tr')
        
        for row_idx, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) == 0:
                continue
            
            row_text = row.get_text()
            round_match = re.search(r'第(\d+)回', row_text)
            
            if not round_match:
                continue
            
            rnd = int(round_match.group(1))
            print(f"\n  Row {row_idx + 1}: Round {rnd} ({len(cells)} cells)")
            
            # 初期化
            if rnd not in result:
                result[rnd] = {
                    'n3_rehearsal': 'NULL',
                    'n4_rehearsal': 'NULL',
                    'n3_winning': 'NULL',
                    'n4_winning': 'NULL',
                }
            
            entry = result[rnd]
            
            # セルの内容を表示
            for i, cell in enumerate(cells[:12]):
                cell_text = cell.get_text(strip=True)
                extracted = extract_number_from_cell(cell_text)
                print(f"    Cell {i}: '{cell_text}' -> {extracted}")
            
            # N4 テーブルは 10 列以上、N3 は 8 列以上
            if len(cells) >= 10:
                print(f"  -> N4 table detected")
                # N4 リハーサル 4桁 (1~4 列)
                n4_re = []
                for i in range(1, 5):
                    d = extract_number_from_cell(cells[i].get_text(strip=True))
                    if d:
                        n4_re.append(d)
                
                # N4 当選 4桁 (6~9 列)
                n4_win = []
                for i in range(6, 10):
                    d = extract_number_from_cell(cells[i].get_text(strip=True))
                    if d:
                        n4_win.append(d)
                
                if len(n4_re) == 4:
                    entry['n4_rehearsal'] = ''.join(n4_re)
                    print(f"  -> N4 Rehearsal: {entry['n4_rehearsal']}")
                else:
                    print(f"  -> N4 Rehearsal: incomplete ({len(n4_re)}/4)")
                
                if len(n4_win) == 4:
                    entry['n4_winning'] = ''.join(n4_win)
                    print(f"  -> N4 Winning: {entry['n4_winning']}")
                else:
                    print(f"  -> N4 Winning: incomplete ({len(n4_win)}/4)")
                    
            elif len(cells) >= 8:
                print(f"  -> N3 table detected")
                # N3 リハーサル 3桁 (1~3 列)
                n3_re = []
                for i in range(1, 4):
                    d = extract_number_from_cell(cells[i].get_text(strip=True))
                    if d:
                        n3_re.append(d)
                
                # N3 当選 3桁 (5~7 列)
                n3_win = []
                for i in range(5, 8):
                    d = extract_number_from_cell(cells[i].get_text(strip=True))
                    if d:
                        n3_win.append(d)
                
                if len(n3_re) == 3:
                    entry['n3_rehearsal'] = ''.join(n3_re)
                    print(f"  -> N3 Rehearsal: {entry['n3_rehearsal']}")
                else:
                    print(f"  -> N3 Rehearsal: incomplete ({len(n3_re)}/3)")
                
                if len(n3_win) == 3:
                    entry['n3_winning'] = ''.join(n3_win)
                    print(f"  -> N3 Winning: {entry['n3_winning']}")
                else:
                    print(f"  -> N3 Winning: incomplete ({len(n3_win)}/3)")
    
    return result

def main():
    print(f"Fetching {URL}...")
    response = requests.get(URL, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code}")
        return
    
    print(f"✓ Page fetched successfully\n")
    
    result = parse_page(response.text)
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULT: {len(result)} rounds parsed")
    print(f"{'='*60}")
    
    # 最新の5回を表示
    sorted_rounds = sorted(result.keys(), reverse=True)[:5]
    for rnd in sorted_rounds:
        data = result[rnd]
        print(f"\nRound {rnd}:")
        print(f"  N3 Rehearsal: {data['n3_rehearsal']}")
        print(f"  N4 Rehearsal: {data['n4_rehearsal']}")
        print(f"  N3 Winning: {data['n3_winning']}")
        print(f"  N4 Winning: {data['n4_winning']}")

if __name__ == '__main__':
    main()
