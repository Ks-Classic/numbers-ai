# 過去データ自動更新システム セットアップガイド

## 概要

このシステムは、ナンバーズの過去当選番号データ（`past_results.csv`）を自動的に更新する仕組みです。

- **cronジョブ**: 平日15:00に自動実行
- **抽選日判定**: 平日（月〜金）かつ年末年始（12/29〜1/3）を除外
- **フォールバック機能**: Webスクレイピング失敗時に検索APIを使用

## セットアップ手順

### 1. 依存パッケージのインストール

```bash
cd scripts
pip install -r requirements.txt python-dotenv
```

### 2. 環境変数の設定

プロジェクトルートに `.env.local` ファイルを作成し、必要に応じてAPIキーを設定します：

```bash
# データ更新用APIキー（オプション）
# Webスクレイピングに失敗した場合のフォールバック機能で使用
GEMINI_API_KEY=your_gemini_api_key_here
SERP_API_KEY=your_serp_api_key_here
```

**注意**: APIキーは必須ではありません。Webスクレイピングが正常に動作する場合は設定不要です。

### 3. cronジョブの設定

WSL環境でcronジョブを設定します：

```bash
# スクリプトに実行権限を付与
chmod +x scripts/setup_cron.sh scripts/auto_update_past_results.py

# cronジョブを設定
bash scripts/setup_cron.sh
```

### 4. cronサービスの起動（WSL環境）

WSL環境では、cronサービスが起動していない場合があります：

```bash
# cronサービスを起動
sudo service cron start

# cronサービスを自動起動するように設定
sudo systemctl enable cron

# cronサービスの状態を確認
sudo service cron status
```

### 5. 手動実行の確認

cronジョブが正しく動作するか確認するため、手動で実行してみます：

```bash
python3 scripts/auto_update_past_results.py
```

## cronジョブの設定内容

```
0 15 * * 1-5 cd /path/to/project && python3 scripts/auto_update_past_results.py >> logs/cron.log 2>&1
```

- **実行時刻**: 毎日15:00（抽選後）
- **実行曜日**: 月曜日〜金曜日（1-5）
- **ログ出力**: `logs/cron.log`

## 動作フロー

1. **cronジョブ実行**（平日15:00）
   ↓
2. **抽選日判定**（平日かつ年末年始でない）
   ↓
3. **最新回号を取得**（最新版ページから自動取得）
   ↓
4. **最新版ページから最新の1回分のみ取得**（マージモード）
   ↓
5. **Webスクレイピング実行**（`fetch_past_results.py --merge`）
   ↓
6. **失敗時** → 検索APIフォールバック（Gemini API → SerpAPI）
   ↓
7. **CSV更新**（既存CSVファイルとマージして最新の1回分を追加/更新）
   ↓
8. **ログ記録**（`logs/data_update_YYYY-MM-DD.log`）

**注意**: 自動実行時は最新の1回分のみ取得します。過去分を大量に取得する場合は手動実行してください。

## 手動実行時の大量取得

手動実行時は、`--limit`オプションで大量のデータを取得できます：

```bash
# 過去1000件を取得
python3 scripts/fetch_past_results.py --limit 1000

# 過去500件を取得して別ファイルに保存
python3 scripts/fetch_past_results.py data/my_results.csv --limit 500
```

スクリプトは自動的に必要なページを探索して取得します。

## ログファイル

- **実行ログ**: `logs/data_update_YYYY-MM-DD.log`
- **cronログ**: `logs/cron.log`

ログには以下の情報が記録されます：
- 実行日時
- 抽選日判定結果
- データ取得結果
- エラー情報（発生時）

## トラブルシューティング

### cronジョブが実行されない

1. **cronサービスが起動しているか確認**
   ```bash
   sudo service cron status
   ```

2. **cronジョブが正しく設定されているか確認**
   ```bash
   crontab -l
   ```

3. **手動実行で動作確認**
   ```bash
   python3 scripts/auto_update_past_results.py
   ```

4. **ログファイルを確認**
   ```bash
   tail -f logs/cron.log
   tail -f logs/data_update_$(date +%Y-%m-%d).log
   ```

### Webスクレイピングに失敗する

1. **インターネット接続を確認**
2. **フォールバック機能が有効か確認**（APIキーが設定されているか）
3. **ログファイルでエラー内容を確認**

### データが更新されない

1. **CSVファイルの更新時刻を確認**
   ```bash
   ls -l data/past_results.csv
   ```

2. **ログファイルで実行結果を確認**
3. **手動実行で動作確認**

## 注意事項

- **APIキーの管理**: `.env.local`ファイルはgitignoreに含まれているため、APIキーがコミットされないよう注意してください
- **WSL環境**: WSL環境では、cronサービスが起動していない場合があります。システム起動時に自動起動する設定を推奨します
- **年末年始**: 12/29〜1/3は抽選日ではないため、自動更新はスキップされます

## CUBE生成との関係

### CUBE生成は手動トリガー

- **CUBE生成**: ユーザーが回号を入力することで実行される（手動トリガー）
- **データ更新**: 当選番号とリハーサル数字は自動取得・更新される（自動化）

### データ更新の重要性

- **当日の回号のCUBE生成**: ユーザーが当日の回号を入力した際に、前日分の当選番号とリハーサル数字が利用可能である必要がある
- **データの最新性**: 毎日最新データが自動取得・更新されるため、常に最新の情報でCUBEを生成できる

詳細は [04-05_データ自動更新とCUBE生成自動化.md](../02_todo/04_operations/04-05_データ自動更新とCUBE生成自動化.md) を参照。

## 関連ファイル

- `scripts/fetch_past_results.py`: データ取得スクリプト
- `scripts/auto_update_past_results.py`: 自動更新スクリプト
- `scripts/setup_cron.sh`: cronジョブ設定スクリプト
- `data/past_results.csv`: 過去当選番号データ
- `logs/data_update_*.log`: 実行ログ
- `logs/cron.log`: cron実行ログ

## 関連ドキュメント

- [04-05_データ自動更新とCUBE生成自動化.md](../02_todo/04_operations/04-05_データ自動更新とCUBE生成自動化.md): データ自動更新とCUBE生成の関係
- [10-cube-automation-design.md](../01_design/10-cube-automation-design.md): CUBE生成システム設計書
