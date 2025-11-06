#!/usr/bin/env python3
"""
TODOディレクトリの再整理スクリプト（todo-new版）
既存のファイルを読み込んで、新しい構造（docs/todo-new/）にコピーします。
"""

import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TODO_DIR = PROJECT_ROOT / "docs" / "todo"
TODO_NEW_DIR = PROJECT_ROOT / "docs" / "todo-new"

# 新しいディレクトリ構造
NEW_STRUCTURE = {
    "00_project-status": [
        "README.md",
        "現在のフェーズ.md",
        "進捗状況サマリー.md",
        "移行計画.md",
    ],
    "01_current-tasks/ai-improvement": [
        "03-01_Weights & Biases導入とセットアップ.md",
        "03-02_特徴量エンジニアリング実験.md",
        "03-03_ハイパーパラメータチューニング.md",
        "03-04_アンサンブル学習の検証.md",
    ],
    "01_current-tasks/data-infrastructure": [
        "02-01_Supabase環境構築とテーブル設計.md",
        "02-02_CSVデータのマイグレーション.md",
        "02-03_データ取得ロジックの書き換え.md",
        "02-04_学習データ範囲の選定と再学習.md",
        "学習データ範囲の選択肢.md",
        "学習管理方法のアドバイス.md",
        "学習進捗サマリー.md",
    ],
    "02_future-tasks/microservices": [
        "README.md",
        "04-01_Dockerコンテナ化とGCP Cloud Run準備.md",
        "04-02_パターンB（0あり）実装.md",
        "04-03_マイクロサービス統合.md",
    ],
    "02_future-tasks/operations": [
        "07-01_CI/CDパイプライン構築.md",
        "07-02_セキュリティ対策実装.md",
        "07-03_モニタリングとログ管理.md",
    ],
    "99_completed/mvp-foundation": [
        "01-01_プロジェクトセットアップと環境構築.md",
        "01-02_データファイル準備.md",
        "01-03_予測表生成アルゴリズム実装.md",
        "01-04_AIモデル構築と学習.md",
        "01-05_バックエンドAPI開発.md",
        "01-06_フロントエンドUI実装.md",
        "01-07_デプロイと動作確認.md",
    ],
    "99_completed/frontend-development": [
        "05-01_共通UIコンポーネント実装.md",
        "05-02_画面実装とルーティング.md",
        "05-03_状態管理とAPI連携.md",
    ],
    "99_completed/backend-api": [
        "06-01_Next.js API Routes実装.md",
        "06-02_FastAPI AI推論エンジン実装.md",
    ],
}

# ファイルの元の場所を定義
SOURCE_MAPPING = {
    # プロジェクトステータス関連（既に作成済み）
    "00_project-status/README.md": TODO_DIR / "00_project-status" / "README.md",
    "00_project-status/現在のフェーズ.md": TODO_DIR / "00_project-status" / "現在のフェーズ.md",
    "00_project-status/進捗状況サマリー.md": TODO_DIR / "00_project-status" / "進捗状況サマリー.md",
    "00_project-status/移行計画.md": TODO_DIR / "00_project-status" / "移行計画.md",
    
    # AI改善タスク
    "01_current-tasks/ai-improvement/03-01_Weights & Biases導入とセットアップ.md": TODO_DIR / "03_ai-improvement" / "03-01_Weights & Biases導入とセットアップ.md",
    "01_current-tasks/ai-improvement/03-02_特徴量エンジニアリング実験.md": TODO_DIR / "03_ai-improvement" / "03-02_特徴量エンジニアリング実験.md",
    "01_current-tasks/ai-improvement/03-03_ハイパーパラメータチューニング.md": TODO_DIR / "03_ai-improvement" / "03-03_ハイパーパラメータチューニング.md",
    "01_current-tasks/ai-improvement/03-04_アンサンブル学習の検証.md": TODO_DIR / "03_ai-improvement" / "03-04_アンサンブル学習の検証.md",
    
    # データインフラタスク
    "01_current-tasks/data-infrastructure/02-01_Supabase環境構築とテーブル設計.md": TODO_DIR / "02_data-infrastructure" / "02-01_Supabase環境構築とテーブル設計.md",
    "01_current-tasks/data-infrastructure/02-02_CSVデータのマイグレーション.md": TODO_DIR / "02_data-infrastructure" / "02-02_CSVデータのマイグレーション.md",
    "01_current-tasks/data-infrastructure/02-03_データ取得ロジックの書き換え.md": TODO_DIR / "02_data-infrastructure" / "02-03_データ取得ロジックの書き換え.md",
    "01_current-tasks/data-infrastructure/02-04_学習データ範囲の選定と再学習.md": TODO_DIR / "02_data-infrastructure" / "02-04_学習データ範囲の選定と再学習.md",
    "01_current-tasks/data-infrastructure/学習データ範囲の選択肢.md": TODO_DIR / "02_data-infrastructure" / "学習データ範囲の選択肢.md",
    "01_current-tasks/data-infrastructure/学習管理方法のアドバイス.md": TODO_DIR / "02_data-infrastructure" / "学習管理方法のアドバイス.md",
    "01_current-tasks/data-infrastructure/学習進捗サマリー.md": TODO_DIR / "02_data-infrastructure" / "学習進捗サマリー.md",
    
    # マイクロサービスタスク
    "02_future-tasks/microservices/README.md": TODO_DIR / "04_microservices" / "README.md",
    "02_future-tasks/microservices/04-01_Dockerコンテナ化とGCP Cloud Run準備.md": TODO_DIR / "04_microservices" / "04-01_Dockerコンテナ化とGCP Cloud Run準備.md",
    "02_future-tasks/microservices/04-02_パターンB（0あり）実装.md": TODO_DIR / "04_microservices" / "04-02_パターンB（0あり）実装.md",
    "02_future-tasks/microservices/04-03_マイクロサービス統合.md": TODO_DIR / "04_microservices" / "04-03_マイクロサービス統合.md",
    
    # 運用タスク
    "02_future-tasks/operations/07-01_CI/CDパイプライン構築.md": TODO_DIR / "07_cicd-operations" / "07-01_CI/CDパイプライン構築.md",
    "02_future-tasks/operations/07-02_セキュリティ対策実装.md": TODO_DIR / "07_cicd-operations" / "07-02_セキュリティ対策実装.md",
    "02_future-tasks/operations/07-03_モニタリングとログ管理.md": TODO_DIR / "07_cicd-operations" / "07-03_モニタリングとログ管理.md",
    
    # MVP基盤構築タスク
    "99_completed/mvp-foundation/01-01_プロジェクトセットアップと環境構築.md": TODO_DIR / "01_mvp-foundation" / "01-01_プロジェクトセットアップと環境構築.md",
    "99_completed/mvp-foundation/01-02_データファイル準備.md": TODO_DIR / "01_mvp-foundation" / "01-02_データファイル準備.md",
    "99_completed/mvp-foundation/01-03_予測表生成アルゴリズム実装.md": TODO_DIR / "01_mvp-foundation" / "01-03_予測表生成アルゴリズム実装.md",
    "99_completed/mvp-foundation/01-04_AIモデル構築と学習.md": TODO_DIR / "01_mvp-foundation" / "01-04_AIモデル構築と学習.md",
    "99_completed/mvp-foundation/01-05_バックエンドAPI開発.md": TODO_DIR / "01_mvp-foundation" / "01-05_バックエンドAPI開発.md",
    "99_completed/mvp-foundation/01-06_フロントエンドUI実装.md": TODO_DIR / "01_mvp-foundation" / "01-06_フロントエンドUI実装.md",
    "99_completed/mvp-foundation/01-07_デプロイと動作確認.md": TODO_DIR / "01_mvp-foundation" / "01-07_デプロイと動作確認.md",
    
    # フロントエンド開発タスク
    "99_completed/frontend-development/05-01_共通UIコンポーネント実装.md": TODO_DIR / "05_frontend-development" / "05-01_共通UIコンポーネント実装.md",
    "99_completed/frontend-development/05-02_画面実装とルーティング.md": TODO_DIR / "05_frontend-development" / "05-02_画面実装とルーティング.md",
    "99_completed/frontend-development/05-03_状態管理とAPI連携.md": TODO_DIR / "05_frontend-development" / "05-03_状態管理とAPI連携.md",
    
    # バックエンドAPI開発タスク
    "99_completed/backend-api/06-01_Next.js API Routes実装.md": TODO_DIR / "06_backend-api" / "06-01_Next.js API Routes実装.md",
    "99_completed/backend-api/06-02_FastAPI AI推論エンジン実装.md": TODO_DIR / "06_backend-api" / "06-02_FastAPI AI推論エンジン実装.md",
}

def main():
    """メイン処理"""
    print("=" * 60)
    print("TODOディレクトリの再整理（todo-new版）")
    print("=" * 60)
    
    # 新しいディレクトリを作成
    print("\n1. 新しいディレクトリを作成中...")
    for new_dir in NEW_STRUCTURE.keys():
        target_dir = TODO_NEW_DIR / new_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {target_dir}")
    
    # READMEファイルを作成（既に作成済みのものはスキップ）
    print("\n2. READMEファイルを確認中...")
    # READMEファイルは既に作成済みなので、コピーします
    readme_files = {
        "README.md": TODO_DIR / "README.md",
        "00_project-status/README.md": TODO_DIR / "00_project-status" / "README.md",
        "01_current-tasks/README.md": TODO_DIR / "01_current-tasks" / "README.md",
        "01_current-tasks/ai-improvement/README.md": TODO_DIR / "01_current-tasks" / "ai-improvement" / "README.md",
        "01_current-tasks/data-infrastructure/README.md": TODO_DIR / "01_current-tasks" / "data-infrastructure" / "README.md",
        "02_future-tasks/README.md": TODO_DIR / "02_future-tasks" / "README.md",
        "02_future-tasks/microservices/README.md": TODO_DIR / "02_future-tasks" / "microservices" / "README.md",
        "02_future-tasks/operations/README.md": TODO_DIR / "02_future-tasks" / "operations" / "README.md",
        "99_completed/README.md": TODO_DIR / "99_completed" / "README.md",
    }
    
    for rel_path, source_path in readme_files.items():
        if source_path.exists():
            target_path = TODO_NEW_DIR / rel_path
            shutil.copy2(source_path, target_path)
            print(f"   ✓ {rel_path}")
        else:
            print(f"   ⚠ ファイルが見つかりません: {source_path}")
    
    # ファイルをコピー
    print("\n3. ファイルをコピー中...")
    copied_count = 0
    skipped_count = 0
    error_count = 0
    
    for rel_path, source_path in SOURCE_MAPPING.items():
        target_path = TODO_NEW_DIR / rel_path
        
        if not source_path.exists():
            print(f"   ⚠ ソースファイルが見つかりません: {source_path}")
            skipped_count += 1
            continue
        
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            print(f"   ✓ {rel_path}")
            copied_count += 1
        except Exception as e:
            print(f"   ✗ エラー: {rel_path} - {e}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print("完了レポート")
    print("=" * 60)
    print(f"コピー成功: {copied_count} ファイル")
    print(f"スキップ: {skipped_count} ファイル")
    print(f"エラー: {error_count} ファイル")
    print(f"\n新しい構造は {TODO_NEW_DIR} に作成されました。")
    print("\n次のステップ:")
    print("1. docs/todo-new/ の内容を確認してください")
    print("2. 問題がなければ、docs/todo/ を docs/todo-old/ にリネーム")
    print("3. docs/todo-new/ を docs/todo/ にリネーム")

if __name__ == "__main__":
    main()

