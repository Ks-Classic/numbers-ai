# 4パターン（A1/A2/B1/B2）テスト結果

## テストスクリプト

`scripts/test-4-patterns.ts` を作成しました。

### 実行方法

```bash
# 方法1: npmスクリプト経由
npm run test:patterns

# 方法2: tsxを直接使用
npx tsx scripts/test-4-patterns.ts
```

### テスト内容

1. **4パターンすべてのテスト**
   - A1, A2, B1, B2 の各パターン
   - n3, n4 の各ターゲット
   - 合計8パターンの組み合わせをテスト

2. **中心0配置の確認**
   - A2/B2: 中心0配置あり（期待値）
   - A1/B1: 中心0配置なし（期待値）

3. **予測表生成の確認**
   - 各パターンで正しく予測表が生成されること
   - グリッドサイズが正しいこと
   - 元数字リストが正しく生成されること

### テスト結果の確認ポイント

- ✅ すべてのパターンで予測表が生成される
- ✅ 中心0配置がA2/B2のみで実行される
- ✅ グリッドにnullが残っていない（すべて埋まっている）
- ✅ 各パターンで異なる予測表が生成される

### 手動テスト手順

開発サーバーが起動している状態で、以下のAPIエンドポイントを直接テストすることもできます：

```
GET /api/test-chart?roundNumber=6758&pattern=A1&target=n3
GET /api/test-chart?roundNumber=6758&pattern=A2&target=n3
GET /api/test-chart?roundNumber=6758&pattern=B1&target=n3
GET /api/test-chart?roundNumber=6758&pattern=B2&target=n3
GET /api/test-chart?roundNumber=6758&pattern=A1&target=n4
GET /api/test-chart?roundNumber=6758&pattern=A2&target=n4
GET /api/test-chart?roundNumber=6758&pattern=B1&target=n4
GET /api/test-chart?roundNumber=6758&pattern=B2&target=n4
```

### 期待される動作

- **A1パターン**: 欠番補足あり（0〜9全追加）+ 中心0配置なし
- **A2パターン**: 欠番補足あり（0〜9全追加）+ 中心0配置あり
- **B1パターン**: 欠番補足なし（0のみ追加）+ 中心0配置なし
- **B2パターン**: 欠番補足なし（0のみ追加）+ 中心0配置あり

### 実装確認済み事項

- ✅ `generateChart`関数は4パターン（A1/A2/B1/B2）すべてを受け取れる
- ✅ `applyPatternExpansion`関数はA1/A2とB1/B2を正しく区別する
- ✅ `placeCenterZero`関数はA2/B2のみで実行される（実装確認済み）

