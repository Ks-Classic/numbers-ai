# FastAPIサーバー起動方法

## セットアップ

1. 仮想環境を作成（推奨）
```bash
cd api
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. 環境変数を設定（必要に応じて）
```bash
export FASTAPI_URL=http://localhost:8000
```

## 起動方法

### 方法1: run.pyを使用（推奨）
```bash
cd api
source venv/bin/activate
python run.py
```

サーバーは `http://localhost:8000` で起動します。

### 方法2: uvicornを直接使用
```bash
cd api
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 動作確認

サーバー起動後、以下のコマンドでヘルスチェックを実行：

```bash
curl http://localhost:8000/health
```

正常な場合、以下のようなJSONが返されます：
```json
{
  "status": "ok",
  "model_loaded": true,
  "data_loaded": true
}
```

## APIエンドポイント

- `GET /health` - ヘルスチェック
- `POST /api/predict/axis` - 軸数字予測
- `POST /api/predict/combination` - 組み合わせ予測
- `POST /api/reload` - モデルとデータの強制再読み込み

## ドキュメント

サーバー起動後、以下のURLでAPIドキュメントを確認できます：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 注意事項

- サーバー起動時にモデルとデータを読み込みます（初回は数秒かかる場合があります）
- モデルファイルは `data/models/` に配置してください
- 過去データは `data/past_results.csv` に配置してください
- 罫線マスターデータは `data/keisen_master.json` に配置してください
- ファイル更新自動検知機能により、モデルやデータを更新すると次回のAPIリクエスト時に自動的に再読み込みされます

## トラブルシューティング

### モジュールが見つからないエラー

```bash
# 仮想環境を有効化
source venv/bin/activate

# 依存関係を再インストール
pip install -r requirements.txt
```

### モデルファイルが見つからないエラー

- `data/models/` ディレクトリに必要なモデルファイル（`.pkl`）が配置されているか確認
- モデルファイル名は以下の通り：
  - `n3_axis.pkl`
  - `n4_axis.pkl`
  - `n3_box_comb.pkl`
  - `n3_straight_comb.pkl`
  - `n4_box_comb.pkl`
  - `n4_straight_comb.pkl`（オプション）

### ポート8000が既に使用されている場合

```bash
# 別のポートで起動
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

ただし、その場合は `.env.local` で `FASTAPI_URL` も変更してください。
