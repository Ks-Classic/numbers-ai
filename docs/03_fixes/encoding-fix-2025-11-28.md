# データ取得エンコーディング修正

## 問題の概要

Vercel本番環境で回号入力時に最新データチェックを行い、データがなければhpfree.comから取得する機能が正しく動作していませんでした。

### エラーログ
```
[API] データ更新開始: 回号=6867
[API] 既存データ: 6846件
[API] hpfree.comからデータ取得中...
[API] Webから 0 件の回号データを取得
[API] 更新対象: 0件
```

## 原因

hpfree.comのページは**Shift_JIS**エンコーディングを使用していますが、Node.jsの`fetch` APIはデフォルトで**UTF-8**としてデコードしていました。

### 検証結果

1. **HTMLのエンコーディング宣言**
   ```html
   <meta charset="Shift_JIS">
   ```

2. **文字化けの例**
   - 正しい: `第6867回`
   - 文字化け: `æ6867ñ`

3. **パース失敗の理由**
   - 正規表現 `/第(\d+)回/` が文字化けしたテキストにマッチしない
   - 結果として0件のデータが抽出される

## 修正内容

### `/src/app/api/update-data/route.ts`

**変更前:**
```typescript
const html = await webResponse.text();
const webData = parsePage(html);
```

**変更後:**
```typescript
// Shift_JISでデコード（hpfree.comはShift_JISを使用）
const buffer = await webResponse.arrayBuffer();
const decoder = new TextDecoder('shift-jis');
const html = decoder.decode(buffer);
const webData = parsePage(html);
```

### 他のファイルの状況

- ✅ `/api/py/fetch_data.py` - 既にShift_JISに対応済み（40-42行目）
- ✅ `/api/check-latest-data/route.ts` - hpfree.comから直接取得していないため修正不要
- ✅ `/api/get-latest-round/route.ts` - 実装されていないため修正不要

## テスト方法

### ローカルテスト用スクリプト

デバッグ用のPythonスクリプトを作成して検証しました:

```bash
python3 debug_encoding.py
```

**結果:**
```
Response encoding: ISO-8859-1
Apparent encoding: SHIFT_JIS
Content-Type header: text/html

Trying Shift_JIS encoding...
Found 3 tables
Row 2 (10 cells): 第6868回本番→
  ✓ Found round: 6868
Row 3 (10 cells): 第6867回本番→
  ✓ Found round: 6867
Row 4 (10 cells): 第6866回3110本番→2803
  ✓ Found round: 6866
```

## デプロイ手順

1. ビルド確認
   ```bash
   npm run build
   ```

2. Vercelにデプロイ
   ```bash
   git add .
   git commit -m "fix: hpfree.comのShift_JISエンコーディングに対応"
   git push
   ```

3. 本番環境で動作確認
   - 回号入力画面で最新回号を入力
   - データ更新APIが正しく動作することを確認
   - ログで「Webから X 件の回号データを取得」と表示されることを確認

## 期待される動作

修正後は、hpfree.comから正しくデータを取得できるようになります:

```
[API] データ更新開始: 回号=6867
[API] 既存データ: 6846件
[API] hpfree.comからデータ取得中...
[API] Webから 20 件の回号データを取得  ← 修正後
[API] 更新対象: 3件
```

## 関連ファイル

- `/src/app/api/update-data/route.ts` - 修正済み
- `/api/py/fetch_data.py` - 既に対応済み
- `/debug_encoding.py` - デバッグ用スクリプト（削除可能）
- `/debug_hpfree.py` - デバッグ用スクリプト（削除可能）
- `/debug_parse.py` - デバッグ用スクリプト（削除可能）
