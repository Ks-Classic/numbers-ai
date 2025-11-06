#!/usr/bin/env python3
"""
みずほ銀行のページ取得テストスクリプト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fetch_past_results import fetch_page, MIZUHO_INDEX_URL, MIZUHO_BASE_URL
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def test_mizuhobank_index():
    """みずほ銀行のインデックスページをテスト"""
    print("=" * 80)
    print("みずほ銀行のページ取得テスト")
    print("=" * 80)
    
    print(f"\n1. ページを取得中: {MIZUHO_INDEX_URL}")
    html_content = fetch_page(MIZUHO_INDEX_URL)
    
    if not html_content:
        print("❌ ページの取得に失敗しました")
        return
    
    print(f"✓ ページを取得しました ({len(html_content)}文字)")
    
    # HTMLの一部を表示
    print(f"\n2. HTMLの最初の1000文字:")
    print("-" * 80)
    print(html_content[:1000])
    print("-" * 80)
    
    # HTMLをパース
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print(f"\n3. 全てのリンクを検索:")
    print("-" * 80)
    links = soup.find_all('a', href=True)
    print(f"   見つかったリンク数: {len(links)}")
    
    # バックナンバー関連のリンクを探す
    backnumber_links = []
    for i, link in enumerate(links[:50]):  # 最初の50件を表示
        href = link.get('href', '')
        text = link.get_text().strip()
        
        # numXXXX.html または detail.html を含むリンク
        if 'num' in href.lower() or 'detail' in href.lower() or 'backnumber' in href.lower():
            backnumber_links.append((href, text))
            print(f"   [{i+1}] {href[:80]} ... (テキスト: {text[:30]})")
    
    print(f"\n   バックナンバー関連のリンク数: {len(backnumber_links)}")
    
    # テーブル内のリンクを探す
    print(f"\n4. テーブル内のリンクを検索:")
    print("-" * 80)
    tables = soup.find_all('table')
    print(f"   見つかったテーブル数: {len(tables)}")
    
    for i, table in enumerate(tables):
        table_links = table.find_all('a', href=True)
        if table_links:
            print(f"\n   テーブル {i+1}: {len(table_links)}件のリンク")
            for j, link in enumerate(table_links[:10]):
                href = link.get('href', '')
                text = link.get_text().strip()
                print(f"      [{j+1}] {href[:80]} ... (テキスト: {text[:30]})")
    
    # （B表）A表以前の当せん番号の範囲を探す
    print(f"\n5. （B表）A表以前の当せん番号の範囲を検索:")
    print("-" * 80)
    # 「B表」や「A表以前」などのテキストを含む要素を探す
    b_table_elements = soup.find_all(string=re.compile(r'B表|A表以前'))
    print(f"   'B表'または'A表以前'を含む要素数: {len(b_table_elements)}")
    
    for i, elem in enumerate(b_table_elements[:5]):
        print(f"   [{i+1}] {elem[:100]}")
        # 親要素を取得
        parent = elem.parent
        if parent:
            print(f"       親要素: {parent.name}")
            # 親要素内のリンクを探す
            parent_links = parent.find_all('a', href=True)
            if parent_links:
                print(f"       親要素内のリンク数: {len(parent_links)}")
                for link in parent_links[:5]:
                    href = link.get('href', '')
                    print(f"         - {href}")

if __name__ == "__main__":
    test_mizuhobank_index()

