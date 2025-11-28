#!/usr/bin/env python3
"""
エンコーディングを確認してパースするスクリプト
"""

import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.hpfree.com/numbers/rehearsal.html"

def extract_number_from_cell(cell_text):
    """セル文字列から数値を抽出"""
    if not cell_text:
        return None
    
    txt = cell_text.strip()
    
    # 矢印（→）の後の数字を取得
    arrow_match = re.search(r'[→→→](\d+)', txt)
    if arrow_match:
        return arrow_match.group(1)
    
    # 取り消し線を除去
    txt = re.sub(r'[\u0336\u0335\u0332]', '', txt)
    # 括弧付き注釈を除去
    txt = re.sub(r'\([^)]*\)', '', txt)
    # 数字だけ抽出
    digits = re.findall(r'\d', txt)
    if digits and len(digits) > 0:
        return digits[0]
    
    return None

def main():
    print(f"Fetching {URL}...")
    response = requests.get(URL, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code}")
        return
    
    # エンコーディング情報を表示
    print(f"Response encoding: {response.encoding}")
    print(f"Apparent encoding: {response.apparent_encoding}")
    print(f"Content-Type header: {response.headers.get('Content-Type', 'N/A')}")
    
    # HTMLからエンコーディングを検出
    print(f"\nFirst 500 bytes (raw):")
    print(response.content[:500])
    
    # Shift_JISでデコードしてみる
    print(f"\n{'='*60}")
    print("Trying Shift_JIS encoding...")
    print(f"{'='*60}")
    
    try:
        html_sjis = response.content.decode('shift_jis')
        soup = BeautifulSoup(html_sjis, 'html.parser')
        
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")
        
        # 最初のテーブルの最初の5行を表示
        if tables:
            table = tables[0]
            rows = table.find_all('tr')
            print(f"\nFirst table has {len(rows)} rows\n")
            
            for row_idx, row in enumerate(rows[:5]):
                cells = row.find_all(['td', 'th'])
                row_text = row.get_text(strip=True)
                print(f"Row {row_idx + 1} ({len(cells)} cells): {row_text[:100]}")
                
                # 回号を探す
                round_match = re.search(r'第(\d+)回', row_text)
                if round_match:
                    rnd = int(round_match.group(1))
                    print(f"  ✓ Found round: {rnd}")
                    
                    # セルの内容を表示
                    for i, cell in enumerate(cells[:12]):
                        cell_text = cell.get_text(strip=True)
                        extracted = extract_number_from_cell(cell_text)
                        if cell_text:
                            print(f"    Cell {i}: '{cell_text}' -> {extracted}")
                
                print()
    
    except Exception as e:
        print(f"Shift_JIS decode failed: {e}")
    
    # UTF-8でも試す
    print(f"\n{'='*60}")
    print("Trying UTF-8 encoding...")
    print(f"{'='*60}")
    
    try:
        html_utf8 = response.content.decode('utf-8')
        soup = BeautifulSoup(html_utf8, 'html.parser')
        
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")
        
        if tables:
            table = tables[0]
            rows = table.find_all('tr')
            print(f"\nFirst table has {len(rows)} rows\n")
            
            for row_idx, row in enumerate(rows[:3]):
                cells = row.find_all(['td', 'th'])
                row_text = row.get_text(strip=True)
                print(f"Row {row_idx + 1}: {row_text[:100]}")
    
    except Exception as e:
        print(f"UTF-8 decode failed: {e}")

if __name__ == '__main__':
    main()
