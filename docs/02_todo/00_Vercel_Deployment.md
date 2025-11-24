# Vercelデプロイ計画 (Current Sprint)

**目標**: Next.jsフロントエンドとPython Serverless FunctionsバックエンドをVercelに完全デプロイする。

## 戦略: Clean Cloud Build + libgomp手動注入
ローカルのARM64環境（WSL/Windows）とVercelのx86_64環境のアーキテクチャ不一致を解消するため、バイナリをリポジトリに含めず、Vercelのビルドプロセスで依存関係を解決させる。ただし、`libgomp.so.1`（164KB）のみx86_64版を手動配置。

## タスク一覧

### 1. 構成と設定 (完了)
- [x] `vercel.json` の設定（Pythonランタイムのメモリ・タイムアウト設定）
- [x] `next.config.ts` でのCORS設定（Global Headers）
- [x] `requirements.txt` の統一と軽量化

### 2. アーキテクチャ不一致の解消 (完了)
- [x] **x86_64版libgomp取得**: scikit-learn wheelから抽出
- [x] **手動配置**: `api/lib/libgomp.so.1` (164KB)
- [x] **コード修正**: `axis.py`, `combination.py` に手動ロード処理を追加
- [x] **依存関係調整**: `requirements.txt` から `scikit-learn` を除外（サイズ削減）
- [x] **デプロイ**: `vercel deploy --force` によるクリーンビルド成功

### 3. 動作確認 (進行中)
- [ ] プレビュー環境での予測実行（N3/N4）
- [ ] エラーログの確認（500エラー、ImportErrorがないこと）
- [ ] 本番環境（Production）への昇格

## プレビュー環境
- URL: `https://numbers-mygipqj1l-ks-classic.vercel.app`
- デプロイ日時: 2025-11-24

## 関連ドキュメント
- [CUBE生成ルール](../01_design/CUBE生成ルール.md): 実装済みの仕様
- [Vercelデプロイ手順](../VERCEL_DEPLOY.md): 詳細な手順書
