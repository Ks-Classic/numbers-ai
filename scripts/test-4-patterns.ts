/**
 * 4パターン（A1/A2/B1/B2）のテストスクリプト
 * 
 * 実行方法:
 *   # 直接実行（回号指定なし、デフォルト: 6758）
 *   npx tsx scripts/test-4-patterns.ts
 * 
 *   # 直接実行（回号指定）
 *   npx tsx scripts/test-4-patterns.ts 6758
 *   npx tsx scripts/test-4-patterns.ts 6700
 * 
 *   # デバッグモード有効（第2引数に 'debug' を指定）
 *   npx tsx scripts/test-4-patterns.ts 6758 debug
 * 
 *   # npmスクリプト経由（回号指定なし、デフォルト: 6758）
 *   npm run test:patterns
 * 
 *   # npmスクリプト経由（回号指定、--が必要）
 *   npm run test:patterns -- 6758
 *   npm run test:patterns -- 6700
 * 
 *   # npmスクリプト経由（デバッグモード有効）
 *   npm run test:patterns -- 6758 debug
 */

import { generateChart } from '../src/lib/chart-generator';
import { 
  getPreviousResult, 
  getPreviousPreviousResult,
  getPredictedDigits,
  type ColumnName
} from '../src/lib/data-loader';
import type { Pattern, Target } from '../src/types/prediction';

interface TestResult {
  pattern: Pattern;
  target: Target;
  success: boolean;
  error?: string;
  grid?: (number | null)[][];
  gridSize?: {
    rows: number;
    cols: number;
  };
  sourceDigits?: number[];
  expandedDigits?: number[];
}

interface SourceDigitsInfo {
  previousRound: number;
  previousPreviousRound: number;
  previousWinning: string;
  previousPreviousWinning: string;
  digitsByColumn: Array<{
    column: string;
    previousDigit: number;
    previousPreviousDigit: number;
    predictedDigits: number[];
  }>;
  sourceDigits: number[];
}

/**
 * 元数字（欠番補足前）の生成プロセスを取得
 */
async function getSourceDigitsInfo(
  roundNumber: number,
  target: Target
): Promise<SourceDigitsInfo> {
  const previousResult = await getPreviousResult(roundNumber);
  const previousPreviousResult = await getPreviousPreviousResult(roundNumber);
  
  if (!previousResult || !previousPreviousResult) {
    throw new Error('前回または前々回のデータが見つかりません');
  }
  
  const columnNames: ColumnName[] = target === 'n3' 
    ? ['百の位', '十の位', '一の位']
    : ['千の位', '百の位', '十の位', '一の位'];
  
  const previousWinning = target === 'n3' 
    ? previousResult.n3Winning 
    : previousResult.n4Winning;
  
  const previousPreviousWinning = target === 'n3'
    ? previousPreviousResult.n3Winning
    : previousPreviousResult.n4Winning;
  
  const digitsByColumn: Array<{
    column: string;
    previousDigit: number;
    previousPreviousDigit: number;
    predictedDigits: number[];
  }> = [];
  
  const sourceList: number[] = [];
  
  for (const columnName of columnNames) {
    const digitIndex = columnNames.indexOf(columnName);
    const previousDigit = parseInt(previousWinning[digitIndex], 10);
    const previousPreviousDigit = parseInt(previousPreviousWinning[digitIndex], 10);
    
    const predictedDigits = await getPredictedDigits(
      target,
      columnName,
      previousDigit,
      previousPreviousDigit
    );
    
    digitsByColumn.push({
      column: columnName,
      previousDigit,
      previousPreviousDigit,
      predictedDigits
    });
    
    sourceList.push(...predictedDigits);
  }
  
  sourceList.sort((a, b) => a - b);
  
  return {
    previousRound: previousResult.roundNumber,
    previousPreviousRound: previousPreviousResult.roundNumber,
    previousWinning,
    previousPreviousWinning,
    digitsByColumn,
    sourceDigits: sourceList
  };
}

/**
 * グリッドを表示する
 */
function printGrid(grid: (number | null)[][], rows: number, cols: number, pattern: Pattern, target: Target): void {
  console.log(`\n【予測表: pattern=${pattern}, target=${target}】`);
  // 1-indexedで表示（列1-8）
  console.log('   ', Array.from({ length: cols }, (_, i) => i + 1).join('  '));
  console.log('  ', '-'.repeat(cols * 3));
  // 実装・表示・配列すべて1-indexedで統一（配列のインデックス1から使用、grid[0]は未使用）
  for (let row = 1; row <= rows; row++) {
    const rowData = grid[row].slice(1, cols + 1); // 列も1-indexed（col[0]は未使用）
    const rowStr = rowData.map(val => val === null ? '.' : String(val)).join('  ');
    console.log(`${String(row).padStart(2)} `, rowStr);
  }
  console.log();
}

/**
 * 1つのパターンとターゲットの組み合わせをテスト
 */
async function testPattern(
  pattern: Pattern,
  target: Target,
  roundNumber: number = 6758
): Promise<TestResult> {
  try {
    const chartData = await generateChart(roundNumber, pattern, target);
    
    return {
      pattern,
      target,
      success: true,
      grid: chartData.grid,
      gridSize: {
        rows: chartData.rows,
        cols: chartData.cols
      },
      sourceDigits: chartData.sourceDigits,
      expandedDigits: chartData.expandedDigits
    };
  } catch (error) {
    return {
      pattern,
      target,
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * すべてのパターンとターゲットの組み合わせをテスト
 */
async function testAllPatterns(): Promise<void> {
  const patterns: Pattern[] = ['A1' as Pattern, 'A2' as Pattern, 'B1' as Pattern, 'B2' as Pattern];
  const targets: Target[] = ['n3', 'n4'];
  
  // コマンドライン引数から回号を取得（デフォルト: 6758）
  // @ts-ignore - process is available in Node.js environment
  const roundNumberArg = process.argv[2];
  const roundNumber = roundNumberArg
    ? parseInt(roundNumberArg, 10)
    : 6758;
  
  if (isNaN(roundNumber) || roundNumber < 1000 || roundNumber > 9999) {
    console.error('エラー: 回号は4桁の数字で入力してください（例: 6758）');
    // @ts-ignore - process is available in Node.js environment
    process.exit(1);
  }
  
  // デバッグモードの切り替え（第2引数が 'debug' の場合）
  // @ts-ignore - process is available in Node.js environment
  const debugMode = process.argv[3] === 'debug';
  if (debugMode) {
    // @ts-ignore - process is available in Node.js environment
    process.env.DEBUG_CHART = 'true';
    console.log('🐛 デバッグモード: 有効\n');
  } else {
    // @ts-ignore - process is available in Node.js environment
    process.env.DEBUG_CHART = 'false';
  }
  
  // デバッグモードでない場合は簡潔なヘッダーのみ
  if (!debugMode) {
    console.log(`回号: ${roundNumber}`);
    console.log();
  } else {
    console.log('='.repeat(80));
    console.log('4パターン（A1/A2/B1/B2）テスト');
    console.log(`回号: ${roundNumber}`);
    console.log('='.repeat(80));
    console.log();
  }
  
  // ターゲットごとに処理
  for (const target of targets) {
    if (debugMode) {
      console.log(`\n【ターゲット: ${target.toUpperCase()}】`);
      console.log('-'.repeat(80));
    } else {
      console.log(`\n【ターゲット: ${target.toUpperCase()}】`);
    }
    
    // 元数字の生成プロセスを取得・表示
    try {
      const sourceInfo = await getSourceDigitsInfo(roundNumber, target);
      
      console.log(`前々回（第${sourceInfo.previousPreviousRound}回）: ${sourceInfo.previousPreviousWinning}`);
      console.log(`前回（第${sourceInfo.previousRound}回）: ${sourceInfo.previousWinning}`);
      
      // 各桁の予測出目を表示
      for (const colInfo of sourceInfo.digitsByColumn) {
        console.log(`${colInfo.column}: [${colInfo.predictedDigits.join(', ')}]`);
      }
      
      console.log(`【元数字（欠番補足前）】: [${sourceInfo.sourceDigits.join(', ')}]`);
      console.log();
    } catch (error) {
      console.error(`元数字の取得エラー: ${error instanceof Error ? error.message : error}`);
      continue;
    }
    
    // パターンごとにテスト
    let hasError = false;
    for (const pattern of patterns) {
      const result = await testPattern(pattern, target, roundNumber);
      
      if (result.success) {
        // パターン名を表示
        const patternName = (pattern === ('A1' as Pattern) || pattern === ('A2' as Pattern)) ? '欠番補足あり' : '欠番補足なし';
        console.log(`【パターン ${pattern}】${patternName}`);
        
        // 拡張後の数字（欠番補足後）
        if (result.expandedDigits) {
          console.log(`拡張後: [${result.expandedDigits.join(', ')}]`);
        }
        
        // 予測表を表示
        if (result.grid && result.gridSize) {
          printGrid(result.grid, result.gridSize.rows, result.gridSize.cols, pattern, target);
        }
      } else {
        console.log(`【パターン ${pattern}】`);
        console.log(`  ❌ 失敗: ${result.error}`);
        hasError = true;
      }
    }
    
    if (hasError) {
      // @ts-ignore - process is available in Node.js environment
      process.exit(1);
    }
  }
  
  // デバッグモードの場合のみサマリーを表示
  if (debugMode) {
    console.log('\n' + '='.repeat(80));
    console.log('テスト結果サマリー');
    console.log('='.repeat(80));
    
    const allResults: TestResult[] = [];
    for (const target of targets) {
      for (const pattern of patterns) {
        const result = await testPattern(pattern, target, roundNumber);
        allResults.push(result);
      }
    }
    
    const successCount = allResults.filter(r => r.success).length;
    const totalCount = allResults.length;
    
    console.log(`総テスト数: ${totalCount}`);
    console.log(`成功: ${successCount}`);
    console.log(`失敗: ${totalCount - successCount}`);
    
    if (successCount < totalCount) {
      console.error('\n一部のテストが失敗しました');
      // @ts-ignore - process is available in Node.js environment
      process.exit(1);
    }
    
    console.log('\n✅ すべてのテストが成功しました');
  }
  
  // 正常終了（エラーがない場合）
  // @ts-ignore - process is available in Node.js environment
  process.exit(0);
}

// 実行
testAllPatterns().catch(error => {
  console.error('テスト実行エラー:', error);
  // @ts-ignore - process is available in Node.js environment
  process.exit(1);
});
