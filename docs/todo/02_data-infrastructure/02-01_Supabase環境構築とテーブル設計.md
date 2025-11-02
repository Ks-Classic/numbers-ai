# 02-01 Supabase環境構築とテーブル設計

## 概要
Supabaseプロジェクトを作成し、PostgreSQLデータベースのテーブル設計とマイグレーションを実装する。

## 詳細タスク

- [ ] Supabaseプロジェクトを作成する
  - Supabaseアカウントにログインする
  - 新しいプロジェクトを作成する
  - プロジェクト名とリージョンを設定する
  - データベースパスワードを設定する

- [ ] データベース接続情報を確認する
  - Supabaseダッシュボードで接続情報を取得する
  - PostgreSQL接続文字列を確認する
  - APIキー（anon key, service role key）を確認する

- [ ] past_resultsテーブルを作成する
  - SQLマイグレーションファイルを作成する
  - idカラムを定義する（SERIAL PRIMARY KEY）
  - round_numberカラムを定義する（INTEGER NOT NULL UNIQUE）
  - draw_dateカラムを定義する（DATE NOT NULL）
  - n3_winningカラムを定義する（CHAR(3) NOT NULL）
  - n4_winningカラムを定義する（CHAR(4) NOT NULL）
  - n3_rehearsalカラムを定義する（CHAR(3) NULL可）
  - n4_rehearsalカラムを定義する（CHAR(4) NULL可）
  - created_atカラムを定義する（TIMESTAMP WITH TIME ZONE DEFAULT NOW()）
  - updated_atカラムを定義する（TIMESTAMP WITH TIME ZONE DEFAULT NOW()）
  - インデックスを作成する（round_number, draw_date）

- [ ] generated_chartsテーブルを作成する
  - SQLマイグレーションファイルを作成する
  - idカラムを定義する（SERIAL PRIMARY KEY）
  - round_numberカラムを定義する（INTEGER NOT NULL）
  - targetカラムを定義する（VARCHAR(2) NOT NULL、'n3' or 'n4'）
  - patternカラムを定義する（CHAR(1) NOT NULL、'A' or 'B'）
  - chart_dataカラムを定義する（JSONB NOT NULL）
  - source_digitsカラムを定義する（INTEGER[] NOT NULL）
  - generated_atカラムを定義する（TIMESTAMP WITH TIME ZONE DEFAULT NOW()）
  - UNIQUE制約を追加する（round_number, target, pattern）
  - インデックスを作成する（round_number）

- [ ] マイグレーションスクリプトを作成する
  - migrations/ディレクトリを作成する
  - 001_create_past_results_table.sqlを作成する
  - 002_create_generated_charts_table.sqlを作成する
  - マイグレーション実行手順をドキュメント化する

- [ ] Supabaseクライアントライブラリをインストールする
  - @supabase/supabase-jsをインストールする
  - @supabase/ssrをインストールする（Next.js用）
  - パッケージのバージョンを確認する

- [ ] 環境変数を設定する
  - .env.localにSupabase接続情報を追加する
  - NEXT_PUBLIC_SUPABASE_URLを設定する
  - NEXT_PUBLIC_SUPABASE_ANON_KEYを設定する
  - .env.local.exampleを更新する

- [ ] Supabaseクライアントを作成する
  - src/lib/supabase/client.tsを作成する
  - createClient関数を実装する
  - シングルトンパターンで実装する

- [ ] データベース接続テストを実装する
  - 接続テスト用のスクリプトを作成する
  - テーブルが存在することを確認する
  - クエリが正常に実行されることを確認する
