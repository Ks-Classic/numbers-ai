#!/usr/bin/env python3
"""
ナンバーズ過去当選番号・リハーサル番号取得スクリプト（シンプル版）

データソース: https://www.hpfree.com/numbers/rehearsal.html
指定回号の前回・前々回の当選番号・リハーサル番号を取得し、past_results.csv に埋めます。
※ 日付は取得できないため NULL のままです。
"""

import sys
import re
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("エラー: 必要なパッケージがインストールされていません。\n")
    sys.stderr.write("以下のコマンドでインストールしてください: pip install requests beautifulsoup4\n")
    sys.exit(1)

# ------------------------------------------------------------
# 定数・ユーティリティ
# ------------------------------------------------------------
LATEST_PAGE_URL = "https://www.hpfree.com/numbers/rehearsal.html"

def log(msg: str):
    """標準エラー出力にログを出力（JSON出力を妨げないため）"""
    sys.stderr.write(f"{msg}\n")

def fetch_page(url: str) -> Optional[str]:
    """WebページのHTMLを取得する"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        if resp.encoding is None or resp.encoding == "ISO-8859-1":
            resp.encoding = resp.apparent_encoding or "shift-jis"
        return resp.text
    except Exception as e:
        log(f"⚠ ページ取得エラー: {e}")
        return None

def extract_number_from_cell(cell_text: str) -> Optional[str]:
    """セル文字列から数値を抽出（取り消し線・括弧・矢印に対応）"""
    if not cell_text:
        return None
    txt = cell_text.strip()
    # 矢印（→）の後の数字を取得（例: 8→0）
    arrow = re.search(r"[→→→](\d+)", txt)
    if arrow:
        return arrow.group(1)
    # 取り消し線を除去（U+0336 など）
    txt = re.sub(r"[\u0336\u0335\u0332]", "", txt)
    # 括弧付き注釈を除去 (例: (不), (落))
    txt = re.sub(r"\([^)]*\)", "", txt)
    # 数字だけ抽出
    digits = re.findall(r"\d", txt)
    if digits:
        return digits[0]
    return None

# ------------------------------------------------------------
# テーブル解析ロジック（N4 と N3 を同一回号でマージ）
# ------------------------------------------------------------
def parse_page(soup: BeautifulSoup) -> Dict[int, Dict[str, str]]:
    """ページ内の全テーブルを走査し、回号ごとに N3/N4 データをマージして返す"""
    result: Dict[int, Dict[str, str]] = {}
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            # 回号を探す
            row_text = row.get_text()
            m = re.search(r"第(\d+)回", row_text)
            if not m:
                continue
            rnd = int(m.group(1))
            
            # 初期化または更新
            entry = result.setdefault(rnd, {
                "n3_rehearsal": "NULL",
                "n4_rehearsal": "NULL",
                "n3_winning": "NULL",
                "n4_winning": "NULL",
            })

            # N4 テーブルは 10 列以上、N3 は 8 列以上
            if len(cells) >= 10:
                # N4 リハーサル 4桁 (1~4 列)
                n4_re = []
                for i in range(1, 5):
                    d = extract_number_from_cell(cells[i].get_text())
                    if d:
                        n4_re.append(d)
                # N4 当選 4桁 (6~9 列)
                n4_win = []
                for i in range(6, 10):
                    d = extract_number_from_cell(cells[i].get_text())
                    if d:
                        n4_win.append(d)
                
                if len(n4_re) == 4:
                    entry["n4_rehearsal"] = "".join(n4_re)
                if len(n4_win) == 4:
                    entry["n4_winning"] = "".join(n4_win)
            elif len(cells) >= 8:
                # N3 リハーサル 3桁 (1~3 列)
                n3_re = []
                for i in range(1, 4):
                    d = extract_number_from_cell(cells[i].get_text())
                    if d:
                        n3_re.append(d)
                # N3 当選 3桁 (5~7 列)
                n3_win = []
                for i in range(5, 8):
                    d = extract_number_from_cell(cells[i].get_text())
                    if d:
                        n3_win.append(d)
                
                if len(n3_re) == 3:
                    entry["n3_rehearsal"] = "".join(n3_re)
                if len(n3_win) == 3:
                    entry["n3_winning"] = "".join(n3_win)
    return result

# ------------------------------------------------------------
# CSV 入出力ユーティリティ
# ------------------------------------------------------------
def load_csv(csv_path: str) -> Dict[int, Dict]:
    path = Path(csv_path)
    if not path.exists():
        return {}
    data: Dict[int, Dict] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[1:]:  # ヘッダーはスキップ
            if not line.strip():
                continue
            cols = line.strip().split(",")
            try:
                rnd = int(cols[0])
            except:
                continue
            data[rnd] = {
                "round_number": rnd,
                "draw_date": cols[1] if len(cols) > 1 else "NULL",
                "weekday": cols[2] if len(cols) > 2 else "NULL",
                "n3_rehearsal": cols[3] if len(cols) > 3 else "NULL",
                "n4_rehearsal": cols[4] if len(cols) > 4 else "NULL",
                "n3_winning": cols[5] if len(cols) > 5 else "NULL",
                "n4_winning": cols[6] if len(cols) > 6 else "NULL",
            }
    except Exception as e:
        log(f"⚠ CSV読み込みエラー: {e}")
    return data

def save_csv(data: Dict[int, Dict], csv_path: str):
    path = Path(csv_path)
    # 降順でソート
    rounds = sorted(data.keys(), reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("round_number,draw_date,weekday,n3_rehearsal,n4_rehearsal,n3_winning,n4_winning\n")
        for r in rounds:
            row = data[r]
            f.write(
                f"{row['round_number']},{row['draw_date']},{row['weekday']},{row['n3_rehearsal']},{row['n4_rehearsal']},{row['n3_winning']},{row['n4_winning']}\n"
            )

def has_valid_winning_data(data: Dict[int, Dict], round_num: int) -> bool:
    """指定回号の当選番号が正しく存在するか（N3/N4ともに）"""
    row = data.get(round_num)
    if not row:
        return False
    # NULLでないこと、空文字でないこと
    if row.get("n3_winning") in ["NULL", ""] or row.get("n4_winning") in ["NULL", ""]:
        return False
    return True

# ------------------------------------------------------------
# メインロジック
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='ナンバーズデータ取得（シンプル版）')
    parser.add_argument('target_round', type=int, nargs='?', help='対象回号（予測する回号）')
    parser.add_argument('--force', action='store_true', help='強制的にWebから再取得する')
    parser.add_argument('--json', action='store_true', default=True, help='結果をJSONで出力する（デフォルトTrue）')
    args = parser.parse_args()

    target_round = args.target_round
    
    # CSVパス
    csv_path = Path(__file__).parent.parent.parent / "data" / "past_results.csv"
    existing = load_csv(str(csv_path))

    # 更新が必要かチェック
    need_fetch = False
    if args.force:
        need_fetch = True
        log("ℹ️ 強制更新モード")
    elif target_round:
        # 1. 前回(n-1)の当選番号チェック
        if not has_valid_winning_data(existing, target_round - 1):
            log(f"ℹ️ 第{target_round - 1}回のデータが不足しています")
            need_fetch = True
        # 2. 前々回(n-2)の当選番号チェック
        elif not has_valid_winning_data(existing, target_round - 2):
            log(f"ℹ️ 第{target_round - 2}回のデータが不足しています")
            need_fetch = True
        # 3. 当該回(n)のリハーサル番号チェック（予測時はこれが欲しい）
        # 既にリハーサル番号があればFetch不要だが、更新されている可能性もあるので
        # 当選番号がまだない場合（＝未来/当日）は念のため見に行くのが安全
        elif not has_valid_winning_data(existing, target_round):
             # 当選番号が決まっていない＝予測段階。リハーサル番号の最新状態を確認しに行く
            log(f"ℹ️ 第{target_round}回の最新情報を確認します")
            need_fetch = True
    else:
        # target_round指定なし -> 全更新
        need_fetch = True

    updated_count = 0
    
    if need_fetch:
        log("📥 最新ページ取得中...")
        html = fetch_page(LATEST_PAGE_URL)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            web_data = parse_page(soup)
            
            if web_data:
                log(f"✓ ページから {len(web_data)} 件の回号データを取得")
                
                # 更新対象の設定
                rounds_to_check = []
                if target_round:
                    rounds_to_check = [target_round - 2, target_round - 1, target_round]
                else:
                    rounds_to_check = list(web_data.keys())

                for rnd in rounds_to_check:
                    if rnd <= 0: continue
                    web_row = web_data.get(rnd)
                    if not web_row: continue

                    if rnd in existing:
                        # 既存行あり -> NULL項目のみ更新、または上書き
                        row = existing[rnd]
                        changed = False
                        for key in ["n3_rehearsal", "n4_rehearsal", "n3_winning", "n4_winning"]:
                            new_val = web_row.get(key)
                            old_val = row.get(key)
                            # NULLまたは空なら更新。値があってもWeb側のデータが新しければ更新（修正など）
                            # ここでは「NULLから値が入った」または「値が変わった」場合のみ更新
                            if new_val and new_val != "NULL" and new_val != old_val:
                                row[key] = new_val
                                changed = True
                        if changed:
                            updated_count += 1
                    else:
                        # 新規追加
                        existing[rnd] = {
                            "round_number": rnd,
                            "draw_date": "NULL",
                            "weekday": "NULL",
                            "n3_rehearsal": web_row.get("n3_rehearsal", "NULL"),
                            "n4_rehearsal": web_row.get("n4_rehearsal", "NULL"),
                            "n3_winning": web_row.get("n3_winning", "NULL"),
                            "n4_winning": web_row.get("n4_winning", "NULL"),
                        }
                        updated_count += 1
                        log(f"   ✓ 第{rnd}回を追加")
            else:
                log("❌ ページから有効データが取得できませんでした")
        else:
            log("❌ ページ取得失敗")

    # 保存
    if updated_count > 0:
        save_csv(existing, str(csv_path))
        log(f"✅ {updated_count} 件のデータを更新しました")
    else:
        log("ℹ️ 更新データはありませんでした")

    # 結果出力 (JSON)
    result = {
        "success": True,
        "updated_count": updated_count,
        "target_round": target_round,
        "data": None
    }
    
    if target_round:
        row = existing.get(target_round, {})
        result["data"] = {
            "round_number": target_round,
            "n3_rehearsal": row.get("n3_rehearsal"),
            "n4_rehearsal": row.get("n4_rehearsal"),
            "n3_winning": row.get("n3_winning"),
            "n4_winning": row.get("n4_winning"),
            "exists": target_round in existing
        }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()