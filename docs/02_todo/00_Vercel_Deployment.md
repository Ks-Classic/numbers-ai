# Vercelデプロイ計画 (Current Sprint)

**目標**: Next.jsフロントエンドとPython Serverless FunctionsバックエンドをVercelに完全デプロイする。

## 戦略: Clean Cloud Build (Method A)
ローカルのARM64環境（WSL/Windows）とVercelのx86_64環境のアーキテクチャ不一致を解消するため、バイナリをリポジトリに含めず、Vercelのビルドプロセスで依存関係を解決させる。

## タスク一覧

### 1. 構成と設定 (完了)
- [x] `vercel.json` の設定（Pythonランタイムのメモリ・タイムアウト設定）
- [x] `next.config.ts` でのCORS設定（Global Headers）
- [x] `requirements.txt` の統一と軽量化

### 2. アーキテクチャ不一致の解消 (進行中)
- [ ] **クリーンアップ**: 手動で追加したバイナリ（`api/lib/`）の削除
- [ ] **コード修正**: `axis.py`, `combination.py` の手動ライブラリロード処理の削除
- [ ] **依存関係調整**: `requirements.txt` に `scikit-learn` を追加（`libgomp` 依存解決のため）
- [ ] **デプロイ**: `vercel deploy --force` によるクリーンビルド

### 3. 動作確認
- [ ] プレビュー環境での予測実行（N3/N4）
- [ ] エラーログの確認（500エラー、ImportErrorがないこと）
- [ ] 本番環境（Production）への昇格

## 関連ドキュメント
- [CUBE生成ルール](../01_design/CUBE生成ルール.md): 実装済みの仕様
