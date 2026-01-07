# Numbers AI プロジェクト リファクタリング計画

## 📊 現状分析

### ディレクトリサイズ詳細

| ディレクトリ | サイズ | 内訳 | 本番必要 |
|-------------|--------|------|---------|
| `data/` | **24GB** | models/combination_batches: 18GB, training_data: 6GB | ❌ |
| `data/models/*.onnx` | 500KB | 予測用モデル | ✅ |
| `data/models/*_lgb.txt` | 1MB | LightGBM テキストモデル | ⚠️ 検討 |
| `data/past_results.csv` | 248KB | 過去データ | ✅ |
| `venv/` | **1GB** | ルートの Python 仮想環境 | ❌ |
| `api_venv/` | **316MB** | API用 Python 仮想環境 | ❌ |
| `scripts/venv*` | **294MB** | Scripts用仮想環境 | ❌ |
| `api/` | **419MB** | Python API (venv含む) | ❌ (Next.js APIに移行済み?) |
| `scripts/` | **296MB** | 分析・モデル生成スクリプト | ❌ |
| `docs/` | 1.4MB | ドキュメント | ❌ |
| `core/` | 228KB | Python コア機能 | ⚠️ 検討 |
| `src/` | **780KB** | Next.js アプリ | ✅ |

### Pythonファイル: 4,584個 (ほとんどがvenv内)

## 🎯 リファクタリング目標

### Phase 1: 即座に削除可能なもの
1. **ルートのデバッグ・一時ファイル** (20+個)
   - `debug_*.py`, `test_*.py`, `fetch_*.py`, etc.
   
2. **不要なバックアップファイル**
   - `data/past_results_backup_*.csv`
   - `data/past_results copy.csv`
   - `data/*.backup`

3. **docs内の不要ファイル**
   - `docs/past_results.csv` (重複)
   - `docs/mizuho.js`

### Phase 2: アーカイブ（別リポジトリ or ブランチへ）
1. **Python分析スクリプト** → `numbers-ai-analysis` リポジトリへ
   - `scripts/` (ほぼ全て)
   - `core/`
   - `api/` (レガシー)

2. **学習データ・モデルバッチ** → GCS/S3へ
   - `data/models/combination_batches/` (18GB)
   - `data/training_data/` (6GB)
   - `data/models/backup/`

### Phase 3: 最適化
1. **ビルド対象の最小化**
   - `.vercelignore` の最適化
   - `tsconfig.json` の `exclude` 設定

## 📁 理想的なプロジェクト構造

```
numbers-ai/              # 本番デプロイ対象
├── src/                 # Next.js アプリ (✅必須)
├── public/              # 静的ファイル (✅必須)
├── data/
│   ├── past_results.csv # 過去データ (✅必須)
│   ├── keisen_master.json # マスタ (✅必須)
│   └── models/          # 予測モデルのみ
│       ├── *.onnx       # ONNXモデル (✅必須)
│       └── feature_keys.json
├── scripts/
│   └── production/      # 本番用スクリプトのみ
│       ├── fetch_latest_simple.py
│       └── sync-github-data.sh
├── .github/workflows/   # CI/CD (✅必須)
├── docs/
│   └── (運用ドキュメントのみ)
├── package.json
├── next.config.ts
├── tsconfig.json
└── sentry.*.config.ts
```

## ⚠️ 削除前の確認事項

### 本番で必要な機能の確認
- [ ] 予測機能は `src/lib/predictor/` で完結しているか？
- [ ] `core/` の Python コードは使われていないか？
- [ ] `api/` ディレクトリは Next.js API Routes に完全移行済みか？

### バックアップの確認
- [ ] モデル生成スクリプトのバックアップ
- [ ] 学習データのクラウドバックアップ

## 🚀 実行計画

### Step 1: .vercelignore の最適化
デプロイから除外するファイルを明確化

### Step 2: ルートの不要ファイル削除
```bash
# 削除候補
rm -f debug_*.py test_*.py fetch_*.py migrate_*.py fix_*.py verify_*.py extract_*.py
rm -f GIT_ADD_CUBE_FILES.md MIGRATE_TO_PNPM.md
```

### Step 3: データの整理
```bash
# バックアップ削除
rm -f data/past_results_backup_*.csv
rm -f data/past_results*.backup
rm -f data/past_results\ copy.csv

# 重複削除
rm -f docs/past_results.csv docs/mizuho.js
```

### Step 4: .gitignore 更新
ビルドに不要なファイルを gitignore に追加

### Step 5: 分析コードのアーカイブ
別リポジトリへの移行 or アーカイブブランチへ

---

## 実行しますか？

上記の計画で問題なければ、Step 1から順に実行します。
特定のフェーズから始めたい場合や、除外したいファイルがあれば教えてください。
