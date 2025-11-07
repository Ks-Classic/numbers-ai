# 仮想環境（venv）の使い方とベストプラクティス

## 📚 一般的なベストプラクティス

### ✅ 仮想環境の有効化は**ターミナルセッションごと**に必要

**重要なポイント：**
- **新しいターミナルを開くたびに**`source venv/bin/activate`を実行する必要がある
- 仮想環境の有効化は**ターミナルセッション内でのみ有効**
- ターミナルを閉じると、仮想環境は自動的に無効化される

### 🔄 なぜ毎回必要？

仮想環境の有効化は、**環境変数（PATH）を変更する**だけです：

```bash
# 有効化前
$ which python3
/usr/bin/python3  # システムのPython

# 有効化後
$ source venv/bin/activate
(venv) $ which python3
/home/ykoha/numbers-ai/venv/bin/python3  # 仮想環境のPython
```

この変更は**そのターミナルセッション内でのみ有効**です。新しいターミナルを開くと、環境変数はリセットされるため、再度有効化が必要です。

### 💡 一般的な使い方

#### 1. **ターミナルで作業する場合**

```bash
# プロジェクトディレクトリに移動
cd /path/to/project

# 仮想環境を有効化（毎回必要）
source venv/bin/activate

# プロンプトが (venv) に変わる
(venv) $ python script.py

# 作業終了後（オプション）
deactivate
```

#### 2. **IDE（VS Code/Cursor）で作業する場合**

**自動的に有効化される：**
- `.vscode/settings.json`で`python.defaultInterpreterPath`を設定すると、IDEが自動的にそのPythonを使用
- ターミナルをIDE内で開くと、自動的に有効化される場合がある（設定による）

**手動で選択する場合：**
- コマンドパレット（Ctrl+Shift+P）→「Python: Select Interpreter」
- プロジェクトの`venv/bin/python3`を選択

#### 3. **スクリプトから直接実行する場合**

仮想環境を有効化せずに、直接パスを指定：

```bash
# 仮想環境のPythonを直接使用
./venv/bin/python3 script.py

# または絶対パス
/home/ykoha/numbers-ai/venv/bin/python3 script.py
```

## 🎯 このプロジェクトでの推奨設定

### 現在の状況

- ✅ **プロジェクトルートに`venv/`が存在**
- ✅ `venv/bin/python3`が存在
- ✅ `venv/bin/activate`が存在（再作成済み）
- ✅ `.vscode/settings.json`でシステムのPythonが設定済み（venv使用も可能）

### 推奨される設定

#### オプション1: システムのPythonを使用（**現在の設定・推奨**）

**メリット：**
- 仮想環境の管理が不要
- 設定がシンプル
- WSL環境ではシステムのPythonが安定している
- 依存関係の競合が少ない

**設定：**
```json
{
  "python.defaultInterpreterPath": "/usr/bin/python3"
}
```

**使い方：**
- IDEでは自動的にシステムのPythonを使用
- ターミナルでは`python3`コマンドを直接使用
- **仮想環境の有効化は不要**

**依存関係のインストール：**
```bash
# システム全体にインストール（推奨しない）
sudo pip3 install -r notebooks/requirements.txt

# またはユーザー領域にインストール（推奨）
pip3 install --user -r notebooks/requirements.txt
pip3 install --user -r scripts/requirements.txt
pip3 install --user -r api/requirements.txt
```

#### オプション2: プロジェクトのvenvを作成する場合

**メリット：**
- 依存関係をプロジェクトごとに管理できる
- バージョン競合を防げる
- 本番環境との整合性が取れる

**設定手順：**

1. **venvを作成**
```bash
cd /home/ykoha/numbers-ai
python3 -m venv venv
```

2. **依存関係をインストール**
```bash
source venv/bin/activate
pip install -r notebooks/requirements.txt
pip install -r scripts/requirements.txt
pip install -r api/requirements.txt
```

3. **VS Code/Cursorの設定を更新**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python3",
  "python.terminal.activateEnvironment": true
}
```

4. **使い方**
```bash
# ターミナルで作業する場合
source venv/bin/activate  # 毎回必要

# IDEでは自動的に有効化される（設定済みの場合）
```

**注意：** 現在はシステムのPythonを使用しているため、venvは**オプション**です。

## 🔧 便利な設定

### 1. **シェルの設定ファイルにエイリアスを追加**

`~/.bashrc`または`~/.zshrc`に追加：

```bash
# プロジェクトディレクトリに移動してvenvを有効化
alias venv-activate='cd /home/ykoha/numbers-ai && source venv/bin/activate'
```

使い方：
```bash
venv-activate  # プロジェクトに移動してvenvを有効化
```

### 2. **direnvを使用（高度）**

プロジェクトディレクトリに入ると自動的にvenvを有効化：

```bash
# direnvをインストール
sudo apt install direnv

# .envrcを作成
echo "source venv/bin/activate" > .envrc
direnv allow
```

### 3. **VS Code/Cursorの自動有効化**

`.vscode/settings.json`で設定：

```json
{
  "python.terminal.activateEnvironment": true,
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python3"
}
```

これで、VS Code/Cursor内のターミナルを開くと自動的にvenvが有効化されます。

## 📊 まとめ

| 方法 | 有効化のタイミング | メリット | デメリット |
|------|------------------|---------|-----------|
| **ターミナルで手動** | 毎回`source venv/bin/activate` | シンプル、明示的 | 毎回必要 |
| **IDE設定** | IDE起動時に自動 | 自動化、便利 | 設定が必要 |
| **直接パス指定** | 不要 | 確実 | パスが長い |
| **direnv** | ディレクトリ移動時に自動 | 完全自動化 | 追加ツール必要 |

## ⚠️ 注意事項

1. **プロジェクトごとにvenvを分ける**
   - 異なるプロジェクトで同じvenvを使わない
   - 依存関係の競合を防ぐため

2. **Git管理しない**
   - `venv/`は`.gitignore`に追加
   - 各開発者が自分で作成する

3. **requirements.txtを管理**
   - 依存関係を`requirements.txt`に記録
   - 新しい環境でも再現可能にする

4. **WSL環境での注意**
   - WindowsのパスとWSLのパスは異なる
   - VS Code/CursorではWSL形式のパスを使用

## 🔗 参考資料

- [Python公式ドキュメント: venv](https://docs.python.org/3/library/venv.html)
- [VS Code Python環境設定](https://code.visualstudio.com/docs/python/environments)
- [仮想環境のベストプラクティス](https://docs.python-guide.org/dev/virtualenvs/)

