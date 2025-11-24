/**
 * 組み合わせ予測APIエンドポイント
 * 
 * POST /api/predict/combination
 * 
 * 軸数字から実際の当選番号（組み合わせ）を予測します。
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { predictCombination } from '@/lib/predictor/predictor';

/**
 * リクエストスキーマ
 */
const CombinationRequestSchema = z.object({
  round_number: z.number().int().min(1).max(9999),
  target: z.enum(['n3', 'n4']),
  combo_type: z.enum(['box', 'straight']),
  best_pattern: z.enum(['A1', 'A2', 'B1', 'B2']),
  top_axis_digits: z.array(z.number().int().min(0).max(9)).min(1).max(10),
  rehearsal_digits: z.string().optional(),
  max_combinations: z.number().int().min(1).max(1000).optional().default(100),
});

type CombinationRequest = z.infer<typeof CombinationRequestSchema>;

/**
 * POSTハンドラー
 */
export async function POST(request: NextRequest) {
  try {
    console.log('=== Next.js API Route: /api/predict/combination 開始 ===');

    // リクエストボディを取得
    const body = await request.json();

    console.log('リクエストボディ:', {
      round_number: body.round_number,
      target: body.target,
      combo_type: body.combo_type,
      best_pattern: body.best_pattern,
      top_axis_digits_count: body.top_axis_digits?.length,
      has_rehearsal_digits: !!body.rehearsal_digits,
      max_combinations: body.max_combinations,
    });

    // バリデーション
    const validationResult = CombinationRequestSchema.safeParse(body);

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

    // 組み合わせ予測を実行
    const result = await predictCombination(
      data.round_number,
      data.target,
      data.combo_type,
      data.best_pattern,
      data.top_axis_digits,
      data.rehearsal_digits
    );

    console.log('組み合わせ予測結果:', {
      combinationsCount: result.combinations?.length || 0,
    });

    return NextResponse.json({
      success: true,
      combinations: result.combinations || [],
    });

  } catch (error: any) {
    console.error('組み合わせ予測エラー:', error);

    // モデルが見つからない場合は空の結果を返す（エラーではなくスキップ）
    if (error?.message?.includes('モデルが見つかりません') ||
      error?.message?.includes('モデルが読み込まれていません')) {
      console.warn('組み合わせ予測モデルが見つかりません。空の結果を返します。');
      return NextResponse.json({
        success: true,
        combinations: [],
      });
    }

    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'PREDICTION_ERROR',
          message: error?.message || '予測処理中にエラーが発生しました',
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
