/**
 * 予測表生成アルゴリズムの動作確認スクリプト
 * 
 * 使い方:
 *   pnpm test:chart-generator
 */

import { generateChart } from '@/lib/chart-generator';
import type { Pattern } from '@/types/prediction';

/**
 * グリッドを表示する（デバッグ用）
 */
function printGrid(grid: (number | null)[][], rows: number, cols: number): void {
  console.log('【グリッド】');
  console.log('   ', Array.from({ length: cols }, (_, i) => i).join('  '));
  console.log('  ', '-'.repeat(cols * 3));
  
  for (let y = 0; y < rows; y++) {
    const row = grid[y].map(val => val === null ? '.' : String(val)).join('  ');
    console.log(`${String(y).padStart(2)} `, row);
  }
  console.log();
}

/**
 * グリッドの検証
 */
function validateGrid(grid: (number | null)[][], rows: number, cols: number): void {
  let nullCount = 0;
  let nonNullCount = 0;
  
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      if (grid[y][x] === null) {
        nullCount++;
      } else {
        nonNullCount++;
        // 値が0-9の範囲内か確認
        if (grid[y][x]! < 0 || grid[y][x]! > 9) {
          throw new Error(`不正な値が検出されました: grid[${y}][${x}] = ${grid[y][x]}`);
        }
      }
    }
  }
  
  console.log(`【グリッド検証】`);
  console.log(`  行数: ${rows}, 列数: ${cols}`);
  console.log(`  総セル数: ${rows * cols}`);
  console.log(`  埋まっているセル: ${nonNullCount}`);
  console.log(`  空白セル: ${nullCount}`);
  
  if (nullCount > 0) {
    console.warn(`  ⚠️  警告: ${nullCount}個の空白セルが残っています`);
  } else {
    console.log(`  ✓ すべてのセルが埋まっています`);
  }
  console.log();
}

async function main() {
  console.log('='.repeat(80));
  console.log('予測表生成アルゴリズムの動作確認');
  console.log('='.repeat(80));
  console.log();

  const testCases: Array<{ roundNumber: number; pattern: Pattern; target: 'n3' | 'n4' }> = [
    { roundNumber: 6758, pattern: 'A1', target: 'n3' },
    { roundNumber: 6758, pattern: 'A1', target: 'n4' },
    { roundNumber: 6758, pattern: 'A2', target: 'n3' },
    { roundNumber: 6758, pattern: 'A2', target: 'n4' },
    { roundNumber: 6758, pattern: 'B1', target: 'n3' },
    { roundNumber: 6758, pattern: 'B1', target: 'n4' },
    { roundNumber: 6758, pattern: 'B2', target: 'n3' },
    { roundNumber: 6758, pattern: 'B2', target: 'n4' },
  ];

  for (const testCase of testCases) {
    console.log('-'.repeat(80));
    console.log(
      `【テストケース】 回号: ${testCase.roundNumber}, ` +
      `パターン: ${testCase.pattern}, 対象: ${testCase.target}`
    );
    console.log('-'.repeat(80));
    console.log();

    try {
      const chartData = await generateChart(
        testCase.roundNumber,
        testCase.pattern,
        testCase.target
      );

      console.log(`✓ 予測表を生成しました`);
      console.log(`  元数字リスト: [${chartData.sourceDigits.join(', ')}]`);
      console.log(`  元数字リストの長さ: ${chartData.sourceDigits.length}`);
      console.log();

      // グリッドの検証
      validateGrid(chartData.grid, chartData.rows, chartData.cols);

      // グリッドの表示（最初のテストケースのみ詳細表示）
      if (testCase.roundNumber === 6758 && testCase.pattern === 'A1' && testCase.target === 'n3') {
        printGrid(chartData.grid, chartData.rows, chartData.cols);
      }

      console.log();
    } catch (error) {
      console.error('✗ 予測表生成エラー:', error);
      if (error instanceof Error) {
        console.error('  エラーメッセージ:', error.message);
        if (error.cause) {
          console.error('  原因:', error.cause);
        }
      }
      console.log();
    }
  }

  console.log('='.repeat(80));
  console.log('✓ すべてのテストが完了しました');
  console.log('='.repeat(80));
}

main().catch((error) => {
  console.error('予期しないエラー:', error);
  process.exit(1);
});

