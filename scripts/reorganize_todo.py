#!/usr/bin/env python3
"""
TODOディレクトリの再整理スクリプト

新しい構造に合わせてファイルを移動します。
"""

import os
import shutil
from pathlib import Path

def main():
    """TODOディレクトリを新しい構造に再整理する"""
    base_dir = Path(__file__).parent.parent / 'docs' / 'todo'
    
    # 移動マッピング: (旧パス, 新パス)
    moves = [
        # プロジェクト状況サマリー
        ('進捗状況サマリー.md', '00_project-status/進捗状況サマリー.md'),
        
        # AI精度改善タスク（03_ai-improvement -> 01_current-tasks/ai-improvement）
        ('03_ai-improvement/03-01_Weights & Biases導入とセットアップ.md', '01_current-tasks/ai-improvement/03-01_Weights & Biases導入とセットアップ.md'),
        ('03_ai-improvement/03-02_特徴量エンジニアリング実験.md', '01_current-tasks/ai-improvement/03-02_特徴量エンジニアリング実験.md'),
        ('03_ai-improvement/03-03_ハイパーパラメータチューニング.md', '01_current-tasks/ai-improvement/03-03_ハイパーパラメータチューニング.md'),
        ('03_ai-improvement/03-04_アンサンブル学習の検証.md', '01_current-tasks/ai-improvement/03-04_アンサンブル学習の検証.md'),
        
        # データ管理タスク（02_data-infrastructure -> 01_current-tasks/data-infrastructure）
        ('02_data-infrastructure/02-01_Supabase環境構築とテーブル設計.md', '01_current-tasks/data-infrastructure/02-01_Supabase環境構築とテーブル設計.md'),
        ('02_data-infrastructure/02-02_CSVデータのマイグレーション.md', '01_current-tasks/data-infrastructure/02-02_CSVデータのマイグレーション.md'),
        ('02_data-infrastructure/02-03_データ取得ロジックの書き換え.md', '01_current-tasks/data-infrastructure/02-03_データ取得ロジックの書き換え.md'),
        ('02_data-infrastructure/02-04_学習データ範囲の選定と再学習.md', '01_current-tasks/data-infrastructure/02-04_学習データ範囲の選定と再学習.md'),
        ('02_data-infrastructure/学習データ範囲の選択肢.md', '01_current-tasks/data-infrastructure/学習データ範囲の選択肢.md'),
        ('02_data-infrastructure/学習管理方法のアドバイス.md', '01_current-tasks/data-infrastructure/学習管理方法のアドバイス.md'),
        ('02_data-infrastructure/学習進捗サマリー.md', '01_current-tasks/data-infrastructure/学習進捗サマリー.md'),
        
        # マイクロサービス化タスク（04_microservices -> 02_future-tasks/microservices）
        ('04_microservices/04-01_Dockerコンテナ化とGCP Cloud Run準備.md', '02_future-tasks/microservices/04-01_Dockerコンテナ化とGCP Cloud Run準備.md'),
        ('04_microservices/04-02_パターンB（0あり）実装.md', '02_future-tasks/microservices/04-02_パターンB（0あり）実装.md'),
        ('04_microservices/04-03_マイクロサービス統合.md', '02_future-tasks/microservices/04-03_マイクロサービス統合.md'),
        ('04_microservices/README.md', '02_future-tasks/microservices/README.md'),
        
        # CI/CD・運用タスク（07_cicd-operations -> 02_future-tasks/operations）
        ('07_cicd-operations/07-01_CI/CDパイプライン構築.md', '02_future-tasks/operations/07-01_CI-CDパイプライン構築.md'),
        ('07_cicd-operations/07-02_セキュリティ対策実装.md', '02_future-tasks/operations/07-02_セキュリティ対策実装.md'),
        ('07_cicd-operations/07-03_モニタリングとログ管理.md', '02_future-tasks/operations/07-03_モニタリングとログ管理.md'),
        
        # MVP基盤構築タスク（01_mvp-foundation -> 99_completed/mvp-foundation）
        ('01_mvp-foundation/01-01_プロジェクトセットアップと環境構築.md', '99_completed/mvp-foundation/01-01_プロジェクトセットアップと環境構築.md'),
        ('01_mvp-foundation/01-02_データファイル準備.md', '99_completed/mvp-foundation/01-02_データファイル準備.md'),
        ('01_mvp-foundation/01-03_予測表生成アルゴリズム実装.md', '99_completed/mvp-foundation/01-03_予測表生成アルゴリズム実装.md'),
        ('01_mvp-foundation/01-04_AIモデル構築と学習.md', '99_completed/mvp-foundation/01-04_AIモデル構築と学習.md'),
        ('01_mvp-foundation/01-05_バックエンドAPI開発.md', '99_completed/mvp-foundation/01-05_バックエンドAPI開発.md'),
        ('01_mvp-foundation/01-06_フロントエンドUI実装.md', '99_completed/mvp-foundation/01-06_フロントエンドUI実装.md'),
        ('01_mvp-foundation/01-07_デプロイと動作確認.md', '99_completed/mvp-foundation/01-07_デプロイと動作確認.md'),
        
        # フロントエンド開発タスク（05_frontend-development -> 99_completed/frontend-development）
        ('05_frontend-development/05-01_共通UIコンポーネント実装.md', '99_completed/frontend-development/05-01_共通UIコンポーネント実装.md'),
        ('05_frontend-development/05-02_画面実装とルーティング.md', '99_completed/frontend-development/05-02_画面実装とルーティング.md'),
        ('05_frontend-development/05-03_状態管理とAPI連携.md', '99_completed/frontend-development/05-03_状態管理とAPI連携.md'),
        
        # バックエンドAPI開発タスク（06_backend-api -> 99_completed/backend-api）
        ('06_backend-api/06-01_Next.js API Routes実装.md', '99_completed/backend-api/06-01_Next.js API Routes実装.md'),
        ('06_backend-api/06-02_FastAPI AI推論エンジン実装.md', '99_completed/backend-api/06-02_FastAPI AI推論エンジン実装.md'),
    ]
    
    print("TODOディレクトリの再整理を開始します...")
    print(f"ベースディレクトリ: {base_dir}")
    
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    for old_path, new_path in moves:
        old_file = base_dir / old_path
        new_file = base_dir / new_path
        
        if not old_file.exists():
            print(f"⚠️  スキップ（ファイルが見つかりません）: {old_path}")
            skipped_count += 1
            continue
        
        # 新しいディレクトリを作成
        new_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # ファイルを移動
            shutil.move(str(old_file), str(new_file))
            print(f"✅ 移動完了: {old_path} -> {new_path}")
            moved_count += 1
        except Exception as e:
            print(f"❌ エラー: {old_path} -> {new_path}: {e}")
            error_count += 1
    
    print("\n" + "="*60)
    print(f"移動完了: {moved_count}件")
    print(f"スキップ: {skipped_count}件")
    print(f"エラー: {error_count}件")
    print("="*60)
    
    # 空になった古いディレクトリを削除
    old_dirs = [
        '01_mvp-foundation',
        '02_data-infrastructure',
        '03_ai-improvement',
        '04_microservices',
        '05_frontend-development',
        '06_backend-api',
        '07_cicd-operations',
    ]
    
    print("\n空になった古いディレクトリを削除します...")
    for old_dir in old_dirs:
        old_dir_path = base_dir / old_dir
        if old_dir_path.exists():
            try:
                # ディレクトリが空か確認
                if not any(old_dir_path.iterdir()):
                    old_dir_path.rmdir()
                    print(f"✅ 削除完了: {old_dir}")
                else:
                    print(f"⚠️  スキップ（ディレクトリが空ではありません）: {old_dir}")
            except Exception as e:
                print(f"❌ エラー（削除失敗）: {old_dir}: {e}")

if __name__ == '__main__':
    main()

