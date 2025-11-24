# notebooksフォルダ構成のベストプラクティス

## 📋 一般的なベストプラクティス

### ✅ notebooksフォルダに置くべきファイル

**Jupyter Notebookファイルとその実行スクリプトのみ**を置くのが一般的です：

```
notebooks/
├── *.ipynb              # Jupyter Notebookファイル
├── run_*.py             # Notebook実行スクリプト
├── README.md            # ドキュメント（任意）
└── requirements.txt     # 依存関係（任意、プロジェクトルートと統合推奨）
```

### ❌ notebooksフォルダに置くべきでないもの

以下のディレクトリ・ファイルは**notebooksフォルダ内に置かない**のが一般的です：

#### 1. **`venv/`（仮想環境）**

**理由：**
- 仮想環境は**プロジェクト全体で共有**すべき
- 複数の`venv/`が存在すると依存関係の管理が複雑になる
- Git管理対象外（`.gitignore`で無視）

**推奨構成：**
```
プロジェクトルート/
├── venv/              # プロジェクト全体の仮想環境（1つだけ）
├── notebooks/
│   └── *.ipynb
└── scripts/
    └── *.py
```

**現在の状況：**
- ✅ `notebooks/venv/` - **削除済み**（2024年整理）
- ❌ `api/venv/` - 削除推奨
- ❌ `scripts/venv/` - 削除推奨
- ✅ `プロジェクトルート/venv/` - これだけ残す

#### 2. **`data/`（データディレクトリ）**

**理由：**
- データは**プロジェクト全体で共有**すべき
- 複数の`data/`が存在するとデータの整合性が保てない
- パスの混乱を招く（`notebooks/data/` vs `プロジェクトルート/data/`）

**推奨構成：**
```
プロジェクトルート/
├── data/              # プロジェクト全体のデータ（1つだけ）
│   ├── models/
│   ├── past_results.csv
│   └── ...
├── notebooks/
│   └── *.ipynb        # データは相対パスで ../data/ を参照
└── scripts/
    └── *.py           # データは相対パスで ../data/ を参照
```

**現在の状況：**
- ✅ `notebooks/data/` - **削除済み**（2024年整理）
- ✅ `プロジェクトルート/data/` - これだけ残す

#### 3. **`__pycache__/`（Pythonキャッシュ）**

**理由：**
- 自動生成されるファイル（削除しても問題なし）
- `.gitignore`で無視されるべき
- 各ディレクトリに自動生成されるため、notebooks内に特別に置く必要はない

**推奨対応：**
- `.gitignore`で無視（既に対応済み）
- 必要に応じて削除可能：`find . -type d -name __pycache__ -exec rm -r {} +`

## ✅ 整理完了（2024年実施）

以下の整理が完了しました：

1. **`notebooks/venv/`を削除** - プロジェクトルートの`venv/`を使用
2. **`notebooks/data/`を削除** - プロジェクトルートの`data/`を使用
3. **`notebooks/__pycache__/`を削除** - 自動生成されるため不要

整理後のnotebooksフォルダ構成：
```
notebooks/
├── *.ipynb              # Jupyter Notebookファイル（5ファイル）
├── run_*.py             # Notebook実行スクリプト（6ファイル）
├── README.md            # ドキュメント
├── requirements.txt     # 依存関係
└── *.log, *.txt         # ログファイル
```

## 🔄 推奨される整理手順

### ステップ1: `venv/`の統合

```bash
# notebooks/venv/を削除（プロジェクトルートのvenvを使用）
rm -rf notebooks/venv/

# プロジェクトルートのvenvを有効化して使用
source venv/bin/activate  # または python3 -m venv venv（新規作成時）
```

### ステップ2: `data/`の統合

```bash
# notebooks/data/models/の内容を確認
ls notebooks/data/models/

# プロジェクトルートのdata/models/に移動（重複確認）
# 注意: 既存ファイルを上書きしないよう注意
cp -r notebooks/data/models/* data/models/  # 必要に応じて

# notebooks/data/を削除
rm -rf notebooks/data/
```

### ステップ3: パスの確認

notebooks内のスクリプトが正しくプロジェクトルートの`data/`を参照しているか確認：

```python
# 正しいパス設定（既に実装済み）
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'  # ✅ プロジェクトルートのdata/
```

## 📊 整理後の理想的な構成

```
numbers-ai/
├── venv/                    # プロジェクト全体の仮想環境（1つだけ）
├── data/                    # プロジェクト全体のデータ（1つだけ）
│   ├── models/
│   ├── past_results.csv
│   └── ...
├── core/                    # コアモジュール
├── scripts/                 # スクリプト
│   ├── production/
│   └── tools/
└── notebooks/              # Jupyter Notebookのみ
    ├── *.ipynb
    ├── run_*.py
    ├── README.md
    └── requirements.txt    # 任意（プロジェクトルートと統合推奨）
```

## 🎯 メリット

### 1. **依存関係の一元管理**
- 1つの`venv/`で全プロジェクトの依存関係を管理
- バージョン競合のリスクを低減

### 2. **データの整合性**
- 1つの`data/`で全プロジェクトのデータを管理
- データの重複や不整合を防止

### 3. **パスの明確化**
- 相対パスが明確（`../data/`でプロジェクトルートのdataを参照）
- パスの混乱を防止

### 4. **Git管理の簡素化**
- `.gitignore`で`venv/`と`__pycache__/`を無視
- 不要なファイルをGitに含めない

## ⚠️ 注意事項

### 仮想環境の統合時の注意

複数の`venv/`が存在する場合、依存関係が異なる可能性があります：

```bash
# 各venvのrequirements.txtを確認
diff notebooks/venv/requirements.txt venv/requirements.txt

# 統合前に依存関係を確認
pip freeze > requirements_all.txt
```

### データの統合時の注意

`notebooks/data/models/`と`data/models/`に同じファイルが存在する場合：

```bash
# ファイルの重複を確認
diff notebooks/data/models/ data/models/

# 必要に応じてバックアップ
cp -r notebooks/data/models/ notebooks/data/models_backup/
```

## 📚 参考資料

- [Pythonプロジェクト構造のベストプラクティス](https://docs.python-guide.org/writing/structure/)
- [Jupyter Notebookベストプラクティス](https://www.dataquest.io/blog/jupyter-notebook-tips-tricks-shortcuts/)
- [仮想環境の使い方とベストプラクティス](../SETUP_VENV.md)

