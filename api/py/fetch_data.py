"""
Vercel Serverless Function: データ取得API

Webサイトから最新のナンバーズ当選番号・リハーサル番号を取得し、
GitHubのpast_results.csvを更新します。
"""

import os
import sys
import re
import json
import base64
from http.server import BaseHTTPRequestHandler
from typing import Optional, Dict, List, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ------------------------------------------------------------
# 定数
# ------------------------------------------------------------
LATEST_PAGE_URL = "https://www.hpfree.com/numbers/rehearsal.html"
GITHUB_REPO = os.environ.get("GITHUB_REPO", "Ks-Classic/numbers-ai")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")

def log(msg: str):
    """ログ出力"""
    print(f"[fetch_data] {msg}", file=sys.stderr)

# ------------------------------------------------------------
# Webページ取得・解析
# ------------------------------------------------------------
def fetch_page(url: str) -> Optional[str]:
    """WebページのHTMLを取得する"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as resp:
            # エンコーディングを推測
            content = resp.read()
            # shift-jisを試す
            try:
                return content.decode('shift-jis')
            except:
                try:
                    return content.decode('utf-8')
                except:
                    return content.decode('latin-1')
    except Exception as e:
        log(f"⚠ ページ取得エラー: {e}")
        return None

def extract_number_from_cell(cell_text: str) -> Optional[str]:
    """セル文字列から数値を抽出"""
    if not cell_text:
        return None
    txt = cell_text.strip()
    # 矢印（→）の後の数字を取得
    arrow = re.search(r"[→→→](\d+)", txt)
    if arrow:
        return arrow.group(1)
    # 取り消し線を除去
    txt = re.sub(r"[\u0336\u0335\u0332]", "", txt)
    # 括弧付き注釈を除去
    txt = re.sub(r"\([^)]*\)", "", txt)
    # 数字だけ抽出
    digits = re.findall(r"\d", txt)
    if digits:
        return digits[0]
    return None

def parse_html_simple(html: str) -> Dict[int, Dict[str, str]]:
    """HTMLから回号データを抽出（正規表現ベース）"""
    result: Dict[int, Dict[str, str]] = {}
    
    # テーブル行を抽出
    # <tr>...</tr> パターン
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    
    for row in rows:
        # 回号を探す
        round_match = re.search(r'第(\d+)回', row)
        if not round_match:
            continue
        rnd = int(round_match.group(1))
        
        # セルを抽出
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
        if not cells:
            continue
        
        # 初期化
        entry = result.setdefault(rnd, {
            "n3_rehearsal": "NULL",
            "n4_rehearsal": "NULL",
            "n3_winning": "NULL",
            "n4_winning": "NULL",
        })
        
        # HTMLタグを除去して数字を抽出
        clean_cells = []
        for cell in cells:
            # タグを除去
            clean = re.sub(r'<[^>]+>', '', cell).strip()
            clean_cells.append(clean)
        
        # N4テーブル（10列以上）
        if len(clean_cells) >= 10:
            n4_re = []
            for i in range(1, 5):
                d = extract_number_from_cell(clean_cells[i])
                if d:
                    n4_re.append(d)
            n4_win = []
            for i in range(6, 10):
                d = extract_number_from_cell(clean_cells[i])
                if d:
                    n4_win.append(d)
            
            if len(n4_re) == 4:
                entry["n4_rehearsal"] = "".join(n4_re)
            if len(n4_win) == 4:
                entry["n4_winning"] = "".join(n4_win)
        
        # N3テーブル（8列以上）
        elif len(clean_cells) >= 8:
            n3_re = []
            for i in range(1, 4):
                d = extract_number_from_cell(clean_cells[i])
                if d:
                    n3_re.append(d)
            n3_win = []
            for i in range(5, 8):
                d = extract_number_from_cell(clean_cells[i])
                if d:
                    n3_win.append(d)
            
            if len(n3_re) == 3:
                entry["n3_rehearsal"] = "".join(n3_re)
            if len(n3_win) == 3:
                entry["n3_winning"] = "".join(n3_win)
    
    return result

# ------------------------------------------------------------
# GitHub API操作
# ------------------------------------------------------------
def get_github_csv() -> tuple[str, str]:
    """GitHubからCSVを取得し、(content, sha)を返す"""
    pat_token = os.environ.get("PAT_TOKEN")
    if not pat_token:
        raise Exception("PAT_TOKENが設定されていません")
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/data/past_results.csv?ref={GITHUB_BRANCH}"
    req = Request(url, headers={
        "Authorization": f"Bearer {pat_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "numbers-ai",
    })
    
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]

def update_github_csv(new_content: str, sha: str, message: str) -> dict:
    """GitHubのCSVを更新"""
    pat_token = os.environ.get("PAT_TOKEN")
    if not pat_token:
        raise Exception("PAT_TOKENが設定されていません")
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/data/past_results.csv"
    
    payload = json.dumps({
        "message": message,
        "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
        "sha": sha,
        "branch": GITHUB_BRANCH,
    }).encode("utf-8")
    
    req = Request(url, data=payload, method="PUT", headers={
        "Authorization": f"Bearer {pat_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "numbers-ai",
    })
    
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def parse_csv(content: str) -> Dict[int, Dict]:
    """CSVをパース"""
    data: Dict[int, Dict] = {}
    lines = content.strip().split("\n")
    for line in lines[1:]:  # ヘッダースキップ
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
    return data

def build_csv(data: Dict[int, Dict]) -> str:
    """CSVを構築"""
    lines = ["round_number,draw_date,weekday,n3_rehearsal,n4_rehearsal,n3_winning,n4_winning"]
    for rnd in sorted(data.keys(), reverse=True):
        row = data[rnd]
        lines.append(
            f"{row['round_number']},{row['draw_date']},{row['weekday']},"
            f"{row['n3_rehearsal']},{row['n4_rehearsal']},{row['n3_winning']},{row['n4_winning']}"
        )
    return "\n".join(lines) + "\n"

def has_valid_winning_data(data: Dict[int, Dict], round_num: int) -> bool:
    """当選番号が有効か"""
    row = data.get(round_num)
    if not row:
        return False
    if row.get("n3_winning") in ["NULL", ""] or row.get("n4_winning") in ["NULL", ""]:
        return False
    return True

# ------------------------------------------------------------
# メインロジック
# ------------------------------------------------------------
def fetch_and_update(target_round: int) -> dict:
    """指定回号の予測に必要なデータを取得・更新"""
    log(f"📥 回号{target_round}の予測に必要なデータを確認中...")
    
    # 1. GitHubから現在のCSVを取得
    csv_content, sha = get_github_csv()
    existing = parse_csv(csv_content)
    
    # 2. 必要なデータがあるかチェック
    need_fetch = False
    missing_rounds = []
    
    # 前回(n-1)の当選番号
    if not has_valid_winning_data(existing, target_round - 1):
        need_fetch = True
        missing_rounds.append(target_round - 1)
    
    # 前々回(n-2)の当選番号
    if not has_valid_winning_data(existing, target_round - 2):
        need_fetch = True
        missing_rounds.append(target_round - 2)
    
    if not need_fetch:
        log("✅ 必要なデータは既に存在します")
        return {
            "success": True,
            "updated": False,
            "message": "データは最新です",
            "csv_content": csv_content,
        }
    
    log(f"⚠ 不足データ: 回号 {missing_rounds}")
    
    # 3. Webから最新データを取得
    log("📥 Webから最新データを取得中...")
    html = fetch_page(LATEST_PAGE_URL)
    if not html:
        raise Exception("Webページの取得に失敗しました")
    
    web_data = parse_html_simple(html)
    if not web_data:
        raise Exception("Webページからデータを抽出できませんでした")
    
    log(f"✓ Webから {len(web_data)} 件の回号データを取得")
    
    # 4. データを更新
    updated_count = 0
    rounds_to_check = [target_round - 2, target_round - 1, target_round]
    
    for rnd in rounds_to_check:
        if rnd <= 0:
            continue
        web_row = web_data.get(rnd)
        if not web_row:
            continue
        
        if rnd in existing:
            row = existing[rnd]
            changed = False
            for key in ["n3_rehearsal", "n4_rehearsal", "n3_winning", "n4_winning"]:
                new_val = web_row.get(key)
                old_val = row.get(key)
                if new_val and new_val != "NULL" and new_val != old_val:
                    row[key] = new_val
                    changed = True
            if changed:
                updated_count += 1
                log(f"   ✓ 第{rnd}回を更新")
        else:
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
    
    if updated_count == 0:
        log("ℹ️ 更新するデータがありませんでした")
        return {
            "success": True,
            "updated": False,
            "message": "更新するデータがありませんでした（Webにもデータがない可能性）",
            "csv_content": csv_content,
        }
    
    # 5. GitHubに保存
    new_csv = build_csv(existing)
    commit_result = update_github_csv(
        new_csv, 
        sha, 
        f"chore: 回号{target_round}予測用データを自動更新 [skip ci]"
    )
    
    log(f"✅ {updated_count} 件のデータを更新し、GitHubにコミットしました")
    
    return {
        "success": True,
        "updated": True,
        "updated_count": updated_count,
        "message": f"{updated_count}件のデータを更新しました",
        "csv_content": new_csv,
        "commit_url": commit_result.get("commit", {}).get("html_url"),
    }

# ------------------------------------------------------------
# Vercel Serverless Function Handler
# ------------------------------------------------------------
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # リクエストボディを取得
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            target_round = data.get("target_round") or data.get("roundNumber")
            
            if not target_round:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "target_round または roundNumber が必要です"
                }, ensure_ascii=False).encode('utf-8'))
                return
            
            result = fetch_and_update(int(target_round))
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            log(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False).encode('utf-8'))
    
    def do_GET(self):
        """ヘルスチェック用"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "endpoint": "/api/py/fetch_data",
            "description": "POST with {target_round: number} to fetch and update data"
        }).encode('utf-8'))

