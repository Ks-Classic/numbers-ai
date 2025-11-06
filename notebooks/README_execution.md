# Notebooksスクリプト実行方法

## 仮想環境のセットアップ

このディレクトリにはすでに仮想環境（`venv`）が作成されています。

## 実行方法

### 方法1: 仮想環境をアクティベートしてから実行（推奨）

```bash
cd notebooks
source venv/bin/activate  # 仮想環境をアクティベート
python3 run_01_data_preparation.py
deactivate  # 終了後、仮想環境を無効化（オプション）
```

### 方法2: 仮想環境のPythonを直接使用

```bash
cd notebooks
./venv/bin/python3 run_01_data_preparation.py
```

または

```bash
cd notebooks
notebooks/venv/bin/python3 run_01_data_preparation.py
```

## 依存関係のインストール

仮想環境内に依存関係がインストールされていない場合は、以下のコマンドでインストールできます：

```bash
cd notebooks
source venv/bin/activate
pip install -r requirements.txt
```

## トラブルシューティング

### ModuleNotFoundError: No module named 'pandas'

このエラーが発生する場合は、仮想環境がアクティベートされていない可能性があります。

**解決方法:**
```bash
# 仮想環境をアクティベート
source venv/bin/activate

# 実行
python3 run_01_data_preparation.py
```

### 仮想環境が見つからない場合

新しい仮想環境を作成する場合：

```bash
cd notebooks
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

