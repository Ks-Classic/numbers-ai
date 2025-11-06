/**
 * 予測実行APIエンドポイント
 * 
 * POST /api/predict
 * 
 * 回号とリハーサル数字を受け取り、AI予測結果を返す。
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { predictTarget } from '@/lib/predictor/predictor';

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
 * FastAPIサーバーのURL（環境変数から取得、デフォルトはローカル）
 */
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

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
    if (data.n3Rehearsal) {
      const n3Result = await predictTarget(
        FASTAPI_URL,
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
      
      const n4Result = await predictTarget(
        FASTAPI_URL,
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

