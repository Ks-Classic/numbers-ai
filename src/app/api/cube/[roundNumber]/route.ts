import { NextRequest, NextResponse } from 'next/server';
import { generateChart, generateExtremeCube } from '@/lib/cube-generator';
import { getPreviousResult, getPreviousPreviousResult, getPastResultByRoundNumber } from '@/lib/data-loader';
import type { Pattern, Target } from '@/types/prediction';
import type { KeisenMasterType } from '@/lib/cube-generator';

/**
 * 予測出目を抽出する（ヘルパー関数）
 * 
 * @param roundNumber 回号
 * @param target 対象（'n3' または 'n4'）
 * @param keisenMasterType 罫線マスターの種類
 * @param pattern パターン（'A1' | 'A2' | 'B1' | 'B2'）
 * @returns 予測出目の配列
 */
async function extractPredictedDigits(
  roundNumber: number,
  target: Target,
  keisenMasterType: KeisenMasterType,
  pattern: Pattern = 'A1'
): Promise<number[]> {
  // generateChartを呼び出してsourceDigitsを取得
  const chartData = await generateChart(roundNumber, pattern, target, keisenMasterType);
  return chartData.sourceDigits;
}

/**
 * 欠番補足あり/なしの抽出数字を取得
 * 
 * @param roundNumber 回号
 * @param target 対象（'n3' または 'n4'）
 * @param keisenMasterType 罫線マスターの種類
 * @returns 欠番補足あり（A1/A2）と欠番補足なし（B1/B2）の抽出数字
 */
async function extractPredictedDigitsByMissingFill(
  roundNumber: number,
  target: Target,
  keisenMasterType: KeisenMasterType
): Promise<{
  withMissingFill: number[]; // A1/A2（欠番補足あり）
  withoutMissingFill: number[]; // B1/B2（欠番補足なし）
}> {
  // A1とA2の抽出数字を取得（欠番補足あり）
  const a1Digits = await extractPredictedDigits(roundNumber, target, keisenMasterType, 'A1');
  const a2Digits = await extractPredictedDigits(roundNumber, target, keisenMasterType, 'A2');
  // 和集合を取得（重複除去、ソート）
  const withMissingFill = Array.from(new Set([...a1Digits, ...a2Digits])).sort((a, b) => a - b);
  
  // B1とB2の抽出数字を取得（欠番補足なし）
  const b1Digits = await extractPredictedDigits(roundNumber, target, keisenMasterType, 'B1');
  const b2Digits = await extractPredictedDigits(roundNumber, target, keisenMasterType, 'B2');
  // 和集合を取得（重複除去、ソート）
  const withoutMissingFill = Array.from(new Set([...b1Digits, ...b2Digits])).sort((a, b) => a - b);
  
  return { withMissingFill, withoutMissingFill };
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ roundNumber: string }> }
) {
  try {
    const { roundNumber } = await params;

    if (!roundNumber) {
      return NextResponse.json(
        { error: '回号が指定されていません' },
        { status: 400 }
      );
    }

    const roundNumberInt = parseInt(roundNumber, 10);
    if (isNaN(roundNumberInt) || roundNumberInt < 1) {
      return NextResponse.json(
        { error: '無効な回号です' },
        { status: 400 }
      );
    }

    console.log(`[CUBE API Route] リクエスト: 回号=${roundNumberInt}`);

    // クエリパラメータから手動編集値を取得
    const { searchParams } = new URL(request.url);
    const manualN3Winning = searchParams.get('n3_winning');
    const manualN4Winning = searchParams.get('n4_winning');
    const manualN3Rehearsal = searchParams.get('n3_rehearsal');
    const manualN4Rehearsal = searchParams.get('n4_rehearsal');
    
    console.log(`[CUBE API Route] 手動編集値:`, {
      n3_winning: manualN3Winning,
      n4_winning: manualN4Winning,
      n3_rehearsal: manualN3Rehearsal,
      n4_rehearsal: manualN4Rehearsal,
    });

    // 現在の回号の当選番号を取得（インジケーター説明用）
    // 手動編集値がある場合はそれを優先、なければCSVから取得
    const currentResult = await getPastResultByRoundNumber(roundNumberInt);
    
    console.log(`[CUBE API Route] 現在の回号データ取得:`, {
      roundNumber: roundNumberInt,
      currentResult: currentResult ? {
        n3Winning: currentResult.n3Winning,
        n4Winning: currentResult.n4Winning,
        n3Rehearsal: currentResult.n3Rehearsal,
        n4Rehearsal: currentResult.n4Rehearsal,
      } : null,
      manualN3Winning,
      manualN4Winning,
      manualN3Rehearsal,
      manualN4Rehearsal,
    });
    
    // 手動編集値またはCSVデータを使用
    const currentWinning = {
      n3: manualN3Winning || currentResult?.n3Winning || null,
      n4: manualN4Winning || currentResult?.n4Winning || null,
    };
    
    const currentRehearsal = {
      n3: manualN3Rehearsal || currentResult?.n3Rehearsal || null,
      n4: manualN4Rehearsal || currentResult?.n4Rehearsal || null,
    };
    
    console.log(`[CUBE API Route] current_winning/rehearsal設定:`, {
      currentWinning,
      currentRehearsal,
    });
    
    // 前回・前々回の当選番号を取得
    const previousResult = await getPreviousResult(roundNumberInt);
    const previousPreviousResult = await getPreviousPreviousResult(roundNumberInt);

    if (!previousResult) {
      return NextResponse.json(
        { error: `前回の当選番号が見つかりません（回号: ${roundNumberInt - 1}）` },
        { status: 404 }
      );
    }

    if (!previousPreviousResult) {
      return NextResponse.json(
        { error: `前々回の当選番号が見つかりません（回号: ${roundNumberInt - 2}）` },
        { status: 404 }
      );
    }

    const previousN3 = previousResult.n3Winning.padStart(3, '0');
    const previousN4 = previousResult.n4Winning.padStart(4, '0');
    const previousPreviousN3 = previousPreviousResult.n3Winning.padStart(3, '0');
    const previousPreviousN4 = previousPreviousResult.n4Winning.padStart(4, '0');
    
    // リハーサル数字を取得
    const previousN3Rehearsal = previousResult.n3Rehearsal?.padStart(3, '0') || null;
    const previousN4Rehearsal = previousResult.n4Rehearsal?.padStart(4, '0') || null;
    const previousPreviousN3Rehearsal = previousPreviousResult.n3Rehearsal?.padStart(3, '0') || null;
    const previousPreviousN4Rehearsal = previousPreviousResult.n4Rehearsal?.padStart(4, '0') || null;

    const cubes = [];
    const patterns: Pattern[] = ['A1', 'A2', 'B1', 'B2'];
    const targets: Target[] = ['n3', 'n4'];

    // 欠番補足あり/なしの抽出数字を事前に取得（現罫線）
    const currentExtractedDigits: {
      [target: string]: { withMissingFill: number[]; withoutMissingFill: number[] };
    } = {};
    for (const target of targets) {
      try {
        currentExtractedDigits[target] = await extractPredictedDigitsByMissingFill(
          roundNumberInt,
          target,
          'current'
        );
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        console.error(`[CUBE API Route] 現罫線 ${target} の抽出数字取得に失敗:`, errorMsg, error);
        throw error; // 抽出数字の取得に失敗した場合はエラーを投げる
      }
    }

    // 通常CUBE: 現罫線 × 4パターン（A1, A2, B1, B2） × N3/N4 = 8個
    console.log('[CUBE API Route] 通常CUBE（現罫線）の生成を開始...');
    for (const target of targets) {
      const previousWinning = target === 'n3' ? previousN3 : previousN4;
      const previousPreviousWinning = target === 'n3' ? previousPreviousN3 : previousPreviousN4;

      for (const pattern of patterns) {
        try {
          const chartData = await generateChart(roundNumberInt, pattern, target, 'current');
          cubes.push({
            id: `current_normal_${target}_${pattern}`,
            keisen_type: 'current',
            cube_type: 'normal',
            target,
            pattern,
            grid: chartData.grid,
            rows: chartData.rows,
            cols: chartData.cols,
            previous_winning: previousWinning,
            previous_previous_winning: previousPreviousWinning,
            previous_rehearsal: target === 'n3' ? previousN3Rehearsal : previousN4Rehearsal,
            previous_previous_rehearsal: target === 'n3' ? previousPreviousN3Rehearsal : previousPreviousN4Rehearsal,
            predicted_digits: chartData.expandedDigits || [...chartData.sourceDigits].sort((a, b) => a - b), // ソート済みの数字リストを表示
          });
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          console.error(`[CUBE API Route] 現罫線 ${target} ${pattern} のCUBE生成に失敗:`, errorMsg, error);
          // エラーが発生しても続行
        }
      }
    }

    // 欠番補足あり/なしの抽出数字を事前に取得（新罫線）
    const newExtractedDigits: {
      [target: string]: { withMissingFill: number[]; withoutMissingFill: number[] };
    } = {};
    for (const target of targets) {
      try {
        newExtractedDigits[target] = await extractPredictedDigitsByMissingFill(
          roundNumberInt,
          target,
          'new'
        );
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        console.error(`[CUBE API Route] 新罫線 ${target} の抽出数字取得に失敗:`, errorMsg, error);
        throw error; // 抽出数字の取得に失敗した場合はエラーを投げる
      }
    }

    // 通常CUBE: 新罫線 × 4パターン（A1, A2, B1, B2） × N3/N4 = 8個
    console.log('[CUBE API Route] 通常CUBE（新罫線）の生成を開始...');
    for (const target of targets) {
      const previousWinning = target === 'n3' ? previousN3 : previousN4;
      const previousPreviousWinning = target === 'n3' ? previousPreviousN3 : previousPreviousN4;

      for (const pattern of patterns) {
        try {
          const chartData = await generateChart(roundNumberInt, pattern, target, 'new');
          cubes.push({
            id: `new_normal_${target}_${pattern}`,
            keisen_type: 'new',
            cube_type: 'normal',
            target,
            pattern,
            grid: chartData.grid,
            rows: chartData.rows,
            cols: chartData.cols,
            previous_winning: previousWinning,
            previous_previous_winning: previousPreviousWinning,
            previous_rehearsal: target === 'n3' ? previousN3Rehearsal : previousN4Rehearsal,
            previous_previous_rehearsal: target === 'n3' ? previousPreviousN3Rehearsal : previousPreviousN4Rehearsal,
            predicted_digits: chartData.expandedDigits || [...chartData.sourceDigits].sort((a, b) => a - b), // ソート済みの数字リストを表示
          });
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          console.error(`[CUBE API Route] 新罫線 ${target} ${pattern} のCUBE生成に失敗:`, errorMsg, error);
          // エラーが発生しても続行
        }
      }
    }

    // 極CUBE: 現罫線 × 1パターン（N3のみ）
    console.log('[CUBE API Route] 極CUBE（現罫線）の生成を開始...');
    try {
      const extremeCube = await generateExtremeCube(roundNumberInt, 'current');
      // generateChartを呼び出してsourceDigitsを取得（極CUBEはB1パターン相当）
      const chartData = await generateChart(roundNumberInt, 'B1', 'n3', 'current');
      cubes.push({
        id: 'current_extreme_n3',
        keisen_type: 'current',
        cube_type: 'extreme',
        target: 'n3',
        pattern: null,
        grid: extremeCube.grid,
        rows: extremeCube.rows,
        cols: extremeCube.cols,
        previous_winning: previousN3,
        previous_previous_winning: previousPreviousN3,
        previous_rehearsal: previousN3Rehearsal,
        previous_previous_rehearsal: previousPreviousN3Rehearsal,
        predicted_digits: chartData.expandedDigits || [...chartData.sourceDigits].sort((a, b) => a - b), // ソート済みの数字リストを表示
      });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      console.error(`[CUBE API Route] 現罫線 極CUBE の生成に失敗:`, errorMsg, error);
      // エラーが発生しても続行
    }

    // 極CUBE: 新罫線 × 1パターン（N3のみ）
    console.log('[CUBE API Route] 極CUBE（新罫線）の生成を開始...');
    try {
      const extremeCube = await generateExtremeCube(roundNumberInt, 'new');
      // generateChartを呼び出してsourceDigitsを取得（極CUBEはB1パターン相当）
      const chartData = await generateChart(roundNumberInt, 'B1', 'n3', 'new');
      cubes.push({
        id: 'new_extreme_n3',
        keisen_type: 'new',
        cube_type: 'extreme',
        target: 'n3',
        pattern: null,
        grid: extremeCube.grid,
        rows: extremeCube.rows,
        cols: extremeCube.cols,
        previous_winning: previousN3,
        previous_previous_winning: previousPreviousN3,
        previous_rehearsal: previousN3Rehearsal,
        previous_previous_rehearsal: previousPreviousN3Rehearsal,
        predicted_digits: chartData.expandedDigits || [...chartData.sourceDigits].sort((a, b) => a - b), // ソート済みの数字リストを表示
      });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      console.error(`[CUBE API Route] 新罫線 極CUBE の生成に失敗:`, errorMsg, error);
      // エラーが発生しても続行
    }

    console.log(`[CUBE API Route] 成功: ${cubes.length}個のCUBEを生成しました`);
    console.log(`[CUBE API Route] レスポンス送信前:`, {
      round_number: roundNumberInt,
      current_winning: currentWinning,
      current_rehearsal: currentRehearsal,
      cubes_count: cubes.length,
    });

    return NextResponse.json({
      round_number: roundNumberInt,
      cubes,
      current_winning: currentWinning,
      current_rehearsal: currentRehearsal,
      extracted_digits: {
        current: {
          n3: currentExtractedDigits.n3,
          n4: currentExtractedDigits.n4,
        },
        new: {
          n3: newExtractedDigits.n3,
          n4: newExtractedDigits.n4,
        },
      },
    });
  } catch (error) {
    console.error('[CUBE API Route] エラー:', error);
    const errorMessage = error instanceof Error 
      ? error.message 
      : typeof error === 'string' 
        ? error 
        : 'Unknown error';
    const errorStack = error instanceof Error ? error.stack : undefined;
    console.error('[CUBE API Route] エラー詳細:', {
      message: errorMessage,
      stack: errorStack,
      error: error
    });
    return NextResponse.json(
      { 
        error: `サーバーエラー: ${errorMessage}`,
        detail: errorStack ? errorStack.split('\n').slice(0, 5).join('\n') : undefined
      },
      { status: 500 }
    );
  }
}
