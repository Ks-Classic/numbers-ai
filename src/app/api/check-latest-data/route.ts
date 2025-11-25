import { NextRequest, NextResponse } from 'next/server';
import * as cheerio from 'cheerio';

export const dynamic = 'force-dynamic';

const HPFREE_URL = 'https://www.hpfree.com/numbers/rehearsal.html';

interface RoundData {
    n3_rehearsal: string;
    n4_rehearsal: string;
    n3_winning: string;
    n4_winning: string;
}

/**
 * セル文字列から数値を抽出（取り消し線・括弧・矢印に対応）
 */
function extractNumberFromCell(cellText: string): string | null {
    if (!cellText) return null;
    let txt = cellText.trim();

    // 矢印（→）の後の数字を取得（例: 8→0）
    const arrowMatch = txt.match(/[→→→](\d+)/);
    if (arrowMatch) {
        return arrowMatch[1];
    }

    // 取り消し線を除去（U+0336 など）
    txt = txt.replace(/[\u0336\u0335\u0332]/g, '');
    // 括弧付き注釈を除去 (例: (不), (落))
    txt = txt.replace(/\([^)]*\)/g, '');
    // 数字だけ抽出
    const digits = txt.match(/\d/g);
    if (digits && digits.length > 0) {
        return digits[0];
    }
    return null;
}

/**
 * hpfree.comのページをパースして回号ごとのデータを取得
 */
function parsePage(html: string): Map<number, RoundData> {
    const $ = cheerio.load(html);
    const result = new Map<number, RoundData>();

    $('table').each((_, table) => {
        $(table).find('tr').each((_, row) => {
            const cells = $(row).find('td, th');
            if (cells.length === 0) return;

            const rowText = $(row).text();
            const roundMatch = rowText.match(/第(\d+)回/);
            if (!roundMatch) return;

            const rnd = parseInt(roundMatch[1], 10);

            // 初期化または取得
            if (!result.has(rnd)) {
                result.set(rnd, {
                    n3_rehearsal: 'NULL',
                    n4_rehearsal: 'NULL',
                    n3_winning: 'NULL',
                    n4_winning: 'NULL',
                });
            }
            const entry = result.get(rnd)!;

            // N4 テーブルは 10 列以上、N3 は 8 列以上
            if (cells.length >= 10) {
                // N4 リハーサル 4桁 (1~4 列)
                const n4Re: string[] = [];
                for (let i = 1; i <= 4; i++) {
                    const d = extractNumberFromCell($(cells[i]).text());
                    if (d) n4Re.push(d);
                }
                // N4 当選 4桁 (6~9 列)
                const n4Win: string[] = [];
                for (let i = 6; i <= 9; i++) {
                    const d = extractNumberFromCell($(cells[i]).text());
                    if (d) n4Win.push(d);
                }

                if (n4Re.length === 4) {
                    entry.n4_rehearsal = n4Re.join('');
                }
                if (n4Win.length === 4) {
                    entry.n4_winning = n4Win.join('');
                }
            } else if (cells.length >= 8) {
                // N3 リハーサル 3桁 (1~3 列)
                const n3Re: string[] = [];
                for (let i = 1; i <= 3; i++) {
                    const d = extractNumberFromCell($(cells[i]).text());
                    if (d) n3Re.push(d);
                }
                // N3 当選 3桁 (5~7 列)
                const n3Win: string[] = [];
                for (let i = 5; i <= 7; i++) {
                    const d = extractNumberFromCell($(cells[i]).text());
                    if (d) n3Win.push(d);
                }

                if (n3Re.length === 3) {
                    entry.n3_rehearsal = n3Re.join('');
                }
                if (n3Win.length === 3) {
                    entry.n3_winning = n3Win.join('');
                }
            }
        });
    });

    return result;
}

/**
 * CSVをパースして回号ごとのデータを取得
 */
function parseCsv(csvContent: string): Map<number, Record<string, string>> {
    const lines = csvContent.trim().split('\n');
    const result = new Map<number, Record<string, string>>();

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        const cols = line.split(',');
        const rnd = parseInt(cols[0], 10);
        if (isNaN(rnd)) continue;

        result.set(rnd, {
            round_number: cols[0],
            draw_date: cols[1] || 'NULL',
            weekday: cols[2] || 'NULL',
            n3_rehearsal: cols[3] || 'NULL',
            n4_rehearsal: cols[4] || 'NULL',
            n3_winning: cols[5] || 'NULL',
            n4_winning: cols[6] || 'NULL',
        });
    }

    return result;
}

/**
 * データをCSV形式に変換
 */
function toCsv(data: Map<number, Record<string, string>>): string {
    const header = 'round_number,draw_date,weekday,n3_rehearsal,n4_rehearsal,n3_winning,n4_winning';
    const rounds = Array.from(data.keys()).sort((a, b) => b - a); // 降順

    const rows = rounds.map(rnd => {
        const row = data.get(rnd)!;
        return `${row.round_number},${row.draw_date},${row.weekday},${row.n3_rehearsal},${row.n4_rehearsal},${row.n3_winning},${row.n4_winning}`;
    });

    return header + '\n' + rows.join('\n') + '\n';
}

/**
 * 当選番号が有効かどうかをチェック
 */
function hasValidWinningData(data: Map<number, Record<string, string>>, roundNum: number): boolean {
    const row = data.get(roundNum);
    if (!row) return false;
    if (row.n3_winning === 'NULL' || row.n3_winning === '' ||
        row.n4_winning === 'NULL' || row.n4_winning === '') {
        return false;
    }
    return true;
}

/**
 * 最新データ確認API
 * 
 * GET /api/check-latest-data?round=6865
 */
export async function GET(request: NextRequest) {
    try {
        const searchParams = request.nextUrl.searchParams;
        const roundStr = searchParams.get('round');
        const targetRound = roundStr ? parseInt(roundStr, 10) : null;

        const PAT_TOKEN = process.env.PAT_TOKEN;
        const GITHUB_REPO = process.env.GITHUB_REPO || 'Ks-Classic/numbers-ai';
        const GITHUB_BRANCH = process.env.GITHUB_BRANCH || 'main';

        if (!PAT_TOKEN) {
            return NextResponse.json({ error: 'PAT_TOKENが設定されていません' }, { status: 500 });
        }

        // 1. GitHubからCSVを取得
        const fileUrl = `https://api.github.com/repos/${GITHUB_REPO}/contents/data/past_results.csv?ref=${GITHUB_BRANCH}`;
        const getResponse = await fetch(fileUrl, {
            headers: {
                'Authorization': `Bearer ${PAT_TOKEN}`,
                'Accept': 'application/vnd.github.v3+json',
            },
            cache: 'no-store',
        });

        if (!getResponse.ok) {
            throw new Error(`GitHub CSV取得失敗: ${getResponse.status}`);
        }

        const fileData = await getResponse.json();
        const csvContent = Buffer.from(fileData.content, 'base64').toString('utf-8');
        const existingData = parseCsv(csvContent);

        // 2. 必要なデータがあるかチェック
        let hasRequiredData = true;
        let needsFetch = false;

        if (targetRound) {
            // 前回・前々回のデータチェック
            if (!hasValidWinningData(existingData, targetRound - 1)) {
                hasRequiredData = false;
                needsFetch = true;
            }
            if (!hasValidWinningData(existingData, targetRound - 2)) {
                hasRequiredData = false;
                needsFetch = true;
            }
            // 当該回のデータがまだない場合もチェック
            if (!hasValidWinningData(existingData, targetRound)) {
                needsFetch = true;
            }
        }

        // 3. 対象回のデータを取得
        const targetRoundData = targetRound ? existingData.get(targetRound) : null;

        return NextResponse.json({
            success: true,
            hasRequiredData,
            needsFetch,
            latestRound: Math.max(...Array.from(existingData.keys())),
            targetRoundData: targetRoundData ? {
                round: targetRound,
                n3Rehearsal: targetRoundData.n3_rehearsal === 'NULL' ? null : targetRoundData.n3_rehearsal,
                n4Rehearsal: targetRoundData.n4_rehearsal === 'NULL' ? null : targetRoundData.n4_rehearsal,
                n3Winning: targetRoundData.n3_winning === 'NULL' ? null : targetRoundData.n3_winning,
                n4Winning: targetRoundData.n4_winning === 'NULL' ? null : targetRoundData.n4_winning,
            } : null,
        });

    } catch (error) {
        console.error('[API] データ確認エラー:', error);
        return NextResponse.json(
            { error: 'データの確認に失敗しました', details: error instanceof Error ? error.message : String(error) },
            { status: 500 }
        );
    }
}
