/**
 * 予測実行APIエンドポイント
 * 
 * POST /api/predict
 * 
 * 回号とリハーサル数字を受け取り、AI予測結果を返す。
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import {
  predictAxis,
  predictCombination,
  fetchAndUpdateData,
  type CombinationPredictionResult
} from '@/lib/predictor/vercel-python';

/**
 * リクエストスキーマ
 */
const PredictRequestSchema = z.object({
  roundNumber: z.number().int().min(1).max(9999),
  n3Rehearsal: z.string().regex(/^[0-9]{3}$/).optional(),
  n4Rehearsal: z.string().regex(/^[0-9]{4}$/).optional(),
  useGitHubData: z.boolean().optional(),
});

type PredictRequest = z.infer<typeof PredictRequestSchema>;

/**
 * 環境変数の確認（Vercel Python関数を使用するかどうか）
 */
const USE_VERCEL_PYTHON = process.env.USE_VERCEL_PYTHON === 'true';

import { fetchPastResultsFromGitHub } from '@/lib/data-loader/github-data';

/**
 * POSTハンドラー
 */
export async function POST(request: NextRequest) {
  try {
    console.log('=== Next.js API Route: /api/predict 開始 ===');

    // リクエストボディを取得
    const body = await request.json();

    console.log('リクエストボディ:', {
      roundNumber: body.roundNumber,
      hasN3Rehearsal: !!body.n3Rehearsal,
      hasN4Rehearsal: !!body.n4Rehearsal,
      useGitHubData: body.useGitHubData,
    });

    // バリデーション
    const validationResult = PredictRequestSchema.safeParse(body);

    if (!validationResult.success) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid input data',
            details: validationResult.error.issues.map((err) => ({
              field: err.path.join('.'),
              message: err.message,
            })),
          },
        },
        { status: 400 }
      );
    }

    const data = validationResult.data;

    // GitHubデータの取得（必要な場合）
    let csvContent: string | undefined = undefined;
    if (data.useGitHubData) {
      try {
        console.log('GitHubから最新データを取得中...');
        csvContent = await fetchPastResultsFromGitHub();
        console.log('GitHubデータ取得成功');

        // データ不足チェック: 前回・前々回の当選番号があるか確認
        const lines = csvContent.split('\n');
        const roundNumbers = new Map<number, string>();
        for (const line of lines.slice(1)) {
          if (!line.trim()) continue;
          const cols = line.split(',');
          const rnd = parseInt(cols[0], 10);
          const n3Winning = cols[5];
          const n4Winning = cols[6];
          roundNumbers.set(rnd, `${n3Winning},${n4Winning}`);
        }

        // 前回(n-1)と前々回(n-2)の当選番号をチェック
        const prevData = roundNumbers.get(data.roundNumber - 1);
        const prevPrevData = roundNumbers.get(data.roundNumber - 2);

        const isDataMissing = (dataStr: string | undefined) => {
          if (!dataStr) return true;
          const [n3, n4] = dataStr.split(',');
          return n3 === 'NULL' || n4 === 'NULL' || !n3 || !n4;
        };

        if (isDataMissing(prevData) || isDataMissing(prevPrevData)) {
          console.log('⚠ データ不足を検出。Webから最新データを取得します...');
          console.log(`  前回(${data.roundNumber - 1}): ${prevData || '未登録'}`);
          console.log(`  前々回(${data.roundNumber - 2}): ${prevPrevData || '未登録'}`);

          try {
            const fetchResult = await fetchAndUpdateData(data.roundNumber);
            console.log('データ更新結果:', fetchResult);

            if (fetchResult.success && fetchResult.csv_content) {
              csvContent = fetchResult.csv_content;
              console.log('✅ 最新データを取得しました');
            } else if (!fetchResult.updated) {
              // Webにもデータがない場合
              console.warn('⚠ Webにもデータがありません:', fetchResult.message);
            }
          } catch (fetchError) {
            console.error('データ自動取得エラー:', fetchError);
            // エラーでも続行（元のデータで試行）
          }
        }
      } catch (error) {
        console.error('GitHubデータ取得失敗:', error);
        // エラーでも続行するか、エラーを返すか？
        // ここではエラーとして返す
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'GITHUB_DATA_ERROR',
              message: 'Failed to fetch data from GitHub',
            },
          },
          { status: 500 }
        );
      }
    }

    // リハーサル数字のチェック
    if (!data.n3Rehearsal && !data.n4Rehearsal) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'At least one rehearsal number (n3Rehearsal or n4Rehearsal) is required',
          },
        },
        { status: 400 }
      );
    }

    // 予測結果を格納するオブジェクト
    const result: {
      roundNumber: number;
      n3?: {
        box: {
          axisCandidates: Array<{
            digit: number;
            score: number;
            confidence: number;
            source: string;
          }>;
          numberCandidates: Array<{
            numbers: string;
            score: number;
            confidence: number;
            source: string;
            rank: number;
          }>;
        };
        straight: {
          axisCandidates: Array<{
            digit: number;
            score: number;
            confidence: number;
            source: string;
          }>;
          numberCandidates: Array<{
            numbers: string;
            score: number;
            confidence: number;
            source: string;
            rank: number;
          }>;
        };
      };
      n4?: {
        box: {
          axisCandidates: Array<{
            digit: number;
            score: number;
            confidence: number;
            source: string;
          }>;
          numberCandidates: Array<{
            numbers: string;
            score: number;
            confidence: number;
            source: string;
            rank: number;
          }>;
        };
        straight: {
          axisCandidates: Array<{
            digit: number;
            score: number;
            confidence: number;
            source: string;
          }>;
          numberCandidates: Array<{
            numbers: string;
            score: number;
            confidence: number;
            source: string;
            rank: number;
          }>;
        };
      };
      generatedAt: string;
    } = {
      roundNumber: data.roundNumber,
      generatedAt: new Date().toISOString(),
    };

    // N3の予測
    const runNodePrediction = async (
      roundNumber: number,
      target: 'n3' | 'n4',
      rehearsalDigits: string
    ) => {
      const axisResult = await predictAxis(roundNumber, target, rehearsalDigits, csvContent);

      const topAxisDigits = axisResult.axis_candidates
        .slice(0, 10)
        .map((item: any) => item.digit);

      let boxCombinations: CombinationPredictionResult['combinations'] | null = null;
      let straightCombinations: CombinationPredictionResult['combinations'] | null = null;

      try {
        const boxResponse = await predictCombination(
          roundNumber,
          target,
          'box',
          axisResult.best_pattern,
          topAxisDigits,
          rehearsalDigits,
          csvContent,
          data.n3Rehearsal,
          data.n4Rehearsal
        );
        boxCombinations = boxResponse.combinations || [];
      } catch (error: any) {
        if (
          error?.message?.includes('モデルが見つかりません') ||
          error?.message?.includes('モデルが読み込まれていません')
        ) {
          boxCombinations = [];
        } else {
          throw error;
        }
      }

      try {
        const straightResponse = await predictCombination(
          roundNumber,
          target,
          'straight',
          axisResult.best_pattern,
          topAxisDigits,
          rehearsalDigits,
          csvContent,
          data.n3Rehearsal,
          data.n4Rehearsal
        );
        straightCombinations = straightResponse.combinations || [];
      } catch (error: any) {
        if (
          error?.message?.includes('モデルが見つかりません') ||
          error?.message?.includes('モデルが読み込まれていません')
        ) {
          straightCombinations = [];
        } else {
          throw error;
        }
      }

      return {
        bestPattern: axisResult.best_pattern,
        patternScores: axisResult.pattern_scores,
        box: {
          axisCandidates: axisResult.axis_candidates,
          numberCandidates: boxCombinations,
        },
        straight: {
          axisCandidates: axisResult.axis_candidates,
          numberCandidates: straightCombinations,
        },
      };
    };

    if (data.n3Rehearsal) {
      const n3Result = await runNodePrediction(
        data.roundNumber,
        'n3',
        data.n3Rehearsal
      );

      result.n3 = {
        box: {
          axisCandidates: n3Result.box.axisCandidates.map((item) => ({
            digit: item.digit,
            score: item.score,
            confidence: Math.round(item.score / 10), // スコアを0-100に変換
            source: item.pattern,
          })),
          numberCandidates: n3Result.box.numberCandidates.map((item, index) => ({
            numbers: item.combination,
            score: item.score,
            confidence: Math.round(item.score / 10),
            source: n3Result.bestPattern,
            rank: index + 1,
          })),
        },
        straight: {
          axisCandidates: n3Result.straight.axisCandidates.map((item) => ({
            digit: item.digit,
            score: item.score,
            confidence: Math.round(item.score / 10),
            source: item.pattern,
          })),
          numberCandidates: n3Result.straight.numberCandidates.map((item, index) => ({
            numbers: item.combination,
            score: item.score,
            confidence: Math.round(item.score / 10),
            source: n3Result.bestPattern,
            rank: index + 1,
          })),
        },
      };
    }

    // N4の予測
    if (data.n4Rehearsal) {
      console.log('N4予測開始:', {
        roundNumber: data.roundNumber,
        rehearsal: data.n4Rehearsal,
      });

      const n4Result = await runNodePrediction(
        data.roundNumber,
        'n4',
        data.n4Rehearsal
      );

      console.log('N4予測結果:', {
        axisCandidatesCount: n4Result.box.axisCandidates.length,
        boxNumberCandidatesCount: n4Result.box.numberCandidates.length,
        straightNumberCandidatesCount: n4Result.straight.numberCandidates.length,
        bestPattern: n4Result.bestPattern,
      });

      result.n4 = {
        box: {
          axisCandidates: n4Result.box.axisCandidates.map((item) => ({
            digit: item.digit,
            score: item.score,
            confidence: Math.round(item.score / 10),
            source: item.pattern,
          })),
          numberCandidates: n4Result.box.numberCandidates.map((item, index) => ({
            numbers: item.combination,
            score: item.score,
            confidence: Math.round(item.score / 10),
            source: n4Result.bestPattern,
            rank: index + 1,
          })),
        },
        straight: {
          axisCandidates: n4Result.straight.axisCandidates.map((item) => ({
            digit: item.digit,
            score: item.score,
            confidence: Math.round(item.score / 10),
            source: item.pattern,
          })),
          numberCandidates: n4Result.straight.numberCandidates.map((item, index) => ({
            numbers: item.combination,
            score: item.score,
            confidence: Math.round(item.score / 10),
            source: n4Result.bestPattern,
            rank: index + 1,
          })),
        },
      };
    }

    console.log('=== 予測結果サマリー ===');
    console.log('N3データ:', {
      hasData: !!result.n3,
      axisCandidatesCount: result.n3?.box.axisCandidates.length || 0,
      boxNumberCandidatesCount: result.n3?.box.numberCandidates.length || 0,
    });
    console.log('N4データ:', {
      hasData: !!result.n4,
      axisCandidatesCount: result.n4?.box.axisCandidates.length || 0,
      boxNumberCandidatesCount: result.n4?.box.numberCandidates.length || 0,
    });
    console.log('========================');

    return NextResponse.json({
      success: true,
      data: result,
    });

  } catch (error) {
    console.error('予測APIエラー:', error);

    // エラーの種類に応じて適切なステータスコードを返す
    if (error instanceof Error) {
      if (error.message.includes('VALIDATION_ERROR') || error.message.includes('Invalid')) {
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'VALIDATION_ERROR',
              message: error.message,
            },
          },
          { status: 400 }
        );
      }

      if (error.message.includes('NOT_FOUND') || error.message.includes('見つかりません')) {
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'DATA_NOT_FOUND',
              message: error.message,
            },
          },
          { status: 404 }
        );
      }

      if (error.message.includes('MODEL') || error.message.includes('モデル')) {
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'MODEL_ERROR',
              message: error.message,
            },
          },
          { status: 500 }
        );
      }
    }

    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: error instanceof Error ? error.message : 'Internal server error',
        },
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONSハンドラー（CORSプリフライトリクエスト用）
 */
export async function OPTIONS(request: NextRequest) {
  return NextResponse.json(
    {},
    {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    }
  );
}
