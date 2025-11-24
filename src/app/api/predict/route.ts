/**
 * 予測実行APIエンドポイント（デバッグ版）
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    console.log('[DEBUG] POST handler called');

    const body = await request.json();
    console.log('[DEBUG] Request body:', body);

    return NextResponse.json({
      success: true,
      message: 'POST handler is working',
      receivedData: body,
      timestamp: new Date().toISOString()
    }, { status: 200 });

  } catch (error) {
    console.error('[DEBUG] Error:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

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
