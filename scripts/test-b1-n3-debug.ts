/**
 * B1パターンのn3のみをテストするスクリプト（デバッグ用）
 */

import { generateChart } from '../src/lib/chart-generator';
import type { Pattern, Target } from '../src/types/prediction';

async function testB1N3(): Promise<void> {
  const roundNumber = 6758;
  const pattern: Pattern = 'B1';
  const target: Target = 'n3';
  
  console.log('='.repeat(80));
  console.log('B1パターン、n3ターゲットのテスト');
  console.log(`回号: ${roundNumber}`);
  console.log('='.repeat(80));
  console.log();
  
  // デバッグモードで実行
  process.env.DEBUG_CHART = 'true';
  process.env.NODE_ENV = 'development';
  
  try {
    const chartData = await generateChart(roundNumber, pattern, target);
    
    console.log();
    console.log('='.repeat(80));
    console.log('結果');
    console.log('='.repeat(80));
    console.log(`グリッドサイズ: ${chartData.rows}行 × ${chartData.cols}列`);
    console.log(`元数字数: ${chartData.sourceDigits.length}`);
    console.log(`sourceDigits: [${chartData.sourceDigits.join(', ')}]`);
    console.log();
    
    // グリッドを表示
    console.log('【予測表】');
    // 1-indexedで表示（列1-8）
    console.log('   ', Array.from({ length: chartData.cols }, (_, i) => i + 1).join('  '));
    console.log('  ', '-'.repeat(chartData.cols * 3));
    // 実装・表示・配列すべて1-indexedで統一（配列のインデックス1から使用、grid[0]は未使用）
    for (let row = 1; row <= chartData.rows; row++) {
      const rowData = chartData.grid[row].slice(1, chartData.cols + 1); // 列も1-indexed（col[0]は未使用）
      const rowStr = rowData.map(val => val === null ? '.' : String(val)).join('  ');
      console.log(`${String(row).padStart(2)} `, rowStr);
    }
    console.log();

    // メイン行の情報を表示
    console.log('メイン行の配置（奇数行目）:');
    for (let i = 0; i < chartData.rows; i += 2) {
      const row = i + 1; // 奇数行（1, 3, 5, 7行目）
      const mainRow = [
        chartData.grid[row][1],
        chartData.grid[row][3],
        chartData.grid[row][5],
        chartData.grid[row][7]
      ].filter(v => v !== null);
      console.log(`  行${row}: [${mainRow.join(', ')}]`);
    }
    
  } catch (error) {
    console.error('エラー:', error instanceof Error ? error.message : error);
    if (error instanceof Error && error.stack) {
      console.error('スタックトレース:', error.stack);
    }
  } finally {
    delete process.env.DEBUG_CHART;
  }
}

testB1N3().catch(error => {
  console.error('テスト実行エラー:', error);
  process.exit(1);
});
