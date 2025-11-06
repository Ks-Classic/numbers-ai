# Pythonインタープリター設定

このプロジェクトでは、Cursor/VS Codeで正しいPythonインタープリターを選択する必要があります。

## 設定方法

### 方法1: 自動設定（推奨）

`.vscode/settings.json`ファイルが作成されているため、Cursor/VS Codeを再起動すると自動的に設定されます。

### 方法2: 手動設定

1. **コマンドパレットを開く**
   - `Ctrl+Shift+P` (Windows/Linux)
   - `Cmd+Shift+P` (Mac)

2. **「Python: Select Interpreter」を選択**

3. **以下のインタープリターを選択**
   ```
   ./notebooks/venv/bin/python3
   ```

   または、WSL環境の場合は：
   ```
   \\wsl.localhost\Ubuntu-24.04\home\ykoha\numbers-ai\notebooks\venv\bin\python3
   ```

## 複数の仮想環境について

このプロジェクトには複数の仮想環境があります：

- **`notebooks/venv`**: 機械学習・データ処理用（推奨）
- **`api/venv`**: FastAPI用
- **`scripts/venv`**: スクリプト実行用

作業するディレクトリに応じて、適切なインタープリターを選択してください。

## 確認方法

設定が正しく行われているか確認するには：

1. Cursor/VS Codeのステータスバー（画面下部）でPythonバージョンを確認
2. ターミナルで `python --version` を実行して、仮想環境が有効化されているか確認

## トラブルシューティング

### 警告が消えない場合

1. Cursor/VS Codeを再起動
2. Python拡張機能がインストールされているか確認
3. `.vscode/settings.json`が正しく作成されているか確認

### パスが見つからない場合

WSL環境では、以下のパス形式を試してください：

```
\\wsl.localhost\Ubuntu-24.04\home\ykoha\numbers-ai\notebooks\venv\bin\python3
```

または、相対パス：
```
./notebooks/venv/bin/python3
```

