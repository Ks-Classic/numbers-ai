/**
 * 予測表生成のテスト用APIエンドポイント（デバッグ版）
 * 
 * GET /api/test-chart-debug?roundNumber=6758&pattern=A&target=n3
 */

import { NextRequest, NextResponse } from 'next/server';
import { generateChart } from '@/lib/chart-generator';
import { getPreviousResult, getPreviousPreviousResult, getPredictedDigits } from '@/lib/data-loader';
import type { Pattern, Target } from '@/types/prediction';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const roundNumber = parseInt(searchParams.get('roundNumber') || '6758', 10);
  const pattern = (searchParams.get('pattern') || 'A1') as Pattern;
  const target = (searchParams.get('target') || 'n3') as Target;

  try {
    // デバッグ情報: 前回・前々回のデータを取得
    const previousResult = await getPreviousResult(roundNumber);
    const previousPreviousResult = await getPreviousPreviousResult(roundNumber);
    
    if (!previousResult || !previousPreviousResult) {
      return NextResponse.json({
        success: false,
        error: '前回または前々回のデータが見つかりません',
      }, { status: 500 });
    }

    const previousWinning = target === 'n3' 
      ? previousResult.n3Winning 
      : previousResult.n4Winning;
    
    const previousPreviousWinning = target === 'n3'
      ? previousPreviousResult.n3Winning
      : previousPreviousResult.n4Winning;

    const columnNames: Array<'百の位' | '十の位' | '一の位' | '千の位'> = target === 'n3' 
      ? ['百の位', '十の位', '一の位']
      : ['千の位', '百の位', '十の位', '一の位'];

    // 各桁の予測出目を取得
    const debugInfo: Array<{
      column: string;
      previousDigit: number;
      previousPreviousDigit: number;
      predictedDigits: number[];
    }> = [];

    for (const columnName of columnNames) {
      const digitIndex = columnNames.indexOf(columnName);
      const previousDigit = parseInt(previousWinning[digitIndex], 10);
      const previousPreviousDigit = parseInt(previousPreviousWinning[digitIndex], 10);
      
      const predictedDigits = await getPredictedDigits(
        target,
        columnName as any,
        previousDigit,
        previousPreviousDigit
      );

      debugInfo.push({
        column: columnName,
        previousDigit,
        previousPreviousDigit,
        predictedDigits,
      });
    }

    // 予測表を生成
    const chartData = await generateChart(roundNumber, pattern, target);

    return NextResponse.json({
      success: true,
      roundNumber,
      pattern,
      target,
      debug: {
        previousResult: {
          roundNumber: previousResult.roundNumber,
          winning: previousWinning,
        },
        previousPreviousResult: {
          roundNumber: previousPreviousResult.roundNumber,
          winning: previousPreviousWinning,
        },
        predictedDigitsByColumn: debugInfo,
        sourceDigits: chartData.sourceDigits,
      },
      chartData: {
        rows: chartData.rows,
        cols: chartData.cols,
        grid: chartData.grid,
      },
    });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      details: error instanceof Error ? error.stack : undefined,
    }, {
      status: 500,
    });
  }
}

