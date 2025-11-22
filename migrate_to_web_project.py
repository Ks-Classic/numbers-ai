
import os
import shutil
import sys

def copy_file(src, dest):
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        print(f"Copied: {src} -> {dest}")
    except Exception as e:
        print(f"Error copying {src}: {e}")

def main():
    # ソースディレクトリ（現在のプロジェクト）
    source_dir = os.getcwd()
    # ターゲットディレクトリ（新しいWebプロジェクト）
    # 注: ユーザーのホームディレクトリ直下に作成することを想定
    target_dir = os.path.join(os.path.dirname(source_dir), "numbers-ai-cube")

    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")

    if not os.path.exists(target_dir):
        print(f"Target directory does not exist. Please create it first or run create-next-app.")
        # ここではディレクトリ作成は行わず、ファイルのリストアップのみ行うか、
        # ユーザーにプロジェクト作成を促す
        return

    # 移行対象のファイルリスト
    # 1. CUBE生成ロジック
    cube_logic_files = [
        "src/lib/cube-generator/chart-generator.ts",
        "src/lib/cube-generator/extreme-cube.ts",
        "src/lib/cube-generator/index.ts",
        "src/lib/cube-generator/keisen-master-loader.ts",
        "src/lib/cube-generator/types.ts",
        "src/lib/data-loader/index.ts",
        "src/lib/data-loader/types.ts",
        "src/lib/data-loader/past-results.ts",
        "src/lib/data-loader/keisen-master.ts",
        "src/lib/data-loader/github-data.ts",
        "src/lib/utils.ts",
    ]

    # 2. API Route
    api_files = [
        "src/app/api/cube/[roundNumber]/route.ts",
        "src/app/api/check-data-status/route.ts",
    ]

    # 3. ページコンポーネント
    page_files = [
        "src/app/cube/page.tsx",
        "src/app/page.tsx", # トップページも必要なら
        "src/app/layout.tsx", # レイアウトも
        "src/app/globals.css", # CSSも
    ]
    
    # 4. コンポーネント
    component_files = [
        # 必要に応じて追加
    ]

    # 5. データファイル
    data_files = [
        "data/keisen_master_new.json",
        "data/past_results.csv",
    ]

    # 6. 設定ファイル
    config_files = [
        "tailwind.config.ts",
        "postcss.config.mjs",
        "tsconfig.json",
        "next.config.ts",
    ]

    all_files = cube_logic_files + api_files + page_files + component_files + data_files + config_files

    for file_path in all_files:
        src_path = os.path.join(source_dir, file_path)
        dest_path = os.path.join(target_dir, file_path)
        
        if os.path.exists(src_path):
            copy_file(src_path, dest_path)
        else:
            print(f"Skipping (not found): {src_path}")

if __name__ == "__main__":
    main()
