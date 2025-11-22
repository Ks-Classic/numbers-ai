# npm から pnpm への移行ガイド

## 📊 移行の理由

### pnpm のメリット
- ⚡ **高速インストール**: npmより最大2倍高速
- 💾 **ディスク容量節約**: シンボリックリンクで依存関係を共有
- 🔒 **厳格な依存関係管理**: phantom dependencies（幽霊依存）を防ぐ
- 🌳 **モノレポ対応**: ワークスペース機能が優秀

### numbers-ai-cube との統一
- numbers-ai-cube は既に pnpm を使用
- 両プロジェクトを統一することで管理が容易に

---

## 🚀 移行手順

### 前提条件
pnpm がインストールされていること。未インストールの場合:
```bash
npm install -g pnpm
```

### ステップ1: 既存ファイルの削除とインストール

```bash
cd ~/numbers-ai

# 既存の node_modules と package-lock.json を削除
rm -rf node_modules package-lock.json

# pnpm で依存関係をインストール
pnpm install
```

### ステップ2: 動作確認

```bash
# 開発サーバーを起動
pnpm dev

# ビルドテスト
pnpm build

# テストスクリプトを実行
pnpm test:data-loader
pnpm test:chart-generator
pnpm test:patterns
```

### ステップ3: 変更をコミット

```bash
# 変更ファイルを確認
git status

# pnpm-lock.yaml と package.json の変更をコミット
git add pnpm-lock.yaml package.json .gitignore .npmrc
git commit -m "chore: migrate from npm to pnpm"
git push
```

---

## 📝 変更内容

### 1. package.json
- `packageManager`: `"npm@10.0.0"` → `"pnpm@9.0.0"`
- スクリプト内の `npx` → `pnpm exec` に変更

### 2. .npmrc
- pnpm 用の設定に更新
- `strict-peer-dependencies=false` を追加

### 3. .gitignore
- `package-lock.json` を追加（pnpm では pnpm-lock.yaml を使用）

### 4. ロックファイル
- `package-lock.json` を削除
- `pnpm-lock.yaml` を追加

---

## 🔄 よく使うコマンドの対応表

| npm | pnpm |
|---|---|
| `npm install` | `pnpm install` |
| `npm install <pkg>` | `pnpm add <pkg>` |
| `npm install -D <pkg>` | `pnpm add -D <pkg>` |
| `npm uninstall <pkg>` | `pnpm remove <pkg>` |
| `npm run <script>` | `pnpm <script>` または `pnpm run <script>` |
| `npx <command>` | `pnpm exec <command>` または `pnpm dlx <command>` |
| `npm update` | `pnpm update` |
| `npm list` | `pnpm list` |

---

## ⚠️ トラブルシューティング

### 問題: peer dependencies の警告が出る
**解決策**: `.npmrc` に `strict-peer-dependencies=false` を追加（既に設定済み）

### 問題: 一部のパッケージが見つからない
**解決策**: `shamefully-hoist=true` を `.npmrc` に追加（npm の挙動に近づける）

### 問題: インストールが失敗する
**解決策**:
```bash
# キャッシュをクリア
pnpm store prune

# 再インストール
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

---

## 📚 参考リンク

- [pnpm 公式ドキュメント](https://pnpm.io/)
- [npm から pnpm への移行ガイド](https://pnpm.io/motivation)
- [pnpm CLI コマンド](https://pnpm.io/cli/add)

---

## ✅ チェックリスト

移行完了後、以下を確認してください:

- [ ] `pnpm install` が正常に完了する
- [ ] `pnpm dev` で開発サーバーが起動する
- [ ] `pnpm build` でビルドが成功する
- [ ] テストスクリプトが正常に動作する
- [ ] `pnpm-lock.yaml` が生成されている
- [ ] `package-lock.json` が削除されている
- [ ] 変更がコミット・プッシュされている
