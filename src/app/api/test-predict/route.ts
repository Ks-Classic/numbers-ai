/**
 * テスト用の最小限のAPIエンドポイント
 */

import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    console.log('[TEST] GET handler called');
    return NextResponse.json({
        message: 'Test endpoint is working',
        method: 'GET',
        timestamp: new Date().toISOString()
    }, { status: 200 });
}

export async function POST(request: NextRequest) {
    console.log('[TEST] POST handler called');
    return NextResponse.json({
        message: 'POST handler is working',
        method: 'POST',
        timestamp: new Date().toISOString()
    }, { status: 200 });
}

export async function OPTIONS(request: NextRequest) {
    console.log('[TEST] OPTIONS handler called');
    return NextResponse.json({}, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        },
    });
}
