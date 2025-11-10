/**
 * 8列×10行となる回号を探すスクリプト
 * 
 * 実行方法:
 *   npx tsx scripts/find_10_row_rounds.ts
 */

import { generateChart } from '../src/lib/cube-generator';
import { loadPastResults } from '../src/lib/data-loader';
import type { Pattern } from '../src/types/prediction';

async function find10RowRounds() {
  console.log('8列×10行となる回号を探しています...\n');

  // データ読み込み
  const pastResults = await loadPastResults();
  
  // 最新の回号を取得
  const maxRound = Math.max(...pastResults.map(r => r.roundNumber));
  console.log(`最新回号: 第${maxRound}回\n`);

  const results: Array<{
    round: number;
    date: string;
    n3Winning: string;
    rows: number;
    mainRows: number;
  }> = [];

  // 最新から順に確認（200回分遡る）
  for (let roundNum = maxRound; roundNum >= maxRound - 200; roundNum--) {
    try {
      // N3のA1パターンで確認（どのパターンでも行数は同じ）
      const chartData = await generateChart(roundNum, 'A1' as Pattern, 'n3', 'current');
      
      if (chartData.rows === 10) {
        const result = pastResults.find(r => r.roundNumber === roundNum);
        const date = result?.drawDate || 'N/A';
        const n3Winning = result?.n3Winning || 'N/A';
        
        results.push({
          round: roundNum,
          date,
          n3Winning,
          rows: chartData.rows,
          mainRows: chartData.tempList ? chartData.tempList.length / 4 : chartData.rows / 2 // 概算（正確にはmainRows.length）
        });
        
        console.log(`✓ 第${roundNum}回 (${date}) - N3=${n3Winning} - ${chartData.rows}行`);
        
        if (results.length >= 4) {
          break;
        }
      }
    } catch (error) {
      // エラーが発生した回号はスキップ
      continue;
    }
  }

  console.log('\n' + '='.repeat(70));
  console.log('【結果】8列×10行となる回号（新しい順）');
  console.log('='.repeat(70));

  if (results.length >= 4) {
    results.forEach((result, i) => {
      console.log(`${i + 1}. 第${result.round}回 (${result.date}) - N3=${result.n3Winning} - ${result.rows}行`);
    });
  } else {
    console.log(`10行となる回号が${results.length}件しか見つかりませんでした。`);
    results.forEach((result, i) => {
      console.log(`${i + 1}. 第${result.round}回 (${result.date}) - N3=${result.n3Winning} - ${result.rows}行`);
    });
  }
}

// 実行
find10RowRounds().catch(error => {
  console.error('エラー:', error);
  process.exit(1);
});

