/**
 * 予測表生成のテスト用APIエンドポイント
 * 
 * GET /api/test-chart?roundNumber=6758&pattern=A&target=n3
 */

import { NextRequest, NextResponse } from 'next/server';
import { generateChart } from '@/lib/chart-generator';
import type { Pattern, Target } from '@/types/prediction';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const roundNumber = parseInt(searchParams.get('roundNumber') || '6758', 10);
  const pattern = (searchParams.get('pattern') || 'A1') as Pattern;
  const target = (searchParams.get('target') || 'n3') as Target;

  try {
    const chartData = await generateChart(roundNumber, pattern, target);

    // グリッドを文字列形式で整形（見やすくするため）
    const gridString = chartData.grid.map(row => 
      row.map(cell => cell === null ? '.' : String(cell)).join(' ')
    ).join('\n');

    return NextResponse.json({
      success: true,
      roundNumber,
      pattern,
      target,
      chartData: {
        rows: chartData.rows,
        cols: chartData.cols,
        sourceDigits: chartData.sourceDigits,
        grid: chartData.grid,
        gridString, // 見やすい形式
      },
    }, {
      headers: {
        'Content-Type': 'application/json',
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

