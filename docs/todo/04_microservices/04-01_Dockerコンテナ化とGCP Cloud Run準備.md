# 04-01 Dockerコンテナ化とGCP Cloud Run準備

## 概要
FastAPI AIエンジンをDockerコンテナ化し、GCP Cloud Runへのデプロイ準備を行う。

## 詳細タスク

- [ ] Dockerfileを作成する
  - api/Dockerfileを作成する
  - ベースイメージを選択する（python:3.10-slim等）
  - 依存関係をインストールする処理を実装する
  - アプリケーションファイルをコピーする処理を実装する
  - ポートを公開する処理を実装する
  - CMDを設定する

- [ ] .dockerignoreを作成する
  - 不要なファイルを除外する設定を追加する
  - __pycache__を除外する
  - .gitを除外する
  - その他、不要なファイルを除外する

- [ ] Dockerイメージをビルドする
  - ローカルでDockerイメージをビルドする
  - ビルドエラーを修正する
  - イメージサイズを確認する

- [ ] Dockerコンテナをテストする
  - ローカルでDockerコンテナを起動する
  - APIが正常に動作することを確認する
  - ヘルスチェックエンドポイントを確認する

- [ ] GCPプロジェクトを作成する
  - GCPアカウントにログインする
  - 新しいプロジェクトを作成する
  - プロジェクトIDを設定する

- [ ] Cloud Run APIを有効化する
  - GCPコンソールでCloud Run APIを有効化する
  - 必要な権限を確認する

- [ ] gcloud CLIをセットアップする
  - gcloud CLIをインストールする
  - gcloud auth loginを実行する
  - プロジェクトを設定する

- [ ] DockerイメージをGCP Container Registryにプッシュする
  - Container Registryに接続する設定をする
  - Dockerイメージをタグ付けする
  - docker pushを実行する

- [ ] Cloud Runサービスを作成する
  - gcloud run deployコマンドを実行する
  - リージョンを設定する
  - メモリとCPUを設定する
  - タイムアウトを設定する

- [ ] Cloud Runサービスをテストする
  - デプロイされたサービスのURLを確認する
  - APIが正常に動作することを確認する
  - レスポンスタイムを測定する
