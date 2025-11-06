# リハーサル数字可視化サーバーの使用方法

## 概要

`visualization_server.py`は、リハーサル数字と当選番号の関係性を可視化するためのHTTPサーバーです。
ブラウザから指定回号の全パターン（A1, A2, B1, B2）のデータを生成し、リアルタイムで表示できます。

## 起動方法

**重要**: 仮想環境をアクティベートしてからサーバーを起動してください。

```bash
cd notebooks
source venv/bin/activate
python3 visualization_server.py
```

デフォルトでポート8000で起動します。別のポートを使用する場合は：

```bash
python3 visualization_server.py --port 8080
```

## トラブルシューティング

### ModuleNotFoundError: No module named 'pandas'

仮想環境がアクティベートされていません。以下のコマンドでアクティベートしてください：

```bash
cd notebooks
source venv/bin/activate
python3 visualization_server.py
```

仮想環境が存在しない場合は、以下のコマンドで作成してください：

```bash
cd notebooks
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy
python3 visualization_server.py
```

## APIエンドポイント

### GET /api/rounds

利用可能な回号リスト（6000回以降）を取得します。

**レスポンス例:**
```json
{
  "success": true,
  "rounds": [6849, 6848, 6847, ...]
}
```

### GET /api/generate?round=<回号>&target=n3

指定回号の全パターン（A1, A2, B1, B2）のデータを生成します。

**パラメータ:**
- `round`: 回号（必須、6000以上）
- `target`: 対象（n3またはn4、デフォルト: n3）

**レスポンス例:**
```json
{
  "success": true,
  "round_number": 6849,
  "data": {
    "A1": { ... },
    "A2": { ... },
    "B1": { ... },
    "B2": { ... }
  }
}
```

## HTMLページでの使用

1. サーバーを起動
2. ブラウザで `docs/report/rehearsal_chart_interactive.html` を開く
3. 回号をプルダウンで選択（降順表示）
4. 「表示」ボタンをクリック（全パターンのデータが生成される）
5. パターンを切り替えて表示

## トラブルシューティング

### CORSエラーが発生する場合

サーバーが正しく起動しているか確認してください。

### データが生成されない場合

- 指定回号が6000以上であることを確認
- `train_data_from_4801.csv`に該当回号のデータが存在することを確認
- リハーサル数字が存在する回号であることを確認

