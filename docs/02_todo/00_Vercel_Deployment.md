# 🚀 Vercelデプロイ計画 (Current Sprint - ✅ 完了)

**最終更新**: 2025-11-25
**ステータス**: ✅ **完了** - Python Serverless Functions動作確認済み

---

## 🎯 目標
Next.jsフロントエンドとLightGBMモデルによる予測機能を**Vercel単体**で完結させる。

---

## 📋 完了した作業

### ✅ Phase 1: libgomp問題の解決
- [x] LightGBM 4.5.0 に更新（OpenMP依存軽減版）
- [x] `LD_LIBRARY_PATH` 環境変数設定（vercel.json）
- [x] `libgomp.so.1` の配置（api/py/）
- [x] `ctypes.CDLL` による明示的ロード

### ✅ Phase 2: scikit-learn依存の除去
- [x] モデルをLightGBMネイティブ形式（.txt）に変換
- [x] 特徴量キーをJSON形式で保存
- [x] `model_loader.py` をBooster形式に対応
- [x] requirements.txtからscikit-learn削除（サイズ制限対策）

### ✅ Phase 3: デプロイ・検証
- [x] プレビュー環境で予測API動作確認
- [x] `/api/py/axis` エンドポイント: 正常動作
- [x] `/api/py/combination` エンドポイント: 正常動作

---

## 🔧 最終アーキテクチャ

```
[ブラウザ] → [Vercel Next.js] → [Vercel Python Serverless] → [LightGBM Native]
                  │
                  ├── /api/py/axis.py      (軸数字予測)
                  └── /api/py/combination.py (組み合わせ予測)
```

### 技術スタック
| コンポーネント | 技術 |
|--------------|------|
| フロントエンド | Next.js 15.5.4 |
| Python関数 | Vercel Serverless Functions |
| 機械学習 | LightGBM 4.5.0（ネイティブ形式） |
| データ | pandas, numpy |

---

## 📝 解決した技術的課題

### 1. libgomp.so.1問題
**問題**: LightGBMがOpenMP（libgomp.so.1）に依存、Vercel環境で見つからない

**解決策**:
1. `libgomp.so.1` をapi/py/に同梱
2. vercel.jsonで`LD_LIBRARY_PATH`を設定
3. Python関数内で`ctypes.CDLL`で明示的ロード

### 2. サイズ制限（250MB）超過
**問題**: scikit-learn追加でServerless関数が250MB制限を超過

**解決策**:
1. モデルをpickle形式からLightGBMネイティブ形式（.txt）に変換
2. `lgb.Booster`で直接ロード（scikit-learn不要）
3. 特徴量キーを別ファイル（JSON）で管理

### 3. Next.js APIルートとの競合
**問題**: `api/predict/`がNext.js API Routeと競合

**解決策**:
- Python関数を`api/py/`に移動
- vercel.jsonでrewriteルール設定

---

## 🗂️ 関連ファイル

| ファイル | 説明 |
|----------|------|
| `api/py/axis.py` | 軸数字予測API |
| `api/py/combination.py` | 組み合わせ予測API |
| `api/py/requirements.txt` | Python依存関係 |
| `api/py/libgomp.so.1` | OpenMPライブラリ |
| `core/model_loader.py` | モデルローダー（Booster対応） |
| `data/models/*.txt` | LightGBMネイティブモデル |
| `data/models/*_keys.json` | 特徴量キー定義 |
| `vercel.json` | Vercel設定（LD_LIBRARY_PATH含む） |

---

## 📚 関連ドキュメント
- [システムアーキテクチャ](../01_design/02-system-architecture.md)
- [AIアルゴリズム設計](../01_design/04-algorithm-ai.md)
- [MVP最速デプロイ戦略](../01_design/MVP-最速デプロイ戦略.md)

---

## 🔜 次のステップ

1. **本番デプロイ**: `vercel --prod`
2. **フロントエンド統合**: Next.js API RouteからPython関数を呼び出す
3. **テスト関数削除**: `api/py/test.py`をプロダクション前に削除
4. **パフォーマンス監視**: Vercel Analyticsで応答時間を監視
