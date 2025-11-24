/**
 * 予測実行APIエンドポイント（サンプルデータ版）
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { sampleAxisCandidates, sampleAxisCandidatesN4 } from '@/lib/sample-data';

/**
 * リクエストスキーマ
 */
const PredictRequestSchema = z.object({
  roundNumber: z.number().int().min(1).max(9999),
  n3Rehearsal: z.string().regex(/^[0-9]{3}$/).optional(),
  n4Rehearsal: z.string().regex(/^[0-9]{4}$/).optional(),
});

type PredictRequest = z.infer<typeof PredictRequestSchema>;

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
    });

    // バリデーション
    const validationResult = PredictRequestSchema.safeParse(body);

    if (!validationResult.success) {
      return NextResponse.json(
        {
          success: false,
          error: 'Invalid request data',
          details: validationResult.error.errors,
        },
        { status: 400 }
      );
    }

    const { roundNumber, n3Rehearsal, n4Rehearsal } = validationResult.data;

    // サンプルデータを返す
    const response = {
      success: true,
      roundNumber,
      n3: n3Rehearsal ? {
        rehearsal: n3Rehearsal,
        axisCandidates: sampleAxisCandidates,
      } : null,
      n4: n4Rehearsal ? {
        rehearsal: n4Rehearsal,
        axisCandidates: sampleAxisCandidatesN4,
      } : null,
      timestamp: new Date().toISOString(),
    };

    console.log('=== 予測成功 ===');

    return NextResponse.json(response, { status: 200 });

  } catch (error) {
    console.error('予測エラー:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONSハンドラー（CORSプリフライトリクエスト用）
 */
export async function OPTIONS(request: NextRequest) {
  return NextResponse.json({}, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
