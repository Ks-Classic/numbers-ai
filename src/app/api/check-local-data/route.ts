import { NextRequest, NextResponse } from 'next/server';
import { loadPastResults } from '@/lib/data-loader/past-results';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
    try {
        const searchParams = request.nextUrl.searchParams;
        const roundStr = searchParams.get('round');

        if (!roundStr) {
            return NextResponse.json({ error: 'Round number is required' }, { status: 400 });
        }

        const round = parseInt(roundStr, 10);
        const results = await loadPastResults();

        // Check for N-1 and N-2
        const prev1 = results.find(r => r.roundNumber === round - 1);
        const prev2 = results.find(r => r.roundNumber === round - 2);

        // Check for Rehearsal for N
        const current = results.find(r => r.roundNumber === round);

        const hasRequiredData = !!(prev1 && prev2);

        return NextResponse.json({
            success: true,
            hasRequiredData,
            currentData: current ? {
                n3Rehearsal: current.n3Rehearsal,
                n4Rehearsal: current.n4Rehearsal
            } : null
        });

    } catch (error) {
        console.error('[API] ローカルデータ確認エラー:', error);
        return NextResponse.json(
            { error: 'ローカルデータの確認に失敗しました' },
            { status: 500 }
        );
    }
}
