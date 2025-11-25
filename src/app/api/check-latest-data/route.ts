import { NextRequest, NextResponse } from 'next/server';
import { fetchPastResultsFromGitHub } from '@/lib/data-loader/github-data';
import { loadPastResults } from '@/lib/data-loader/past-results';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
    try {
        const searchParams = request.nextUrl.searchParams;
        const roundStr = searchParams.get('round');
        const round = roundStr ? parseInt(roundStr, 10) : null;

        // 1. GitHubから最新データを取得
        console.log('[API] GitHubから最新データを取得中...');
        const csvContent = await fetchPastResultsFromGitHub();

        // 2. CSVをパースして最新回号とリクエストされた回号のデータを特定
        const lines = csvContent.trim().split('\n');
        const headers = lines[0].split(',').map(h => h.trim());

        // ヘッダーインデックス
        const roundIdx = headers.indexOf('round_number');
        const n3RehearsalIdx = headers.indexOf('n3_rehearsal');
        const n4RehearsalIdx = headers.indexOf('n4_rehearsal');
        const n3WinningIdx = headers.indexOf('n3_winning');
        const n4WinningIdx = headers.indexOf('n4_winning');

        let latestRound = 0;
        let targetRoundData = null;
        let previousRoundData = null; // 前回 (round - 1)
        let previousPreviousRoundData = null; // 前々回 (round - 2)

        // データ行を解析 (1行目はヘッダーなのでスキップ)
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;

            const cols = line.split(',').map(c => c.trim());
            const currentRound = parseInt(cols[roundIdx], 10);

            if (!isNaN(currentRound)) {
                if (currentRound > latestRound) {
                    latestRound = currentRound;
                }

                if (round) {
                    if (currentRound === round) {
                        targetRoundData = {
                            round: currentRound,
                            n3Rehearsal: cols[n3RehearsalIdx] === 'NULL' ? null : cols[n3RehearsalIdx],
                            n4Rehearsal: cols[n4RehearsalIdx] === 'NULL' ? null : cols[n4RehearsalIdx],
                        };
                    }
                    if (currentRound === round - 1) {
                        previousRoundData = {
                            round: currentRound,
                            n3Winning: cols[n3WinningIdx] === 'NULL' ? null : cols[n3WinningIdx],
                            n4Winning: cols[n4WinningIdx] === 'NULL' ? null : cols[n4WinningIdx],
                        };
                    }
                    if (currentRound === round - 2) {
                        previousPreviousRoundData = {
                            round: currentRound,
                            n3Winning: cols[n3WinningIdx] === 'NULL' ? null : cols[n3WinningIdx],
                            n4Winning: cols[n4WinningIdx] === 'NULL' ? null : cols[n4WinningIdx],
                        };
                    }
                }
            }
        }

        return NextResponse.json({
            success: true,
            latestRound,
            targetRoundData,
            previousRoundData,
            previousPreviousRoundData,
            hasRequiredData: !!(previousRoundData && previousPreviousRoundData),
            csvContent: csvContent.substring(0, 1000) + '...' // デバッグ用
        });

    } catch (error) {
        console.error('[API] データ確認エラー:', error);
        return NextResponse.json(
            { error: 'データの確認に失敗しました', details: error instanceof Error ? error.message : String(error) },
            { status: 500 }
        );
    }
}
