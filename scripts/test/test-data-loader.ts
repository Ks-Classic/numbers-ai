/**
 * データ読み込みユーティリティの動作確認スクリプト
 * 
 * 使い方:
 *   pnpm test:data-loader
 */

import {
  loadPastResults,
  getPastResultByRoundNumber,
  getPreviousResult,
  getPreviousPreviousResult,
  loadKeisenMaster,
  getPredictedDigits,
} from '../src/lib/data-loader/index';

async function main() {
  console.log('='.repeat(80));
  console.log('データ読み込みユーティリティの動作確認');
  console.log('='.repeat(80));
  console.log();

  // CSV読み込みのテスト
  console.log('📊 CSV読み込みテスト');
  console.log('-'.repeat(80));
  
  try {
    const results = await loadPastResults();
    console.log(`✓ 過去当選番号データを読み込みました: ${results.length}件`);
    console.log();
    
    // 最初の5件を表示
    console.log('【最初の5件】');
    for (const result of results.slice(0, 5)) {
      console.log(
        `  第${result.roundNumber}回 (${result.drawDate}): ` +
        `N3=${result.n3Winning}(${result.n3Rehearsal || 'なし'}), ` +
        `N4=${result.n4Winning}(${result.n4Rehearsal || 'なし'})`
      );
    }
    console.log();
    
    // 特定の回号を取得
    const testRoundNumber = 6758;
    const specificResult = await getPastResultByRoundNumber(testRoundNumber);
    if (specificResult) {
      console.log(`【回号${testRoundNumber}のデータ】`);
      console.log(`  日付: ${specificResult.drawDate}`);
      console.log(`  N3当選: ${specificResult.n3Winning}`);
      console.log(`  N4当選: ${specificResult.n4Winning}`);
      console.log(`  N3リハーサル: ${specificResult.n3Rehearsal || 'なし'}`);
      console.log(`  N4リハーサル: ${specificResult.n4Rehearsal || 'なし'}`);
      console.log();
      
      // 前回・前々回の取得
      const previous = await getPreviousResult(testRoundNumber);
      const previousPrevious = await getPreviousPreviousResult(testRoundNumber);
      
      if (previous) {
        console.log(`【前回（第${previous.roundNumber}回）】`);
        console.log(`  N3: ${previous.n3Winning}, N4: ${previous.n4Winning}`);
      }
      
      if (previousPrevious) {
        console.log(`【前々回（第${previousPrevious.roundNumber}回）】`);
        console.log(`  N3: ${previousPrevious.n3Winning}, N4: ${previousPrevious.n4Winning}`);
      }
      console.log();
    }
  } catch (error) {
    console.error('✗ CSV読み込みエラー:', error);
    return;
  }

  // JSON読み込みのテスト
  console.log('📋 JSON読み込みテスト');
  console.log('-'.repeat(80));
  
  try {
    const master = await loadKeisenMaster();
    console.log('✓ 罫線マスターデータを読み込みました');
    console.log();
    
    // N3の構造確認
    console.log('【N3の構造確認】');
    const n3Columns = Object.keys(master.n3);
    console.log(`  桁数: ${n3Columns.length}（${n3Columns.join(', ')}）`);
    
    // N4の構造確認
    console.log('【N4の構造確認】');
    const n4Columns = Object.keys(master.n4);
    console.log(`  桁数: ${n4Columns.length}（${n4Columns.join(', ')}）`);
    console.log();
    
    // 予測出目の取得テスト
    console.log('【予測出目取得テスト】');
    const testCases = [
      { target: 'n3' as const, column: '百の位' as const, prev: 1, prevPrev: 2 },
      { target: 'n3' as const, column: '十の位' as const, prev: 5, prevPrev: 7 },
      { target: 'n4' as const, column: '千の位' as const, prev: 0, prevPrev: 9 },
      { target: 'n4' as const, column: '百の位' as const, prev: 3, prevPrev: 6 },
    ];
    
    for (const testCase of testCases) {
      const digits = await getPredictedDigits(
        testCase.target,
        testCase.column,
        testCase.prev,
        testCase.prevPrev
      );
      console.log(
        `  ${testCase.target}.${testCase.column} ` +
        `(前回:${testCase.prev}, 前々回:${testCase.prevPrev}) → ` +
        `[${digits.join(', ')}]`
      );
    }
    console.log();
    
    // キャッシュのテスト
    console.log('【キャッシュ機能のテスト】');
    const start1 = Date.now();
    await loadKeisenMaster(true);
    const time1 = Date.now() - start1;
    
    const start2 = Date.now();
    await loadKeisenMaster(true);
    const time2 = Date.now() - start2;
    
    console.log(`  1回目: ${time1}ms`);
    console.log(`  2回目（キャッシュ）: ${time2}ms`);
    if (time2 < time1) {
      console.log(`  ✓ キャッシュが機能しています（${time1 - time2}ms短縮）`);
    }
    console.log();
    
  } catch (error) {
    console.error('✗ JSON読み込みエラー:', error);
    return;
  }

  console.log('='.repeat(80));
  console.log('✓ すべてのテストが完了しました');
  console.log('='.repeat(80));
}

main().catch((error) => {
  console.error('予期しないエラー:', error);
  process.exit(1);
});

