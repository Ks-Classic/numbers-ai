/**
 * データ読み込みユーティリティの動作確認API
 * 
 * GET /api/test-data-loader
 */

import { NextResponse } from 'next/server';
import {
  loadPastResults,
  getPastResultByRoundNumber,
  getPreviousResult,
  getPreviousPreviousResult,
  loadKeisenMaster,
  getPredictedDigits,
} from '@/lib/data-loader';

export async function GET() {
  const results: {
    success: boolean;
    csv?: {
      total: number;
      samples: Array<{
        roundNumber: number;
        drawDate: string;
        n3Winning: string;
        n4Winning: string;
      }>;
      specificRound?: {
        roundNumber: number;
        drawDate: string;
        n3Winning: string;
        n4Winning: string;
        n3Rehearsal: string | null;
        n4Rehearsal: string | null;
      };
      previous?: {
        roundNumber: number;
        n3Winning: string;
        n4Winning: string;
      };
      previousPrevious?: {
        roundNumber: number;
        n3Winning: string;
        n4Winning: string;
      };
    };
    json?: {
      n3Columns: string[];
      n4Columns: string[];
      predictedDigits: Array<{
        target: string;
        column: string;
        previous: number;
        previousPrevious: number;
        digits: number[];
      }>;
      cacheTest: {
        firstLoad: number;
        secondLoad: number;
        cached: boolean;
      };
    };
    error?: string;
  } = {
    success: false,
  };

  try {
    // CSV読み込みのテスト
    const csvResults = await loadPastResults();
    results.csv = {
      total: csvResults.length,
      samples: csvResults.slice(0, 5).map((r) => ({
        roundNumber: r.roundNumber,
        drawDate: r.drawDate,
        n3Winning: r.n3Winning,
        n4Winning: r.n4Winning,
      })),
    };

    // 特定の回号を取得
    const testRoundNumber = 6758;
    const specificResult = await getPastResultByRoundNumber(testRoundNumber);
    if (specificResult) {
      results.csv.specificRound = specificResult;
    }

    // 前回・前々回の取得
    const previous = await getPreviousResult(testRoundNumber);
    const previousPrevious = await getPreviousPreviousResult(testRoundNumber);
    if (previous) {
      results.csv.previous = {
        roundNumber: previous.roundNumber,
        n3Winning: previous.n3Winning,
        n4Winning: previous.n4Winning,
      };
    }
    if (previousPrevious) {
      results.csv.previousPrevious = {
        roundNumber: previousPrevious.roundNumber,
        n3Winning: previousPrevious.n3Winning,
        n4Winning: previousPrevious.n4Winning,
      };
    }

    // JSON読み込みのテスト
    const start1 = Date.now();
    const master = await loadKeisenMaster();
    const time1 = Date.now() - start1;

    const start2 = Date.now();
    await loadKeisenMaster(true);
    const time2 = Date.now() - start2;

    results.json = {
      n3Columns: Object.keys(master.n3),
      n4Columns: Object.keys(master.n4),
      predictedDigits: [],
      cacheTest: {
        firstLoad: time1,
        secondLoad: time2,
        cached: time2 < time1,
      },
    };

    // 予測出目の取得テスト
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
      results.json.predictedDigits.push({
        target: testCase.target,
        column: testCase.column,
        previous: testCase.prev,
        previousPrevious: testCase.prevPrev,
        digits,
      });
    }

    results.success = true;
  } catch (error) {
    results.error =
      error instanceof Error ? error.message : String(error);
    return NextResponse.json(results, { status: 500 });
  }

  return NextResponse.json(results);
}

