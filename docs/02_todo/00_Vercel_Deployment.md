# 🚀 Vercelデプロイ計画 (Current Sprint - 最優先)

**最終更新**: 2025-11-25
**ステータス**: 🔴 ブロック中（libgomp問題）

---

## 🎯 目標
Next.jsフロントエンドとLightGBMモデルによる予測機能を**Vercel単体**で完結させる。

---

## 📋 現在の状況

### ✅ 完了済み
- [x] ONNXモデル変換スクリプト作成（`scripts/convert_to_onnx.py`）
- [x] LightGBM → ONNX変換実行（6モデル、合計0.5MB）
- [x] ONNX推論モジュール実装試行
- [x] ドキュメント更新（本ファイル、02-system-architecture.md、04-algorithm-ai.md）

### ❌ 不採用となった方針
| 方針 | 不採用理由 |
|------|-----------|
| ONNX + onnxruntime-node | Next.jsビルド時にメモリ不足（SIGKILL） |
| ONNX + onnxruntime-web | 同様のビルド問題 |
| FastAPI別サービス | Vercel単体完結の要件に反する |

### 🔴 現在のブロッカー
**libgomp.so.1問題**: Vercel環境でLightGBMが依存するOpenMPライブラリが見つからない

---

## 🔧 最終方針: Vercel Python Serverless + LightGBM

### アーキテクチャ
```
[ブラウザ] → [Vercel Next.js] → [Vercel Python Serverless] → [LightGBM]
                  │
                  ├── /api/predict/axis.py
                  └── /api/predict/combination.py
```

### 選定理由
| 評価軸 | 評価 |
|--------|------|
| Vercel単体 | ✅ |
| モデル改修効率 | ✅ Pythonで直接 |
| 再デプロイ | ✅ git pushのみ |
| 実装負荷 | ✅ 既存コード活用 |

---

## 📝 次のアクション（再開時はここから）

### Phase 1: libgomp問題の解決 ⬅️ **ここから再開**

#### 1.1 LightGBM最新版での検証
```bash
# api/requirements.txt を更新
lightgbm==4.5.0  # OpenMP依存軽減版

# Vercelデプロイテスト
vercel deploy --force
```

#### 1.2 代替案（1.1で解決しない場合）
- [ ] scikit-learn `GradientBoostingClassifier` で代替
  - 精度検証が必要
  - OpenMP依存なし

### Phase 2: デプロイ・検証
- [ ] プレビュー環境で予測API動作確認
- [ ] 本番環境への昇格

### Phase 3: 不要コード整理
- [ ] `onnxruntime-web`関連の削除確認
- [ ] 古いFastAPI設定の削除

---

## 🗂️ 関連ファイル

| ファイル | 説明 |
|----------|------|
| `api/predict/axis.py` | 軸数字予測API |
| `api/predict/combination.py` | 組み合わせ予測API |
| `api/requirements.txt` | Python依存関係 |
| `core/model_loader.py` | モデルローダー |
| `data/models/*.pkl` | LightGBMモデル |

---

## 📚 関連ドキュメント
- [システムアーキテクチャ](../01_design/02-system-architecture.md)
- [AIアルゴリズム設計](../01_design/04-algorithm-ai.md)
- [MVP最速デプロイ戦略](../01_design/MVP-最速デプロイ戦略.md)

---

## ⚠️ フォールバック計画

libgomp問題が解決しない場合：

1. **scikit-learn GBM代替** - OpenMP依存なし、精度若干低下の可能性
2. **FastAPI別サービス**（最終手段） - Railway/Render等で無料デプロイ
