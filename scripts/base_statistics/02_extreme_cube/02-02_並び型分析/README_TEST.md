# 並び型判定スクリプトのテスト実行方法

## 前提条件

- Python 3.8以上
- 必要なパッケージがインストールされていること（pandas, numpyなど）

## テストの実行方法

### 方法1: unittestモジュールを使用（推奨）

pytestは不要です。Python標準の`unittest`モジュールを使用しています。

```bash
# プロジェクトルートから実行
cd /path/to/numbers-ai

# venvを有効化（存在する場合）
source venv/bin/activate

# テストを実行
python -m unittest scripts.base_statistics.02_extreme_cube.02-02_並び型分析.test_pattern_classifier -v
```

### 方法2: テストファイルを直接実行（推奨）

```bash
# プロジェクトルートから実行
cd /path/to/numbers-ai

# venvを有効化（存在する場合）
source venv/bin/activate

# PYTHONPATHを設定してテストファイルを直接実行
PYTHONPATH=/path/to/numbers-ai/core:/path/to/numbers-ai/scripts/production python scripts/base_statistics/02_extreme_cube/02-02_並び型分析/test_pattern_classifier.py
```

または、プロジェクトルートにいる場合：

```bash
cd /home/ykoha/numbers-ai
source venv/bin/activate
PYTHONPATH=/home/ykoha/numbers-ai/core:/home/ykoha/numbers-ai/scripts/production python scripts/base_statistics/02_extreme_cube/02-02_並び型分析/test_pattern_classifier.py
```

### 方法3: シェルスクリプトを使用

```bash
# 実行権限を付与（初回のみ）
chmod +x scripts/base_statistics/02_extreme_cube/02-02_並び型分析/run_tests.sh

# スクリプトを実行
./scripts/base_statistics/02_extreme_cube/02-02_並び型分析/run_tests.sh
```

## venvの設定方法

### venvが存在しない場合

```bash
# プロジェクトルートで実行
python3 -m venv venv

# venvを有効化
source venv/bin/activate

# 必要なパッケージをインストール
pip install -r requirements.txt
```

### venvが既に存在する場合

```bash
# venvを有効化
source venv/bin/activate

# パッケージが不足している場合はインストール
pip install -r requirements.txt
```

## テスト内容

以下のテストクラスが含まれています：

- `TestConnectionFunctions`: つながりの判定関数のテスト
- `TestBasicPatterns`: 基本型（横一文字型、縦一文字型、V字型、逆V字型）のテスト
- `TestDiagonalPatterns`: 斜め型（4種類）のテスト
- `TestLShapePatterns`: L字型（4種類）のテスト
- `TestZigzagPatterns`: ジグザグ型（2種類）のテスト
- `TestCornerPatterns`: コーナー型（8種類）のテスト
- `TestClassifyPattern`: `classify_pattern()`関数の統合テスト（全22種類の型をテスト）

## トラブルシューティング

### ImportErrorが発生する場合

プロジェクトルートから実行していることを確認してください。

```bash
# プロジェクトルートに移動
cd /path/to/numbers-ai

# 再度実行
python -m unittest scripts.base_statistics.02_extreme_cube.02-02_並び型分析.test_pattern_classifier -v
```

### モジュールが見つからない場合

必要なパッケージがインストールされているか確認してください。

```bash
# venvを有効化
source venv/bin/activate

# パッケージをインストール
pip install pandas numpy
```

