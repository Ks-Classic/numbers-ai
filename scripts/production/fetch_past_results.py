#!/usr/bin/env python3
"""
ナンバーズ過去当選番号・リハーサル番号取得スクリプト

Webページから直接データを取得して、past_results.csvを作成します。

データソース: https://www.hpfree.com/numbers/rehearsal.html
最新回号を自動取得し、そこから過去分を取得します。
過去分のページは自動で探索します。

使い方:
    python3 fetch_past_results.py [output_file] [--limit N] [--use-fallback]

オプション:
    output_file      出力ファイルパス（デフォルト: data/past_results.csv）
    --limit N        取得する最大件数（デフォルト: 300、手動実行時は1000など大量取得可能）
    --use-fallback   Webスクレイピング失敗時に検索APIを使用

出力:
    data/past_results.csv (デフォルト)
"""

import sys
import csv
import re
import time
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
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

# 環境変数からAPIキーを読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがなくても動作するようにする

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SERP_API_KEY = os.getenv('SERP_API_KEY')

# 最新版ページのURL
LATEST_PAGE_URL = 'https://www.hpfree.com/numbers/rehearsal.html'
BASE_PAGE_URL = 'https://www.hpfree.com/numbers/'

# みずほ銀行のページURL（4800回以前用）
MIZUHO_BASE_URL = 'https://www.mizuhobank.co.jp/takarakuji/check/numbers/backnumber/'
MIZUHO_INDEX_URL = 'https://www.mizuhobank.co.jp/takarakuji/check/numbers/backnumber/index.html'

# みずほ銀行の最新データページURL（日付が含まれている）
MIZUHO_LATEST_N4_URL = 'https://www.mizuhobank.co.jp/takarakuji/check/numbers/numbers4/index.html'
MIZUHO_LATEST_N3_URL = 'https://www.mizuhobank.co.jp/takarakuji/check/numbers/numbers3/index.html'

# リハーサル番号が取得可能になる回号
REHEARSAL_AVAILABLE_FROM = 4801


def extract_number_from_cell(cell_text: str) -> Optional[str]:
    """
    セルから数値を抽出（特殊表記に対応）
    
    対応する特殊表記:
    - 取り消し線: 8̶
    - 変更記号: 7→5, 8̶→0
    - 括弧付き注釈: (不), (落), (早)
    - 複合: 8̶→0(不)(不), 7→5(不)(落)
    
    Args:
        cell_text: セルのテキスト内容
        
    Returns:
        抽出された数値（1桁の文字列）、またはNone
    """
    if not cell_text:
        return None
    
    # テキストを正規化（空白を除去）
    text = cell_text.strip()
    
    # 取り消し線を含む変更パターン: 8̶→0 または 8→0
    # 矢印の後の数字を取得（最終的な値）
    # 矢印記号: → (U+2192) または → (全角)
    arrow_match = re.search(r'[→→→](\d+)', text)
    if arrow_match:
        # 矢印の後の数字を返す（最終的な値）
        return arrow_match.group(1)
    
    # 取り消し線だけの場合（例: 8̶）、単純な数字を探す
    # 取り消し線記号（U+0336）を除去
    text = re.sub(r'[\u0336\u0335\u0332]', '', text)  # 各種取り消し線記号
    
    # 括弧付きの注釈を除去: (不), (落), (早) など
    text = re.sub(r'\([^)]*\)', '', text)
    
    # 数字のみを抽出
    digits = re.findall(r'\d', text)
    if digits:
        # 最初の数字を返す（通常は1桁のはず）
        return digits[0]
    
    return None


def get_latest_round_number() -> Optional[int]:
    """
    最新版ページから最新の回号を取得する
    
    Returns:
        最新の回号、またはNone
    """
    print(f"📥 最新版ページを取得中: {LATEST_PAGE_URL}...")
    html_content = fetch_page(LATEST_PAGE_URL)
    
    if not html_content:
        print("⚠ 最新版ページの取得に失敗しました")
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 最新の回号を探す（表の最初の行から）
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            row_text = row.get_text()
            # 回号のパターンを探す（第XXXX回）
            round_matches = re.findall(r'第(\d+)回', row_text)
            if round_matches:
                # 最新の回号（最大値）を返す
                round_numbers = [int(r) for r in round_matches]
                if round_numbers:
                    latest_round = max(round_numbers)
                    print(f"✓ 最新回号を取得しました: 第{latest_round}回")
                    return latest_round
    
    print("⚠ 最新回号が見つかりませんでした")
    return None


def find_past_pages(base_url: str) -> List[str]:
    """
    過去分のページを自動探索する
    
    Args:
        base_url: ベースURL
        
    Returns:
        見つかったページURLのリスト
    """
    print(f"\n🔍 過去分のページを探索中...")
    found_pages = []
    
    # まず最新版ページからリンクを取得
    html_content = fetch_page(LATEST_PAGE_URL)
    if not html_content:
        print("⚠ 最新版ページの取得に失敗しました")
        return found_pages
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 過去分へのリンクを探す（rehearsal20XX-X.html のパターン）
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '')
        # rehearsal20XX-X.html のパターンを探す
        match = re.search(r'rehearsal(\d{4})-(\d+)\.html', href)
        if match:
            year = int(match.group(1))
            quarter = int(match.group(2))
            
            # 絶対URLに変換
            if href.startswith('/'):
                full_url = f"{BASE_PAGE_URL.rstrip('/')}{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(BASE_PAGE_URL, href)
            
            if full_url not in found_pages:
                found_pages.append(full_url)
                print(f"  ✓ ページを発見: {href} ({year}年{quarter}期)")
    
    # 見つからない場合は、既知のパターンで生成
    if not found_pages:
        print("  ⚠ リンクからページが見つかりませんでした。既知のパターンで生成します...")
        current_year = datetime.now().year
        
        # 過去5年分を生成（半期ごとに4ページ）
        for year in range(current_year - 4, current_year + 1):
            for quarter in range(1, 5):
                page_url = f"{BASE_PAGE_URL}rehearsal{year}-{quarter}.html"
                found_pages.append(page_url)
    
    print(f"✓ {len(found_pages)}件のページを発見しました")
    return found_pages


def is_draw_day(date: datetime = None) -> bool:
    """
    抽選日かどうかを判定（平日かつ年末年始でない）
    
    Args:
        date: 判定する日付（デフォルト: 今日）
        
    Returns:
        抽選日の場合True
    """
    if date is None:
        date = datetime.now()
    
    # 週末を除外（月曜=0, 日曜=6）
    weekday = date.weekday()
    if weekday >= 5:  # 土曜日(5)または日曜日(6)
        return False
    
    # 年末年始を除外（12/29〜1/3）
    month = date.month
    day = date.day
    
    if month == 12 and day >= 29:
        return False
    if month == 1 and day <= 3:
        return False
    
    return True


def calculate_weekday(draw_date: Optional[str]) -> Optional[int]:
    """
    日付から曜日を計算（0-4の整数）
    
    Args:
        draw_date: 日付文字列（YYYY-MM-DD形式、NULL可）
    
    Returns:
        曜日（0:月, 1:火, 2:水, 3:木, 4:金）、NULLの場合はNone
    """
    if not draw_date or draw_date == 'NULL' or not draw_date.strip():
        return None
    
    try:
        date_obj = datetime.strptime(draw_date, '%Y-%m-%d')
        weekday = date_obj.weekday()
        # ナンバーズは平日のみ抽選のため、0-4の値のみ
        if weekday < 5:
            return weekday
        return None
    except (ValueError, TypeError):
        return None


def fetch_with_gemini_api(query: str) -> Optional[str]:
    """
    Gemini APIを使用して情報を取得する
    
    Args:
        query: 検索クエリ
        
    Returns:
        取得した情報、またはNone
    """
    if not GEMINI_API_KEY:
        return None
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"ナンバーズの最新当選番号について検索してください。{query} 最新の回号、N3当選番号、N4当選番号、リハーサル数字を教えてください。JSON形式で返してください。"
                }]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text']
            return content
        
        return None
    except Exception as e:
        print(f"⚠ Gemini API取得エラー: {e}")
        return None


def fetch_with_serp_api(query: str) -> Optional[str]:
    """
    SerpAPI (Google Search API)を使用して情報を取得する
    
    Args:
        query: 検索クエリ
        
    Returns:
        取得した情報、またはNone
    """
    if not SERP_API_KEY:
        return None
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": SERP_API_KEY,
            "engine": "google",
            "hl": "ja",
            "gl": "jp"
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        # 検索結果のスニペットを返す
        if 'organic_results' in result and len(result['organic_results']) > 0:
            snippets = [r.get('snippet', '') for r in result['organic_results'][:3]]
            return '\n'.join(snippets)
        
        return None
    except Exception as e:
        print(f"⚠ SerpAPI取得エラー: {e}")
        return None


def parse_fallback_data(api_result: str) -> Optional[Dict[int, Dict[str, str]]]:
    """
    APIから取得したデータをパースして辞書形式に変換
    
    Args:
        api_result: APIから取得したテキスト
        
    Returns:
        回号をキーとした辞書、またはNone
    """
    if not api_result:
        return None
    
    results = {}
    
    # JSON形式を試す
    try:
        # JSON形式の部分を抽出
        json_match = re.search(r'\{[^{}]*"round_number"[^{}]*\}', api_result)
        if json_match:
            data = json.loads(json_match.group())
            round_number = data.get('round_number')
            if round_number:
                results[round_number] = {
                    'n3_winning': data.get('n3_winning', ''),
                    'n4_winning': data.get('n4_winning', ''),
                    'n3_rehearsal': data.get('n3_rehearsal', ''),
                    'n4_rehearsal': data.get('n4_rehearsal', ''),
                }
                return results
    except:
        pass
    
    # テキスト形式から抽出を試す
    # 回号のパターンを探す
    round_match = re.search(r'第(\d+)回', api_result)
    if round_match:
        round_number = int(round_match.group(1))
        
        # N3当選番号
        n3_match = re.search(r'N3[：:]\s*(\d{3})', api_result)
        n3_winning = n3_match.group(1) if n3_match else ''
        
        # N4当選番号
        n4_match = re.search(r'N4[：:]\s*(\d{4})', api_result)
        n4_winning = n4_match.group(1) if n4_match else ''
        
        # リハーサル数字
        n3_rehearsal_match = re.search(r'リハーサル[：:]\s*(\d{3})', api_result)
        n3_rehearsal = n3_rehearsal_match.group(1) if n3_rehearsal_match else ''
        
        n4_rehearsal_match = re.search(r'N4.*リハーサル[：:]\s*(\d{4})', api_result)
        n4_rehearsal = n4_rehearsal_match.group(1) if n4_rehearsal_match else ''
        
        results[round_number] = {
            'n3_winning': n3_winning,
            'n4_winning': n4_winning,
            'n3_rehearsal': n3_rehearsal,
            'n4_rehearsal': n4_rehearsal,
        }
        
        return results
    
    return None


def fetch_with_fallback(base_url: str, max_rounds: int) -> Tuple[Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
    """
    Webスクレイピングに失敗した場合、検索APIでフォールバック
    
    Args:
        base_url: ベースURL
        max_rounds: 取得する最大件数
        
    Returns:
        (n4_data, n3_data) のタプル
    """
    print("\n⚠ Webスクレイピングに失敗しました。検索APIでフォールバックを試行します...")
    
    n4_data = {}
    n3_data = {}
    
    # 最新の回号を検索
    query = "ナンバーズ 最新 当選番号 リハーサル"
    
    # Gemini APIを優先的に試す
    if GEMINI_API_KEY:
        print("📡 Gemini APIで検索中...")
        api_result = fetch_with_gemini_api(query)
        if api_result:
            parsed = parse_fallback_data(api_result)
            if parsed:
                # N4とN3のデータを分ける
                for round_num, data in parsed.items():
                    if data.get('n4_winning'):
                        n4_data[round_num] = {
                            'n4_winning': data.get('n4_winning', ''),
                            'n4_rehearsal': data.get('n4_rehearsal', ''),
                        }
                    if data.get('n3_winning'):
                        n3_data[round_num] = {
                            'n3_winning': data.get('n3_winning', ''),
                            'n3_rehearsal': data.get('n3_rehearsal', ''),
                        }
                if n4_data or n3_data:
                    print(f"✓ Gemini APIでデータを取得しました（{len(n4_data)}件のN4、{len(n3_data)}件のN3）")
                    return n4_data, n3_data
    
    # SerpAPIを試す
    if SERP_API_KEY:
        print("📡 SerpAPIで検索中...")
        api_result = fetch_with_serp_api(query)
        if api_result:
            parsed = parse_fallback_data(api_result)
            if parsed:
                for round_num, data in parsed.items():
                    if data.get('n4_winning'):
                        n4_data[round_num] = {
                            'n4_winning': data.get('n4_winning', ''),
                            'n4_rehearsal': data.get('n4_rehearsal', ''),
                        }
                    if data.get('n3_winning'):
                        n3_data[round_num] = {
                            'n3_winning': data.get('n3_winning', ''),
                            'n3_rehearsal': data.get('n3_rehearsal', ''),
                        }
                if n4_data or n3_data:
                    print(f"✓ SerpAPIでデータを取得しました（{len(n4_data)}件のN4、{len(n3_data)}件のN3）")
                    return n4_data, n3_data
    
    print("✗ 検索APIでもデータを取得できませんでした")
    return n4_data, n3_data


def fetch_page(url: str, max_retries: int = 3) -> Optional[str]:
    """
    WebページのHTMLを取得
    
    Args:
        url: 取得するURL
        max_retries: 最大リトライ回数
        
    Returns:
        HTMLコンテンツ、またはNone（404エラーの場合もNoneを返す）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # 404エラーの場合は特別処理（ページが存在しない）
            if response.status_code == 404:
                print(f"   ⚠ 404エラー: ページが存在しません - {url}")
                return None
            
            response.raise_for_status()
            
            # エンコーディングを自動検出
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'shift-jis'
            
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"   ⚠ 404エラー: ページが存在しません - {url}")
                return None
            print(f"⚠ 取得エラー (試行 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
            else:
                return None
        except Exception as e:
            print(f"⚠ 取得エラー (試行 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
            else:
                return None
    
    return None


def fetch_mizuhobank_csv(round_number: int, session: Optional[requests.Session] = None) -> Optional[str]:
    """
    みずほ銀行のCSVファイルを取得
    
    CSVファイルのURL形式:
    https://www.mizuhobank.co.jp/retail/takarakuji/numbers/csv/A100{round_number:04d}.CSV
    
    Args:
        round_number: 回号
        session: requests.Sessionオブジェクト（再利用用、Noneの場合は新規作成）
        
    Returns:
        CSVファイルの内容（Shift_JISエンコーディング）、またはNone
    """
    csv_url = f'https://www.mizuhobank.co.jp/retail/takarakuji/numbers/csv/A100{round_number:04d}.CSV'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # セッションが提供されていない場合は新規作成
    if session is None:
        session = requests.Session()
        session.headers.update(headers)
    
    try:
        response = session.get(csv_url, timeout=30)
        
        if response.status_code == 404:
            return None
        
        # 403エラー（アクセス拒否）の場合もスキップ
        if response.status_code == 403:
            return None
        
        response.raise_for_status()
        
        # Shift_JISエンコーディングで取得
        response.encoding = 'shift_jis'
        
        return response.text
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return None
        raise
    except Exception as e:
        return None


def parse_mizuhobank_csv(csv_content: str, round_number: int, max_round: Optional[int] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    みずほ銀行のCSVファイルからN3とN4の当選番号と日付を抽出（リハーサル番号はなし）
    
    Args:
        csv_content: CSVファイルの内容（Shift_JISエンコーディング）
        round_number: 回号
        max_round: 取得する最大回号（Noneの場合は制限なし）
        
    Returns:
        (n3_winning, n4_winning, draw_date) のタプル。見つからない場合はNone
    """
    # 最大回号のチェック
    if max_round and round_number > max_round:
        return None, None, None
    
    try:
        # Shift_JISからUTF-8に変換
        if isinstance(csv_content, bytes):
            csv_text = csv_content.decode('shift_jis', errors='ignore')
        else:
            csv_text = csv_content
        
        # 全角数字を半角に変換
        csv_text = re.sub(r'[０-９]', lambda m: str(ord(m.group(0)) - 0xFEE0), csv_text)
        
        # 行に分割
        lines = csv_text.split('\n')
        # 空行を除去
        lines = [line.strip() for line in lines if line.strip()]
        
        # プレフィックス行（A50など）をスキップ
        skip_prefix = False
        if lines and lines[0].startswith('A5'):
            skip_prefix = True
            lines = lines[1:]
        
        if len(lines) < 11:
            return None, None, None
        
        # ヘッダー行から回号と日付を抽出
        # 形式: 第2701回ナンバーズ,数字選択式全国自治宝くじ,平成21年10月8日,...
        header_line = lines[0] if len(lines) > 0 else ''
        
        date_match = re.search(r'(平成|令和|昭和)(\d+|元)年(\d{1,2})月(\d{1,2})日', header_line)
        draw_date = ''
        if date_match:
            era = date_match.group(1)
            year_str = date_match.group(2)
            month = date_match.group(3).zfill(2)
            day = date_match.group(4).zfill(2)
            
            # 元号を西暦に変換
            if era == '平成':
                year = 1988 + (1 if year_str == '元' else int(year_str))
            elif era == '令和':
                year = 2018 + (1 if year_str == '元' else int(year_str))
            elif era == '昭和':
                year = 1925 + (1 if year_str == '元' else int(year_str))
            else:
                year = None
            
            if year:
                draw_date = f"{year}-{month}-{day}"
        
        # N3の当選番号を抽出
        # 元のCSVファイルの4行目 = プレフィックススキップ後は lines[2]（0-indexedで3行目）
        n3_winning = None
        n3_line_idx = 2 if skip_prefix else 3
        if len(lines) > n3_line_idx:
            n3_line = lines[n3_line_idx]
            n3_parts = n3_line.split(',')
            if len(n3_parts) >= 2 and ('ナンバーズ51' in n3_parts[0] or 'ナンバーズ３' in n3_parts[0]):
                n3_winning = n3_parts[1].strip()
                # 3桁の数字のみを抽出（先頭の0も含む）
                n3_match = re.search(r'(\d{3})', n3_winning)
                if n3_match:
                    n3_winning = n3_match.group(1)
                else:
                    n3_winning = None
        
        # N4の当選番号を抽出
        # 元のCSVファイルの11行目 = プレフィックススキップ後は lines[9]（0-indexedで10行目）
        n4_winning = None
        n4_line_idx = 9 if skip_prefix else 10
        if len(lines) > n4_line_idx:
            n4_line = lines[n4_line_idx]
            n4_parts = n4_line.split(',')
            if len(n4_parts) >= 2 and ('ナンバーズ52' in n4_parts[0] or 'ナンバーズ４' in n4_parts[0]):
                n4_winning = n4_parts[1].strip()
                # 4桁の数字のみを抽出（先頭の0も含む）
                n4_match = re.search(r'(\d{4})', n4_winning)
                if n4_match:
                    n4_winning = n4_match.group(1)
                else:
                    n4_winning = None
        
        return n3_winning, n4_winning, draw_date
        
    except Exception as e:
        return None, None, None



def parse_japanese_date(date_str: str) -> str:
    """
    日本語の日付文字列（平成/令和XX年XX月XX日）をYYYY-MM-DD形式に変換
    
    Args:
        date_str: 日本語の日付文字列
        
    Returns:
        YYYY-MM-DD形式の日付文字列。変換できない場合は空文字列
    """
    if not date_str:
        return ''
        
    match = re.search(r'(平成|令和|昭和)(\d+|元)年(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        era = match.group(1)
        year_str = match.group(2)
        month = match.group(3).zfill(2)
        day = match.group(4).zfill(2)
        
        # 元号を西暦に変換
        if era == '平成':
            year = 1988 + (1 if year_str == '元' else int(year_str))
        elif era == '令和':
            year = 2018 + (1 if year_str == '元' else int(year_str))
        elif era == '昭和':
            year = 1925 + (1 if year_str == '元' else int(year_str))
        else:
            return ''
        
        return f"{year}-{month}-{day}"
    
    # YYYY年MM月DD日形式の場合
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}-{month}-{day}"
        
    return ''


def parse_mizuhobank_table(soup: BeautifulSoup, max_round: Optional[int] = None) -> Tuple[Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
    """
    みずほ銀行のページからN3とN4の当選番号を抽出（リハーサル番号はなし）
    横持ち（通常）と縦持ち（スマホ表示等）の両方に対応
    
    Args:
        soup: BeautifulSoupオブジェクト
        max_round: 取得する最大回号（Noneの場合は制限なし）
        
    Returns:
        (n4_data, n3_data) のタプル
    """
    n4_data = {}
    n3_data = {}
    
    # 表を探す
    tables = soup.find_all('table')
    print(f"   デバッグ: 見つかったテーブル数: {len(tables)}")
    
    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')
        if not rows:
            continue
            
        print(f"   デバッグ: テーブル{table_idx + 1}の行数: {len(rows)}")
        
        # 縦持ちテーブルかどうかの判定
        # 行ヘッダーに「回別」や「抽せん日」が含まれているか確認
        is_vertical = False
        for row in rows[:5]: # 最初の5行を確認
            text = row.get_text()
            if "回別" in text or "抽せん日" in text:
                # セルを確認して、ヘッダーセルがあるか
                cells = row.find_all(['th', 'td'])
                if cells and ("回別" in cells[0].get_text() or "抽せん日" in cells[0].get_text()):
                    is_vertical = True
                    break
        
        if is_vertical:
            print(f"   デバッグ: テーブル{table_idx + 1}は縦持ち形式と判定しました")
            # 縦持ちの場合の処理
            # {列インデックス: {項目名: 値}}
            temp_data = {} 
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                    
                header_text = cells[0].get_text().strip()
                
                for i, cell in enumerate(cells[1:]): # 最初のセルはヘッダー
                    val = cell.get_text().strip()
                    if i not in temp_data:
                        temp_data[i] = {}
                    
                    if "回別" in header_text:
                        # 第1234回 -> 1234
                        match = re.search(r'第(\d+)回', val)
                        if match:
                            temp_data[i]['round'] = int(match.group(1))
                    elif "抽せん日" in header_text:
                        temp_data[i]['date'] = parse_japanese_date(val)
                    elif "抽せん数字" in header_text:
                        temp_data[i]['number'] = val
            
            # temp_dataからn4_data, n3_dataを構築
            for idx, data in temp_data.items():
                if 'round' in data and 'number' in data:
                    r = data['round']
                    if max_round and r > max_round:
                        continue
                        
                    num = data['number']
                    date = data.get('date', '')
                    
                    # 数字のみを抽出（念のため）
                    num_clean = re.sub(r'\D', '', num)
                    
                    if len(num_clean) == 4:
                        n4_data[r] = {'n4_winning': num_clean, 'draw_date': date, 'n4_rehearsal': ''}
                    elif len(num_clean) == 3:
                        n3_data[r] = {'n3_winning': num_clean, 'draw_date': date, 'n3_rehearsal': ''}
            
        else:
            # 横持ち（通常）の場合の処理
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                
                # 回号を含むセルを探す
                row_text = row.get_text()
                round_match = re.search(r'第(\d+)回', row_text)
                if not round_match:
                    continue
                
                round_number = int(round_match.group(1))
                
                # 最大回号のチェック
                if max_round and round_number > max_round:
                    continue
                
                # 抽せん日を探す
                draw_date = parse_japanese_date(row_text)
                
                # N3とN4の当選番号を抽出
                try:
                    n3_winning = ''
                    n4_winning = ''
                    
                    # セルから直接数字を探す
                    cell_texts = [cell.get_text().strip() for cell in cells]
                    
                    for i, cell_text in enumerate(cell_texts):
                        cell_text_clean = re.sub(r'\s+', '', cell_text)
                        
                        # 3桁の数字
                        if len(cell_text_clean) == 3 and cell_text_clean.isdigit() and not n3_winning:
                            # 回号や日付でないことを確認（簡易的）
                            if i >= 1 and "回" not in cell_text and "月" not in cell_text:
                                n3_winning = cell_text_clean
                                continue
                        
                        # 4桁の数字
                        if len(cell_text_clean) == 4 and cell_text_clean.isdigit() and not n4_winning:
                            if i >= 1 and "回" not in cell_text and "月" not in cell_text:
                                n4_winning = cell_text_clean
                                continue
                    
                    # データを保存
                    if n3_winning:
                        n3_data[round_number] = {
                            'n3_winning': n3_winning,
                            'n3_rehearsal': '',
                            'draw_date': draw_date,
                        }
                    
                    if n4_winning:
                        n4_data[round_number] = {
                            'n4_winning': n4_winning,
                            'n4_rehearsal': '',
                            'draw_date': draw_date,
                        }
                        
                except (ValueError, IndexError) as e:
                    continue
    
    return n4_data, n3_data


def find_mizuhobank_pages(target_min_round: Optional[int] = None, target_max_round: Optional[int] = None) -> List[str]:
    """
    みずほ銀行のページ一覧からリンクを取得
    
    Args:
        target_min_round: 取得対象の最小回号（指定された場合、必要な範囲のURLのみ生成）
        target_max_round: 取得対象の最大回号（指定された場合、必要な範囲のURLのみ生成）
    
    Returns:
        見つかったページURLのリスト
    """
    print(f"\n🔍 みずほ銀行のページ一覧を取得中: {MIZUHO_INDEX_URL}...")
    html_content = fetch_page(MIZUHO_INDEX_URL)
    
    if not html_content:
        print("⚠ みずほ銀行のページ一覧の取得に失敗しました")
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    found_pages = []
    
    # 範囲が指定されている場合、必要な範囲のURLのみを生成
    if target_min_round is not None and target_max_round is not None:
        # URL形式が2種類ある：
        # 1. num0001.html形式: 第1回～第2700回（20回ごと）
        # 2. detail.html?fromto=XXXX_YYYY&type=numbers形式: 第2701回～第4800回（20回ごと）
        
        # 第1回～第2700回の範囲が必要な場合
        if target_min_round <= 2700:
            min_range = max(1, target_min_round)
            max_range = min(2700, target_max_round)
            # 20回ごとの開始回号を計算
            start_round = ((min_range - 1) // 20) * 20 + 1
            end_round = ((max_range - 1) // 20) * 20 + 1
            
            for start in range(start_round, end_round + 1, 20):
                if start > max_range:
                    break
                page_num = f"{start:04d}"
                url = urljoin(MIZUHO_BASE_URL, f'num{page_num}.html')
                found_pages.append(url)
        
        # 第2701回～第4800回の範囲が必要な場合
        if target_max_round >= 2701:
            min_range = max(2701, target_min_round)
            max_range = min(4800, target_max_round)
            # 20回ごとの開始回号を計算
            start_round = ((min_range - 1) // 20) * 20 + 1
            end_round = ((max_range - 1) // 20) * 20 + 1
            
            for start in range(start_round, end_round + 1, 20):
                if start > max_range:
                    break
                end = min(start + 19, max_range)
                url = urljoin(MIZUHO_BASE_URL, f'detail.html?fromto={start}_{end}&type=numbers')
                found_pages.append(url)
        
        print(f"   範囲指定: 第{target_min_round}回 ～ 第{target_max_round}回")
        print(f"   ✓ {len(found_pages)}件のURLを生成しました")
        if found_pages:
            print(f"   最初の3件: {found_pages[:3]}")
            if len(found_pages) > 3:
                print(f"   最後の3件: {found_pages[-3:]}")
        
        return found_pages
    
    # 範囲が指定されていない場合、既存のロジックで全範囲のURLを生成
    # （B表）A表以前の当せん番号の範囲のリンクを探す
    # リンクを探す（numXXXX.html または detail.html?fromto=... のパターン）
    links = soup.find_all('a', href=True)
    
    print(f"   デバッグ: 見つかったリンク数: {len(links)}")
    
    # デバッグ: リンクの一部を表示（backnumber関連のもの）
    debug_count = 0
    backnumber_related = []
    for link in links:
        href = link.get('href', '')
        text = link.get_text().strip()
        
        # backnumber関連のリンクを探す
        if 'backnumber' in href.lower() or 'num' in href.lower() or 'detail' in href.lower():
            backnumber_related.append((href, text))
            debug_count += 1
            if debug_count <= 10:
                print(f"   デバッグ: バックナンバー関連リンク [{debug_count}]: {href[:100]} (テキスト: {text[:30]})")
    
    print(f"   デバッグ: バックナンバー関連リンク数: {len(backnumber_related)}")
    
    # 実際のリンクが見つからない場合は、直接URLを生成する
    # num0001.html, num0021.html, ... のパターンで生成
    # または detail.html?fromto=XXXX_YYYY&type=numbers のパターンで生成
    
    # まず、直接リンクを探す
    for link in links:
        href = link.get('href', '')
        # num0001.html のようなパターン
        if re.search(r'num\d+\.html', href):
            if href.startswith('/'):
                full_url = f"https://www.mizuhobank.co.jp{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(MIZUHO_BASE_URL, href)
            
            if full_url not in found_pages:
                found_pages.append(full_url)
        
        # detail.html?fromto=... のパターン
        elif 'detail.html' in href and 'fromto=' in href:
            if href.startswith('/'):
                full_url = f"https://www.mizuhobank.co.jp{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(MIZUHO_BASE_URL, href)
            
            if full_url not in found_pages:
                found_pages.append(full_url)
    
    # もしリンクが見つからない場合は、テーブル内のリンクも探す
    if not found_pages:
        print("   デバッグ: テーブル内のリンクを検索中...")
        tables = soup.find_all('table')
        print(f"   デバッグ: 見つかったテーブル数: {len(tables)}")
        
        for table in tables:
            table_links = table.find_all('a', href=True)
            print(f"   デバッグ: テーブル内のリンク数: {len(table_links)}")
            for link in table_links[:10]:  # 最初の10件を表示
                href = link.get('href', '')
                text = link.get_text().strip()
                print(f"   デバッグ: テーブル内リンク: {href[:100]} (テキスト: {text[:30]})")
                
                # numXXXX.html または detail.html を含むリンクを探す
                if re.search(r'num\d+\.html', href) or ('detail.html' in href and 'fromto=' in href):
                    if href.startswith('/'):
                        full_url = f"https://www.mizuhobank.co.jp{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(MIZUHO_BASE_URL, href)
                    
                    if full_url not in found_pages:
                        found_pages.append(full_url)
                        print(f"   デバッグ: テーブル内で発見: {href[:100]}")
    
    # それでもリンクが見つからない場合は、直接URLを生成
    if not found_pages:
        print("   デバッグ: リンクが見つからないため、直接URLを生成します")
        
        # URL形式が2種類ある：
        # 1. num0001.html形式: 第1回～第2700回（20回ごと）
        # 2. detail.html?fromto=XXXX_YYYY&type=numbers形式: 第2701回～第4800回（20回ごと）
        
        # 第1回～第2700回: num0001.html形式
        for start_round in range(1, 2701, 20):
            page_num = f"{start_round:04d}"
            url = urljoin(MIZUHO_BASE_URL, f'num{page_num}.html')
            found_pages.append(url)
        
        print(f"   デバッグ: numXXXX.html形式を{len(found_pages)}件生成しました")
        
        # 第2701回～第4800回: detail.html?fromto=XXXX_YYYY&type=numbers形式
        detail_url_count = 0
        for start_round in range(2701, 4801, 20):
            end_round = min(start_round + 19, 4800)
            url = urljoin(MIZUHO_BASE_URL, f'detail.html?fromto={start_round}_{end_round}&type=numbers')
            found_pages.append(url)
            detail_url_count += 1
        
        print(f"   デバッグ: detail.html形式を{detail_url_count}件生成しました（合計{len(found_pages)}件）")
        
        # 最初の数件をテスト
        if found_pages:
            test_url = found_pages[0]
            print(f"   デバッグ: テストURL: {test_url}")
            test_content = fetch_page(test_url)
            if test_content:
                print(f"   ✓ テストURLにアクセス成功 ({len(test_content)}文字)")
            else:
                print(f"   ✗ テストURLにアクセス失敗")
        
        # 2701回以降のURLもテスト
        if len(found_pages) > 135:  # num0001.html形式が135件ある場合
            test_url2 = found_pages[135]  # 最初のdetail.html形式
            print(f"   デバッグ: テストURL2 (detail.html形式): {test_url2}")
            test_content2 = fetch_page(test_url2)
            if test_content2:
                print(f"   ✓ テストURL2にアクセス成功 ({len(test_content2)}文字)")
            else:
                print(f"   ✗ テストURL2にアクセス失敗")
    
    print(f"✓ {len(found_pages)}件のページを発見しました")
    if found_pages:
        print(f"   最初の5件: {found_pages[:5]}")
    
    return found_pages


def parse_n4_table(soup: BeautifulSoup, latest_only: bool = False) -> Dict[int, Dict[str, str]]:
    """
    N4の表データを抽出（4桁）
    
    Args:
        soup: BeautifulSoupオブジェクト
        latest_only: Trueの場合、最新の1行のみを取得
        
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
                        # 特殊表記に対応した数値抽出
                        digit = extract_number_from_cell(cell_text)
                        if digit:
                            n4_rehearsal_digits.append(digit)
                
                if len(n4_rehearsal_digits) != 4:
                    continue
                
                n4_rehearsal = ''.join(n4_rehearsal_digits)
                
                # 当選番号（4桁）
                n4_winning_digits = []
                for i in range(6, 10):  # 6-9番目のセル
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        # 特殊表記に対応した数値抽出
                        digit = extract_number_from_cell(cell_text)
                        if digit:
                            n4_winning_digits.append(digit)
                
                if len(n4_winning_digits) != 4:
                    continue
                
                n4_winning = ''.join(n4_winning_digits)
                
                results[round_number] = {
                    'n4_winning': n4_winning,
                    'n4_rehearsal': n4_rehearsal,
                }
                
                # 最新のみ取得の場合、最初の有効な行で終了
                if latest_only:
                    return results
                    
            except (ValueError, IndexError) as e:
                continue
    
    return results


def parse_n3_table(soup: BeautifulSoup, latest_only: bool = False) -> Dict[int, Dict[str, str]]:
    """
    N3の表データを抽出（3桁）
    
    Args:
        soup: BeautifulSoupオブジェクト
        latest_only: Trueの場合、最新の1行のみを取得
        
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
                        # 特殊表記に対応した数値抽出
                        digit = extract_number_from_cell(cell_text)
                        if digit:
                            n3_rehearsal_digits.append(digit)
                
                if len(n3_rehearsal_digits) != 3:
                    continue
                
                n3_rehearsal = ''.join(n3_rehearsal_digits)
                
                # 当選番号（3桁）
                n3_winning_digits = []
                for i in range(5, 8):  # 5-7番目のセル
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        # 特殊表記に対応した数値抽出
                        digit = extract_number_from_cell(cell_text)
                        if digit:
                            n3_winning_digits.append(digit)
                
                if len(n3_winning_digits) != 3:
                    continue
                
                n3_winning = ''.join(n3_winning_digits)
                
                results[round_number] = {
                    'n3_winning': n3_winning,
                    'n3_rehearsal': n3_rehearsal,
                }
                
                # 最新のみ取得の場合、最初の有効な行で終了
                if latest_only:
                    return results
                    
            except (ValueError, IndexError) as e:
                continue
    
    return results


def combine_data(n4_data: Dict[int, Dict[str, str]], n3_data: Dict[int, Dict[str, str]], latest_round: int, max_rounds: int = 300, merge_mode: bool = False) -> List[Dict[str, str]]:
    """
    N4とN3のデータを結合
    
    Args:
        n4_data: N4のデータ辞書
        n3_data: N3のデータ辞書
        latest_round: 最新の回号
        max_rounds: 取得する最大件数
        merge_mode: マージモードの場合、取得したデータをそのまま使用
        
    Returns:
        結合したデータのリスト
    """
    results = []
    
    # 取得したデータの回号と一致するものを使用
    available_rounds = set(n4_data.keys()) | set(n3_data.keys())
    
    if not available_rounds:
        return results
    
    # マージモードの場合は、取得したデータをそのまま使用
    if merge_mode:
        target_rounds = available_rounds
        print(f"   マージモード: 取得したデータをそのまま使用（{len(target_rounds)}件）")
    else:
        # 最新回から指定件数分の回号を生成
        target_rounds = set(range(latest_round - max_rounds + 1, latest_round + 1))
        target_rounds = target_rounds & available_rounds
        
        # デバッグ情報
        min_round = min(available_rounds)
        max_round = max(available_rounds)
        print(f"   取得データ範囲: 第{min_round}回 ～ 第{max_round}回（{len(available_rounds)}件）")
        print(f"   目標範囲: 第{min(target_rounds) if target_rounds else 'N/A'}回 ～ 第{max(target_rounds) if target_rounds else 'N/A'}回（{len(target_rounds)}件）")
    
    print(f"   一致するデータ: {len(target_rounds)}件")
    
    # N4データがない回号を確認
    missing_n4 = [r for r in target_rounds if r not in n4_data.keys()]
    if missing_n4:
        print(f"   N4データがない回号: {sorted(missing_n4)[:10]}...（{len(missing_n4)}件）")
    
    # 日付を計算するためのベース（最新回から逆算）
    # ナンバーズは平日のみ抽選があるため、単純な日数差ではなく平日をカウントする必要がある
    # マージモードの場合は、取得したデータの最大回号を使用
    if merge_mode and available_rounds:
        latest_round = max(available_rounds)
        # 最新回の日付を基準にする（既存CSVから取得、または今日の日付から逆算）
        # 既存CSVから最新回の日付を取得できる場合はそれを使用
        base_date = datetime.now()
    else:
        # 通常モードの場合も、最新回の日付を基準にする
        base_date = datetime.now()
    
    for round_number in sorted(target_rounds, reverse=True):
        # N4データを取得
        n4_info = n4_data.get(round_number, {})
        n4_winning = n4_info.get('n4_winning', '')
        n4_rehearsal = n4_info.get('n4_rehearsal', '')
        
        # N3データを取得
        n3_info = n3_data.get(round_number, {})
        n3_winning = n3_info.get('n3_winning', '')
        n3_rehearsal = n3_info.get('n3_rehearsal', '')
        
        # 日付を取得（みずほ銀行のデータから取得した日付を優先）
        draw_date = ''
        if n4_info.get('draw_date'):
            draw_date = n4_info.get('draw_date')
        elif n3_info.get('draw_date'):
            draw_date = n3_info.get('draw_date')
        
        # N4またはN3のデータがなければスキップ（マージモードの場合はN3データのみでもOK）
        if not n4_winning and not n3_winning:
            continue
        
        # マージモードの場合は、N4データがなくてもN3データがあれば保存
        if merge_mode and not n4_winning and n3_winning:
            # N3データのみの場合、N4データは空文字列で保存
            n4_winning = ''
            n4_rehearsal = ''
        elif not merge_mode and not n4_winning:
            # 通常モードの場合はN4データ必須
            continue
        
        # 日付が取得できていない場合のみ、推定値を計算
        if not draw_date:
            # 日付を計算（最新回から逆算、平日のみを考慮）
            # ナンバーズは平日のみ抽選があるため、平日のみをカウント
            round_diff = latest_round - round_number
            draw_date_obj = base_date
            weekday_count = 0
            
            # 最新回から逆算して、平日のみをカウント
            while weekday_count < round_diff:
                draw_date_obj = draw_date_obj - timedelta(days=1)
                # 平日かどうかを確認（月曜=0, 金曜=4）
                if draw_date_obj.weekday() < 5:
                    # 年末年始を除外
                    month = draw_date_obj.month
                    day = draw_date_obj.day
                    if not ((month == 12 and day >= 29) or (month == 1 and day <= 3)):
                        weekday_count += 1
            
            draw_date = draw_date_obj.strftime('%Y-%m-%d')
        
        # weekdayを計算
        weekday = calculate_weekday(draw_date)
        weekday_str = str(weekday) if weekday is not None else 'NULL'
        
        results.append({
            'round_number': round_number,
            'draw_date': draw_date,
            'weekday': weekday_str,
            'n3_winning': n3_winning if n3_winning else '',
            'n4_winning': n4_winning,
            'n3_rehearsal': n3_rehearsal if n3_rehearsal else '',
            'n4_rehearsal': n4_rehearsal if n4_rehearsal else '',
        })
    
    return results


def find_missing_rounds(output_file: Path) -> List[int]:
    """
    既存CSVファイルから欠番の回号を検出する
    
    Args:
        output_file: CSVファイルパス
        
    Returns:
        欠番の回号のリスト
    """
    if not output_file.exists():
        return []
    
    existing_data = load_existing_csv(output_file)
    if not existing_data:
        return []
    
    # 既存の回号を取得
    existing_rounds = set()
    for row in existing_data:
        try:
            round_num = int(row.get('round_number', 0))
            if round_num > 0:
                existing_rounds.add(round_num)
        except (ValueError, TypeError):
            continue
    
    if not existing_rounds:
        return []
    
    # 最小回号と最大回号を取得
    min_round = min(existing_rounds)
    max_round = max(existing_rounds)
    
    # 欠番を検出
    missing_rounds = []
    for round_num in range(min_round, max_round + 1):
        if round_num not in existing_rounds:
            missing_rounds.append(round_num)
    
    return sorted(missing_rounds)


def get_existing_round_range(output_file: Path) -> Tuple[Optional[int], Optional[int]]:
    """
    既存CSVファイルから最小回号と最大回号を取得する
    
    Args:
        output_file: CSVファイルパス
        
    Returns:
        (最小回号, 最大回号)のタプル。CSVが存在しない場合は(None, None)
    """
    if not output_file.exists():
        return None, None
    
    existing_data = load_existing_csv(output_file)
    if not existing_data:
        return None, None
    
    round_numbers = []
    for row in existing_data:
        try:
            round_num = int(row.get('round_number', 0))
            if round_num > 0:
                round_numbers.append(round_num)
        except (ValueError, TypeError):
            continue
    
    if not round_numbers:
        return None, None
    
    return min(round_numbers), max(round_numbers)


def load_existing_csv(output_file: Path) -> List[Dict[str, str]]:
    """
    既存のCSVファイルを読み込む
    
    Args:
        output_file: CSVファイルパス
        
    Returns:
        読み込んだデータのリスト
    """
    if not output_file.exists():
        return []
    
    data = []
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # NULL値を空文字列に変換
                cleaned_row = {}
                for key, value in row.items():
                    cleaned_row[key] = '' if value == 'NULL' else value
                data.append(cleaned_row)
    except Exception as e:
        print(f"⚠ 既存CSVファイルの読み込みエラー: {e}")
        return []
    
    return data


def save_to_csv(data: List[Dict[str, str]], output_file: Path, merge: bool = False, update_null: bool = False):
    """
    CSVファイルに保存
    
    Args:
        data: 保存するデータのリスト
        output_file: 出力ファイルパス
        merge: Trueの場合、既存のCSVファイルとマージする
        update_null: Trueの場合、既存データのNULL値を新しいデータで更新する
    """
    # ディレクトリを作成
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'round_number',
        'draw_date',
        'weekday',
        'n3_winning',
        'n4_winning',
        'n3_rehearsal',
        'n4_rehearsal'
    ]
    
    # 既存CSVファイルがある場合、weekdayカラムが存在するか確認
    has_weekday_column = False
    existing_data = None
    if merge and output_file.exists():
        existing_data = load_existing_csv(output_file)
        if existing_data and 'weekday' in existing_data[0]:
            has_weekday_column = True
    
    # マージモードの場合、既存データを読み込む
    if merge and output_file.exists() and existing_data:
        # 回号をキーとして既存データを辞書化
        existing_dict = {int(row['round_number']): row for row in existing_data}
        
        # 既存データにweekdayカラムがない場合、draw_dateから計算
        if not has_weekday_column:
            for round_num, existing_row in existing_dict.items():
                draw_date_val = existing_row.get('draw_date', '')
                if draw_date_val and draw_date_val != 'NULL':
                    weekday = calculate_weekday(draw_date_val)
                    existing_row['weekday'] = str(weekday) if weekday is not None else 'NULL'
        
        # 新しいデータで既存データを更新または追加
        for row in data:
            round_num = int(row['round_number'])
            if round_num in existing_dict:
                # 既存データがある場合
                if update_null:
                    # NULL値更新モード: 既存データのNULL/空のフィールドを新しいデータで更新
                    existing_row = existing_dict[round_num]
                    for key in fieldnames:
                        existing_value = existing_row.get(key, '')
                        new_value = row.get(key, '')
                        # 既存値がNULLまたは空の場合、新しい値で更新
                        if not existing_value or existing_value == 'NULL':
                            if new_value:
                                existing_row[key] = new_value
                        # 既存値がある場合も、新しい値が空でなければ更新
                        elif new_value:
                            existing_row[key] = new_value
                    # weekdayが更新された場合、再計算
                    if 'weekday' in fieldnames:
                        draw_date_val = existing_row.get('draw_date', '')
                        if draw_date_val and draw_date_val != 'NULL':
                            weekday = calculate_weekday(draw_date_val)
                            existing_row['weekday'] = str(weekday) if weekday is not None else 'NULL'
                    existing_dict[round_num] = existing_row
                else:
                    # 通常のマージモード: 新しいデータで完全に置き換え
                    existing_dict[round_num] = row
            else:
                # 新しい回号の場合、追加
                existing_dict[round_num] = row
        
        # 回号順にソート
        data = [existing_dict[round_num] for round_num in sorted(existing_dict.keys(), reverse=True)]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            # NULL値の処理（空文字列をNULLに変換）
            csv_row = {}
            for key in fieldnames:
                value = row.get(key, '')
                # weekdayカラムが存在しない場合、draw_dateから計算
                if key == 'weekday' and not value:
                    draw_date_val = row.get('draw_date', '')
                    if draw_date_val and draw_date_val != 'NULL':
                        weekday = calculate_weekday(draw_date_val)
                        value = str(weekday) if weekday is not None else 'NULL'
                csv_row[key] = value if value else 'NULL'
            
            writer.writerow(csv_row)
    
    print(f"✓ CSVファイルを保存しました: {output_file}")
    print(f"  データ件数: {len(data)}件")


def fetch_multiple_pages(
    base_url: str, 
    max_rounds: int, 
    latest_round: Optional[int] = None,
    target_min_round: Optional[int] = None,
    target_max_round: Optional[int] = None,
    output_file: Optional[Path] = None,
    save_interval: int = 100  # 100件ごとにCSVに保存
) -> tuple[Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
    """
    複数のページからデータを取得
    
    Args:
        base_url: ベースURL
        max_rounds: 取得する最大件数
        latest_round: 最新の回号（Noneの場合は自動取得）
        target_min_round: 取得対象の最小回号（指定された場合のみ）
        target_max_round: 取得対象の最大回号（指定された場合のみ）
        output_file: CSVファイルパス（指定された場合、save_interval件ごとに保存）
        save_interval: CSVに保存する間隔（件数）
        
    Returns:
        (n4_data, n3_data) のタプル
    """
    n4_data = {}
    n3_data = {}
    last_save_count = 0
    consecutive_errors = 0  # 連続エラーカウンター
    max_consecutive_errors = 5  # 最大連続エラー数
    
    # 取得範囲を決定
    if target_min_round is not None and target_max_round is not None:
        # 指定された範囲を使用
        target_min = target_min_round
        target_max = target_max_round
        print(f"   取得対象範囲: 第{target_min}回 ～ 第{target_max}回")
    else:
        # 最新回号を取得
        if latest_round is None:
            latest_round = get_latest_round_number()
            if latest_round is None:
                print("⚠ 最新回号が取得できませんでした")
                return n4_data, n3_data
        
        # 最新回から指定件数分を取得
        target_min = latest_round - max_rounds + 1
        target_max = latest_round
    
    # 4800回以前のデータが必要な場合は、みずほ銀行のページから取得
    if target_max <= REHEARSAL_AVAILABLE_FROM - 1:
        print(f"   みずほ銀行のページから取得します（第{target_min}回 ～ 第{target_max}回）")
        mizuhobank_pages = find_mizuhobank_pages(target_min_round=target_min, target_max_round=target_max)
        
        for page_url in mizuhobank_pages:
            print(f"\n📥 みずほ銀行のページを取得中: {page_url}...")
            html_content = fetch_page(page_url)
            
            if not html_content:
                # 404エラーの場合、そのページをスキップして続行
                print(f"   ⚠ ページをスキップしました: {page_url}")
                consecutive_errors += 1
                
                # 5回連続でエラーが発生した場合、それまでのデータを保存して終了
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\n⚠ {max_consecutive_errors}回連続でエラーが発生したため、処理を終了します")
                    if output_file and (n4_data or n3_data):
                        print(f"\n💾 取得済みデータをCSVに保存します...")
                        all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                        if all_rounds:
                            all_rounds_list = sorted(all_rounds, reverse=True)
                            latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                            temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                            save_to_csv(temp_data, output_file, merge=True)
                            print(f"✓ {len(temp_data)}件のデータを保存しました")
                    return n4_data, n3_data
                
                continue
            
            # エラーが発生しなかった場合、カウンターをリセット
            consecutive_errors = 0
            
            print(f"✓ ページを取得しました ({len(html_content)}文字)")
            
            # HTMLをパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # みずほ銀行のページからデータを抽出
            page_n4_data, page_n3_data = parse_mizuhobank_table(soup, max_round=target_max)
            
            # 取得対象範囲内のデータのみを追加
            filtered_n4_data = {
                round_num: data for round_num, data in page_n4_data.items()
                if target_min <= round_num <= target_max
            }
            n4_data.update(filtered_n4_data)
            print(f"✓ {len(filtered_n4_data)}件のN4データを抽出しました（累計: {len(n4_data)}件）")
            
            filtered_n3_data = {
                round_num: data for round_num, data in page_n3_data.items()
                if target_min <= round_num <= target_max
            }
            n3_data.update(filtered_n3_data)
            print(f"✓ {len(filtered_n3_data)}件のN3データを抽出しました（累計: {len(n3_data)}件）")
            
            # 100件ごとにCSVに保存
            if output_file:
                all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                current_count = len([r for r in all_rounds if target_min <= r <= target_max])
                
                if current_count - last_save_count >= save_interval:
                    print(f"\n💾 中間保存: {current_count}件のデータをCSVに保存します...")
                    # データを結合
                    all_rounds_list = sorted(all_rounds, reverse=True)
                    latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                    
                    temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                    save_to_csv(temp_data, output_file, merge=True)
                    last_save_count = current_count
                    print(f"✓ 中間保存完了（{current_count}件）\n")
            
            # 必要な件数に達したか確認（N4とN3の両方を考慮）
            target_rounds_in_data = set()
            for r in n4_data.keys():
                if target_min <= r <= target_max:
                    target_rounds_in_data.add(r)
            for r in n3_data.keys():
                if target_min <= r <= target_max:
                    target_rounds_in_data.add(r)
            
            # 目標範囲内の最小回号が取得できたか確認
            if target_rounds_in_data:
                min_fetched = min(target_rounds_in_data)
                if min_fetched <= target_min and len(target_rounds_in_data) >= max_rounds:
                    print(f"\n✓ 目標範囲内のデータが十分に取得できました（{len(target_rounds_in_data)}件 >= {max_rounds}件、最小回号: 第{min_fetched}回）")
                    break
            
            # 次のページに進む前に少し待機
            time.sleep(1)
        
        # 最後に、残りのデータを保存（中間保存で保存されていない場合）
        if output_file and (n4_data or n3_data):
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            current_count = len([r for r in all_rounds if target_min <= r <= target_max])
            
            # 最後に保存されていないデータがある場合、最終保存を実行
            if current_count > last_save_count:
                print(f"\n💾 最終保存: {current_count}件のデータをCSVに保存します...")
                all_rounds_list = sorted(all_rounds, reverse=True)
                latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                
                temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                save_to_csv(temp_data, output_file, merge=True)
                print(f"✓ 最終保存完了（{current_count}件）\n")
        
        return n4_data, n3_data
    
    # 4801回以降のデータは、既存の方法（hpfree.com）を使用
    # 4800回以前のデータも含む場合は、両方から取得
    needs_mizuhobank = target_min <= REHEARSAL_AVAILABLE_FROM - 1
    needs_hpfree = target_max >= REHEARSAL_AVAILABLE_FROM
    
    if needs_mizuhobank:
        # まず4800回以前をみずほ銀行から取得
        print(f"   みずほ銀行のページから取得します（第{target_min}回 ～ 第{REHEARSAL_AVAILABLE_FROM - 1}回）")
        mizuhobank_pages = find_mizuhobank_pages(target_min_round=target_min, target_max_round=REHEARSAL_AVAILABLE_FROM - 1)
        
        for page_url in mizuhobank_pages:
            html_content = fetch_page(page_url)
            if not html_content:
                # 404エラーの場合、そのページをスキップして続行
                consecutive_errors += 1
                
                # 5回連続でエラーが発生した場合、それまでのデータを保存して終了
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\n⚠ {max_consecutive_errors}回連続でエラーが発生したため、処理を終了します")
                    if output_file and (n4_data or n3_data):
                        print(f"\n💾 取得済みデータをCSVに保存します...")
                        all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                        if all_rounds:
                            all_rounds_list = sorted(all_rounds, reverse=True)
                            latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                            temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                            save_to_csv(temp_data, output_file, merge=True)
                            print(f"✓ {len(temp_data)}件のデータを保存しました")
                    return n4_data, n3_data
                
                continue
            
            # エラーが発生しなかった場合、カウンターをリセット
            consecutive_errors = 0
            
            soup = BeautifulSoup(html_content, 'html.parser')
            page_n4_data, page_n3_data = parse_mizuhobank_table(soup, max_round=REHEARSAL_AVAILABLE_FROM - 1)
            
            filtered_n4_data = {
                round_num: data for round_num, data in page_n4_data.items()
                if target_min <= round_num <= REHEARSAL_AVAILABLE_FROM - 1
            }
            n4_data.update(filtered_n4_data)
            
            filtered_n3_data = {
                round_num: data for round_num, data in page_n3_data.items()
                if target_min <= round_num <= REHEARSAL_AVAILABLE_FROM - 1
            }
            n3_data.update(filtered_n3_data)
            
            time.sleep(1)
        
        # 4801回以降の取得範囲を更新
        target_min = REHEARSAL_AVAILABLE_FROM
    
    # hpfree.comから取得（4801回以降）
    if needs_hpfree:
        # 過去分のページを自動探索
        past_pages = find_past_pages(base_url)
        
        # 最新版ページも追加
        all_pages = [LATEST_PAGE_URL] + past_pages
        
        # 必要な件数に達するまで順次取得
        for page_url in all_pages:
            print(f"\n📥 ページを取得中: {page_url}...")
            html_content = fetch_page(page_url)
            
            if not html_content:
                print(f"⚠ ページの取得に失敗しました: {page_url}")
                consecutive_errors += 1
                
                # 5回連続でエラーが発生した場合、それまでのデータを保存して終了
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\n⚠ {max_consecutive_errors}回連続でエラーが発生したため、処理を終了します")
                    if output_file and (n4_data or n3_data):
                        print(f"\n💾 取得済みデータをCSVに保存します...")
                        all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                        if all_rounds:
                            all_rounds_list = sorted(all_rounds, reverse=True)
                            latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                            temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                            save_to_csv(temp_data, output_file, merge=True)
                            print(f"✓ {len(temp_data)}件のデータを保存しました")
                    return n4_data, n3_data
                
                continue
            
            # エラーが発生しなかった場合、カウンターをリセット
            consecutive_errors = 0
            
            print(f"✓ ページを取得しました ({len(html_content)}文字)")
            
            # HTMLをパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # N4データを抽出
            page_n4_data = parse_n4_table(soup)
            # 取得対象範囲内のデータのみを追加
            filtered_n4_data = {
                round_num: data for round_num, data in page_n4_data.items()
                if target_min <= round_num <= target_max
            }
            n4_data.update(filtered_n4_data)
            print(f"✓ {len(filtered_n4_data)}件のN4データを抽出しました（累計: {len(n4_data)}件）")
            
            # N3データを抽出
            page_n3_data = parse_n3_table(soup)
            # 取得対象範囲内のデータのみを追加
            filtered_n3_data = {
                round_num: data for round_num, data in page_n3_data.items()
                if target_min <= round_num <= target_max
            }
            n3_data.update(filtered_n3_data)
            print(f"✓ {len(filtered_n3_data)}件のN3データを抽出しました（累計: {len(n3_data)}件）")
            
            # 必要な件数に達したか確認（N4とN3の両方を考慮）
            target_rounds_in_data = set()
            for r in n4_data.keys():
                if target_min <= r <= target_max:
                    target_rounds_in_data.add(r)
            for r in n3_data.keys():
                if target_min <= r <= target_max:
                    target_rounds_in_data.add(r)
            
            # 目標範囲内の最小回号が取得できたか確認
            if target_rounds_in_data:
                min_fetched = min(target_rounds_in_data)
                if min_fetched <= target_min and len(target_rounds_in_data) >= max_rounds:
                    print(f"\n✓ 目標範囲内のデータが十分に取得できました（{len(target_rounds_in_data)}件 >= {max_rounds}件、最小回号: 第{min_fetched}回）")
                    break
            
            # 100件ごとにCSVに保存
            if output_file:
                all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                current_count = len([r for r in all_rounds if target_min <= r <= target_max])
                
                if current_count - last_save_count >= save_interval:
                    print(f"\n💾 中間保存: {current_count}件のデータをCSVに保存します...")
                    # データを結合
                    all_rounds_list = sorted(all_rounds, reverse=True)
                    latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                    
                    temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                    save_to_csv(temp_data, output_file, merge=True)
                    last_save_count = current_count
                    print(f"✓ 中間保存完了（{current_count}件）\n")
            
            # 次のページに進む前に少し待機
            time.sleep(1)
        
        # 最後に、残りのデータを保存（中間保存で保存されていない場合）
        if output_file and (n4_data or n3_data):
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            current_count = len([r for r in all_rounds if target_min <= r <= target_max])
            
            # 最後に保存されていないデータがある場合、最終保存を実行
            if current_count > last_save_count:
                print(f"\n💾 最終保存: {current_count}件のデータをCSVに保存します...")
                all_rounds_list = sorted(all_rounds, reverse=True)
                latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                
                temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                save_to_csv(temp_data, output_file, merge=True)
                print(f"✓ 最終保存完了（{current_count}件）\n")
    
    return n4_data, n3_data


def main():
    if not HAS_DEPS:
        sys.exit(1)
    
    # 引数解析
    # プロジェクトルートを取得（scripts/production/から3階層上がプロジェクトルート）
    project_root = Path(__file__).parent.parent.parent
    output_file = project_root / 'data' / 'past_results.csv'
    max_rounds = 300
    merge_mode = False  # マージモード（自動実行時のみ）
    fill_gaps_mode = False  # 欠番を埋めるモード
    update_null_mode = False  # NULL値を更新するモード
    target_min_round = None  # 取得対象の最小回号
    target_max_round = None  # 取得対象の最大回号
    
    # 引数を解析（順序に関係なく動作するように）
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg == '--limit' and i + 1 < len(args):
            try:
                max_rounds = int(args[i + 1])
                i += 2
            except ValueError:
                i += 1
        elif arg == '--merge':
            merge_mode = True
            # --merge の後に数字が続く場合（古い形式の互換性）
            if i + 1 < len(args) and args[i + 1].isdigit():
                max_rounds = int(args[i + 1])
                i += 2
            else:
                # マージモードのデフォルトは1件
                if max_rounds == 300:
                    max_rounds = 1
                i += 1
        elif arg == '--fill-gaps':
            fill_gaps_mode = True
            merge_mode = True  # 欠番を埋める場合はマージモード
            i += 1
        elif arg == '--update-null':
            update_null_mode = True
            merge_mode = True  # NULL値を更新する場合はマージモード
            i += 1
        elif arg == '--from-round' and i + 1 < len(args):
            try:
                target_min_round = int(args[i + 1])
                merge_mode = True  # 範囲指定時はマージモード
                i += 2
            except ValueError:
                i += 1
        elif arg == '--to-round' and i + 1 < len(args):
            try:
                target_max_round = int(args[i + 1])
                merge_mode = True  # 範囲指定時はマージモード
                i += 2
            except ValueError:
                i += 1
        elif arg == '--help' or arg == '-h':
            print("使い方:")
            print("  python3 fetch_past_results.py [output_file] [--limit N] [--use-fallback] [--merge]")
            print("")
            print("オプション:")
            print("  output_file     出力ファイルパス（デフォルト: data/past_results.csv）")
            print("  --limit N       取得する最大件数（デフォルト: 300）")
            print("  --merge         既存CSVファイルとマージ（--limit Nで大量取得も可能）")
            print("  --fill-gaps     欠番の回号を検出して取得してマージ")
            print("  --update-null   既存データのNULL値を新しいデータで更新")
            print("  --from-round N  取得対象の最小回号を指定")
            print("  --to-round N    取得対象の最大回号を指定")
            print("  --use-fallback  Webスクレイピング失敗時に検索APIを使用")
            print("")
            print("例:")
            print("  python3 fetch_past_results.py")
            print("  python3 fetch_past_results.py --limit 1000")
            print("  python3 fetch_past_results.py --merge  # 最新の1回分のみ追加")
            print("  python3 fetch_past_results.py --merge --limit 1000  # 既存CSVの最古回号より前の1000件を取得してマージ")
            print("  python3 fetch_past_results.py --fill-gaps  # 欠番の回号を検出して取得してマージ")
            print("  python3 fetch_past_results.py --update-null  # 既存データのNULL値を更新")
            print("  python3 fetch_past_results.py --from-round 1 --to-round 4800  # 第1回～第4800回を取得")
            print("  python3 fetch_past_results.py --limit 1000 --merge  # 同じ意味")
            sys.exit(0)
        elif not arg.startswith('--'):
            output_file = Path(arg)
            i += 1
        else:
            i += 1
    
    # 最新回号を取得
    print("=" * 80)
    print("ナンバーズ過去当選番号・リハーサル番号取得スクリプト")
    print("=" * 80)
    
    # 表示メッセージを更新
    if fill_gaps_mode:
        print(f"\nモード: 欠番を埋める（既存CSVの欠番を検出して取得）")
    elif update_null_mode:
        print(f"\nモード: NULL値を更新（既存データのNULL値を新しいデータで更新）")
    elif merge_mode:
        if max_rounds == 1:
            print(f"\nモード: マージ（最新の1回分のみ追加）")
        else:
            min_existing_round, max_existing_round = get_existing_round_range(output_file)
            if min_existing_round is not None:
                print(f"\nモード: マージ（既存CSVの最古回号より前の{max_rounds}件を追加）")
            else:
                print(f"\nモード: マージ（最新回から{max_rounds}件を追加）")
    else:
        print(f"\nモード: 上書き（最新回から{max_rounds}件を取得、既存CSVは上書き）")
    
    print(f"出力先: {output_file}\n")
    
    latest_round = get_latest_round_number()
    if latest_round is None:
        print("⚠ 最新回号が取得できませんでした")
        sys.exit(1)
    
    print(f"最新回号: 第{latest_round}回")
    
    # ベースURL
    base_url = BASE_PAGE_URL
    
    # 既存CSVの回号範囲を取得
    min_existing_round, max_existing_round = get_existing_round_range(output_file)
    
    # 範囲指定モードの処理
    if target_min_round is not None or target_max_round is not None:
        # 範囲が指定されている場合
        if target_min_round is None:
            target_min_round = 1  # デフォルトは第1回から
        if target_max_round is None:
            target_max_round = latest_round  # デフォルトは最新回まで
        
        print(f"\nモード: 範囲指定（第{target_min_round}回 ～ 第{target_max_round}回）")
        print(f"📥 指定範囲のデータを取得します（第{target_min_round}回 ～ 第{target_max_round}回）...")
        
        # 指定範囲のデータを取得
        n4_data, n3_data = fetch_multiple_pages(
            base_url,
            target_max_round - target_min_round + 1,  # 範囲内の全件数
            latest_round=None,
            target_min_round=target_min_round,
            target_max_round=target_max_round,
            output_file=output_file  # 100件ごとにCSVに保存
        )
        
        print(f"✓ 範囲指定のデータを取得: N4={len(n4_data)}件、N3={len(n3_data)}件")
        
        if not n4_data and not n3_data:
            print("⚠ 指定範囲のデータが取得できませんでした")
            sys.exit(1)
        
        # 取得したデータの範囲を使用
        if n4_data or n3_data:
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            if all_rounds:
                latest_round = max(all_rounds)
        
        # 範囲指定モードの場合、fetch_multiple_pages内で既に中間保存が行われているため、
        # 最後の保存はスキップ（中間保存で既にCSVに保存済み）
        print("\n💾 範囲指定モード: 中間保存で既にCSVに保存済みのため、最終保存をスキップします")
        print("=" * 80)
        print("✓ 処理完了")
        print("=" * 80)
        sys.exit(0)
    # キャッチアップモード（ハイブリッド方式：みずほ銀行＋hpfree.com）
    # マージモードかつ、既存データがある場合
    elif merge_mode and max_existing_round is not None:
        print(f"\n📥 キャッチアップモード: 最新データを取得して欠番を補完します...")
        print(f"   既存の最大回号: 第{max_existing_round}回")
        
        # 1. みずほ銀行から最新データを取得（日付と当選番号）
        print("   みずほ銀行から最新データを取得中...")
        mizuho_n4_data = {}
        mizuho_n3_data = {}
        
        # N4
        html_n4 = fetch_page(MIZUHO_LATEST_N4_URL)
        if html_n4:
            soup_n4 = BeautifulSoup(html_n4, 'html.parser')
            mizuho_n4_data, _ = parse_mizuhobank_table(soup_n4)
            
        # N3
        html_n3 = fetch_page(MIZUHO_LATEST_N3_URL)
        if html_n3:
            soup_n3 = BeautifulSoup(html_n3, 'html.parser')
            _, mizuho_n3_data = parse_mizuhobank_table(soup_n3)
            
        if not mizuho_n4_data and not mizuho_n3_data:
            print("⚠ みずほ銀行からデータを取得できませんでした")
            sys.exit(1)
            
        # 2. hpfree.comからリハーサル数字を取得
        print("   hpfree.comからリハーサル数字を取得中...")
        hpfree_n4_data = {}
        hpfree_n3_data = {}
        
        html_hpfree = fetch_page(LATEST_PAGE_URL)
        if html_hpfree:
            soup_hpfree = BeautifulSoup(html_hpfree, 'html.parser')
            hpfree_n4_data = parse_n4_table(soup_hpfree, latest_only=False)
            hpfree_n3_data = parse_n3_table(soup_hpfree, latest_only=False)
        else:
            print("⚠ hpfree.comからリハーサル数字を取得できませんでした（リハーサル数字なしで進めます）")
            
        # 3. データを結合
        # みずほ銀行のデータをベースにする
        all_rounds = sorted(set(mizuho_n4_data.keys()) | set(mizuho_n3_data.keys()), reverse=True)
        
        # 既存CSVを読み込んで既存の回号を取得
        existing_data = load_existing_csv(output_file)
        existing_rounds = set()
        for row in existing_data:
            try:
                round_num = int(row.get('round_number', 0))
                if round_num > 0:
                    existing_rounds.add(round_num)
            except (ValueError, TypeError):
                continue
        
        # 欠番を検出（みずほ銀行のデータにあるが既存CSVにない回号）
        missing_rounds = [r for r in all_rounds if r not in existing_rounds]
        
        if not missing_rounds:
            print("✓ 最新データに欠番はありませんでした")
            sys.exit(0)
            
        print(f"✓ {len(missing_rounds)}件の欠番を検出しました")
        print(f"   欠番の回号: {missing_rounds[:10]}{'...' if len(missing_rounds) > 10 else ''}")
        
        # 欠番データを構築
        n4_data = {}
        n3_data = {}
        
        for r in missing_rounds:
            # N4データ
            if r in mizuho_n4_data:
                n4_entry = mizuho_n4_data[r]
                # リハーサル数字をマージ
                if r in hpfree_n4_data:
                    n4_entry['n4_rehearsal'] = hpfree_n4_data[r].get('n4_rehearsal', '')
                n4_data[r] = n4_entry
                
            # N3データ
            if r in mizuho_n3_data:
                n3_entry = mizuho_n3_data[r]
                # リハーサル数字をマージ
                if r in hpfree_n3_data:
                    n3_entry['n3_rehearsal'] = hpfree_n3_data[r].get('n3_rehearsal', '')
                n3_data[r] = n3_entry
        
        print(f"✓ 欠番データを構築: N4={len(n4_data)}件、N3={len(n3_data)}件")
        
        # 取得したデータの範囲を使用
        if n4_data or n3_data:
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            if all_rounds:
                latest_round = max(all_rounds)
    
    elif update_null_mode:
        print("\n🔍 NULL値がある回号を検出中...")
        existing_data = load_existing_csv(output_file)
        if not existing_data:
            print("⚠ 既存CSVファイルが見つかりませんでした")
            sys.exit(1)
        
        # NULL値がある回号を検出
        null_rounds = []
        for row in existing_data:
            round_num = int(row.get('round_number', 0))
            if round_num > 0:
                # いずれかのフィールドがNULLまたは空の場合
                has_null = False
                for key in ['draw_date', 'n3_winning', 'n4_winning', 'n3_rehearsal', 'n4_rehearsal']:
                    value = row.get(key, '')
                    if not value or value == 'NULL':
                        has_null = True
                        break
                if has_null:
                    null_rounds.append(round_num)
        
        if not null_rounds:
            print("✓ NULL値はありませんでした")
            sys.exit(0)
        
        print(f"✓ {len(null_rounds)}件のNULL値がある回号を検出しました")
        print(f"   NULL値がある回号: {null_rounds[:20]}{'...' if len(null_rounds) > 20 else ''}")
        
        # NULL値がある回号を含む範囲を取得
        min_null = min(null_rounds)
        max_null = max(null_rounds)
        
        print(f"\n📥 NULL値がある回号を取得します（第{min_null}回 ～ 第{max_null}回）...")
        
        # NULL値がある回号を含む範囲のデータを取得
        n4_data, n3_data = fetch_multiple_pages(
            base_url,
            len(null_rounds),  # NULL値がある回号の数だけ取得
            latest_round=None,
            target_min_round=min_null,
            target_max_round=max_null,
            output_file=output_file  # 100件ごとにCSVに保存
        )
        
        # NULL値がある回号のみをフィルタリング
        filtered_n4_data = {r: n4_data[r] for r in null_rounds if r in n4_data}
        filtered_n3_data = {r: n3_data[r] for r in null_rounds if r in n3_data}
        
        n4_data = filtered_n4_data
        n3_data = filtered_n3_data
        
        print(f"✓ NULL値がある回号のデータを取得: N4={len(n4_data)}件、N3={len(n3_data)}件")
        
        if not n4_data and not n3_data:
            print("⚠ NULL値がある回号のデータが取得できませんでした")
            sys.exit(1)
        
        # 取得したデータの範囲を使用
        if n4_data or n3_data:
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            if all_rounds:
                latest_round = max(all_rounds)
    # 欠番を埋めるモードの処理
    elif fill_gaps_mode:
        print("\n🔍 欠番の回号を検出中...")
        missing_rounds = find_missing_rounds(output_file)
        
        if not missing_rounds:
            print("✓ 欠番はありませんでした")
            sys.exit(0)
        
        print(f"✓ {len(missing_rounds)}件の欠番を検出しました")
        print(f"   欠番の回号: {missing_rounds[:20]}{'...' if len(missing_rounds) > 20 else ''}")
        
        # 欠番の回号を含む範囲を取得
        min_missing = min(missing_rounds)
        max_missing = max(missing_rounds)
        
        print(f"\n📥 欠番の回号を取得します（第{min_missing}回 ～ 第{max_missing}回）...")
        
        # 欠番の回号を含む範囲のデータを取得
        n4_data, n3_data = fetch_multiple_pages(
            base_url,
            len(missing_rounds),  # 欠番の数だけ取得
            latest_round=None,
            target_min_round=min_missing,
            target_max_round=max_missing,
            output_file=output_file  # 100件ごとにCSVに保存
        )
        
        # 欠番の回号のみをフィルタリング
        filtered_n4_data = {r: n4_data[r] for r in missing_rounds if r in n4_data}
        filtered_n3_data = {r: n3_data[r] for r in missing_rounds if r in n3_data}
        
        # デバッグ情報: 取得したデータの回号範囲を表示
        if n4_data or n3_data:
            all_fetched_rounds = sorted(set(n4_data.keys()) | set(n3_data.keys()))
            print(f"   取得したデータの回号範囲: 第{min(all_fetched_rounds)}回 ～ 第{max(all_fetched_rounds)}回（{len(all_fetched_rounds)}件）")
            print(f"   取得したデータの回号（最初の10件）: {all_fetched_rounds[:10]}")
            print(f"   欠番の回号（最初の10件）: {missing_rounds[:10]}")
            print(f"   一致する回号: {sorted(set(all_fetched_rounds) & set(missing_rounds))[:10]}")
        
        n4_data = filtered_n4_data
        n3_data = filtered_n3_data
        
        print(f"✓ 欠番のデータを取得: N4={len(n4_data)}件、N3={len(n3_data)}件")
        
        if not n4_data and not n3_data:
            print("⚠ 欠番のデータが取得できませんでした")
            print("   考えられる原因:")
            print("   - 欠番の回号のデータがWebページに存在しない可能性があります")
            print("   - データが別のページに存在する可能性があります")
            print("   - ページの構造が変更された可能性があります")
            sys.exit(1)
        
        # 取得したデータの範囲を使用
        if n4_data or n3_data:
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            if all_rounds:
                latest_round = max(all_rounds)
    # マージモードの処理
    elif merge_mode:
        if max_rounds == 1:
            # デフォルト: 最新版ページから最新の1回分のみ取得
            print("📥 マージモード: 最新版ページから最新の1回分のみ取得します...")
            html_content = fetch_page(LATEST_PAGE_URL)
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                # 最新の1行のみ取得
                n4_data = parse_n4_table(soup, latest_only=True)
                n3_data = parse_n3_table(soup, latest_only=True)
                print(f"✓ 最新データを取得: N4={len(n4_data)}件、N3={len(n3_data)}件")
                
                # 取得したデータの回号を使用（実際に取得できた回号）
                if n4_data:
                    actual_latest_round = max(n4_data.keys())
                elif n3_data:
                    actual_latest_round = max(n3_data.keys())
                else:
                    actual_latest_round = latest_round
                
                latest_round = actual_latest_round
                print(f"実際に取得した回号: 第{latest_round}回")
            else:
                n4_data, n3_data = {}, {}
        elif max_rounds <= 10:
            # 最新N件取得: hpfree.comから直接最新N件を取得（超高速）
            print(f"📥 マージモード: 最新の{max_rounds}回分を超高速で取得します（hpfree.comから直接取得）...")
            
            # hpfree.comから最新版ページを取得
            html_content = fetch_page(LATEST_PAGE_URL)
            if not html_content:
                print("⚠ hpfree.comから最新版ページを取得できませんでした")
                n4_data, n3_data = {}, {}
            else:
                soup = BeautifulSoup(html_content, 'html.parser')
                # 全データを取得してから最新N件を抽出
                all_n4_data = parse_n4_table(soup, latest_only=False)
                all_n3_data = parse_n3_table(soup, latest_only=False)
                
                # 最新N件の回号を取得
                all_rounds = sorted(set(all_n4_data.keys()) | set(all_n3_data.keys()), reverse=True)
                target_rounds = all_rounds[:max_rounds]
                
                # 対象回号のデータのみを抽出
                n4_data = {r: all_n4_data[r] for r in target_rounds if r in all_n4_data}
                n3_data = {r: all_n3_data[r] for r in target_rounds if r in all_n3_data}
                
                print(f"✓ 最新{max_rounds}件のデータを取得: N4={len(n4_data)}件、N3={len(n3_data)}件")
                print(f"   取得した回号: {sorted(target_rounds, reverse=True)}")
                
                # 取得したデータの回号を使用
                if target_rounds:
                    latest_round = max(target_rounds)
                    print(f"実際に取得した回号範囲: 第{min(target_rounds)}回 ～ 第{latest_round}回")
                else:
                    print("⚠ データが取得できませんでした")
        else:
            # 大量取得時（max_rounds > 10）: 既存CSVの最古回号より前のデータを取得
            if min_existing_round is not None:
                # 既存CSVがある場合: 最古回号より前のデータを取得
                target_min_round = min_existing_round - max_rounds
                target_max_round = min_existing_round - 1
                print(f"📥 マージモード（大量取得）: 既存CSVの最古回号（第{min_existing_round}回）より前の{max_rounds}件を取得します...")
                print(f"   取得範囲: 第{target_min_round}回 ～ 第{target_max_round}回")
                
                # 既存データにない回号のみを取得するために、取得範囲を指定
                n4_data, n3_data = fetch_multiple_pages(
                    base_url, 
                    max_rounds, 
                    latest_round=None,  # 実際にはtarget_max_roundを使用
                    target_min_round=target_min_round,
                    target_max_round=target_max_round,
                    output_file=output_file  # 100件ごとにCSVに保存
                )
                
                # 取得したデータの範囲を使用
                if n4_data or n3_data:
                    all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                    if all_rounds:
                        latest_round = max(all_rounds)
            else:
                # 既存CSVがない場合: 最新回から指定件数を取得
                print(f"📥 マージモード（大量取得）: 既存CSVがないため、最新回から{max_rounds}件を取得します...")
                n4_data, n3_data = fetch_multiple_pages(base_url, max_rounds, latest_round, output_file=output_file)
    else:
        # 通常モード: 複数ページからデータを取得（既存CSVは上書き）
        print(f"📥 通常モード: 最新回から{max_rounds}件を取得します（既存CSVは上書きされます）...")
        n4_data, n3_data = fetch_multiple_pages(base_url, max_rounds, latest_round, output_file=output_file)
    
    # Webスクレイピングに失敗した場合、フォールバック機能を試す
    use_fallback = '--use-fallback' in sys.argv
    
    if not n4_data and not n3_data:
        if use_fallback or (GEMINI_API_KEY or SERP_API_KEY):
            n4_data, n3_data = fetch_with_fallback(base_url, max_rounds)
        
        if not n4_data and not n3_data:
            print("✗ データが取得できませんでした")
            sys.exit(1)
    elif not n4_data:
        # N3データだけでも処理を続行
        print("⚠ N4データが取得できませんでしたが、N3データのみで処理を続行します")
    
    # データを結合
    print("\n🔗 データを結合中...")
    # 欠番を埋めるモードまたはマージモードの場合は、取得したデータをそのまま使用
    data = combine_data(n4_data, n3_data, latest_round, max_rounds, merge_mode=merge_mode or fill_gaps_mode)
    print(f"✓ {len(data)}件のデータを結合しました")
    
    if not data:
        print("⚠ データが抽出できませんでした")
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
    # 注意: fetch_multiple_pages()内で中間保存が行われている場合（output_fileが指定されている場合）、
    # 最終保存はfetch_multiple_pages()内で既に実行されているため、ここではスキップする
    # ただし、output_fileが指定されていない場合（中間保存が無効な場合）のみ、ここで保存する
    was_intermediate_save_used = False
    if target_min_round is not None or target_max_round is not None:
        # 範囲指定モードの場合、fetch_multiple_pages内で既に中間保存が行われている
        was_intermediate_save_used = True
    elif fill_gaps_mode:
        # 欠番を埋めるモードの場合、fetch_multiple_pages内で既に中間保存が行われている
        was_intermediate_save_used = True
    elif update_null_mode:
        # NULL値を更新するモードの場合、fetch_multiple_pages内で既に中間保存が行われている
        was_intermediate_save_used = True
    elif merge_mode and max_rounds > 10:
        # マージモード（大量取得、max_rounds > 10）の場合、fetch_multiple_pages内で既に中間保存が行われている
        was_intermediate_save_used = True
    # max_rounds <= 10の場合は、fetch_multiple_pagesを呼び出していないため、中間保存は行われていない
    
    if was_intermediate_save_used:
        print("\n💾 中間保存で既にCSVに保存済みのため、最終保存をスキップします")
    else:
        print("\n💾 CSVファイルに保存中...")
        save_to_csv(data, output_file, merge=merge_mode or fill_gaps_mode or update_null_mode, update_null=update_null_mode)
    
    print("\n" + "=" * 80)
    print("✓ 処理完了")
    print("=" * 80)



def fetch_latest_data_for_api(target_round: int) -> Optional[Dict[str, Any]]:
    """
    API用のデータ取得関数
    指定された回号のデータを取得して辞書として返す（CSV保存なし）
    
    Args:
        target_round: 取得したい回号
        
    Returns:
        データ辞書（見つからない場合はNone）
        {
            'round_number': int,
            'draw_date': str,
            'n3_winning': str,
            'n4_winning': str,
            'n3_rehearsal': str,
            'n4_rehearsal': str
        }
    """
    print(f"APIリクエスト: 第{target_round}回のデータを取得します")
    
    # 最新版ページを取得
    html_content = fetch_page(LATEST_PAGE_URL)
    if not html_content:
        print("⚠ 最新版ページの取得に失敗しました")
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 最新の1行のみ取得するのではなく、ページ内の全データを取得して検索
    n4_data = parse_n4_table(soup, latest_only=False)
    n3_data = parse_n3_table(soup, latest_only=False)
    
    # ターゲット回号のデータがあるか確認
    if target_round in n4_data or target_round in n3_data:
        n4_info = n4_data.get(target_round, {})
        n3_info = n3_data.get(target_round, {})
        
        # データを結合
        result = {
            'round_number': target_round,
            'draw_date': n4_info.get('draw_date') or n3_info.get('draw_date') or '',
            'n3_winning': n3_info.get('n3_winning', ''),
            'n4_winning': n4_info.get('n4_winning', ''),
            'n3_rehearsal': n3_info.get('n3_rehearsal', ''),
            'n4_rehearsal': n4_info.get('n4_rehearsal', '')
        }
        
        # 必須データがあるか確認
        if result['n3_winning'] or result['n4_winning']:
            print(f"✓ 第{target_round}回のデータを取得しました")
            return result
            
    print(f"⚠ 第{target_round}回のデータが見つかりませんでした")
    return None


if __name__ == "__main__":

    main()
