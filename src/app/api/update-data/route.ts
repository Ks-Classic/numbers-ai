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
 * データ更新API
 * 
 * POST /api/update-data
 * 
 * リクエストボディ:
 * {
 *   "roundNumber": 6865 // 対象回号
 * }
 */
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const targetRound = body.roundNumber || body.round;

        const PAT_TOKEN = process.env.PAT_TOKEN;
        const GITHUB_REPO = process.env.GITHUB_REPO || 'Ks-Classic/numbers-ai';
        const GITHUB_BRANCH = process.env.GITHUB_BRANCH || 'main';

        if (!PAT_TOKEN) {
            return NextResponse.json({ error: 'PAT_TOKENが設定されていません' }, { status: 500 });
        }

        console.log(`[API] データ更新開始: 回号=${targetRound || '指定なし'}`);

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
        const sha = fileData.sha;
        const existingData = parseCsv(csvContent);

        console.log(`[API] 既存データ: ${existingData.size}件`);

        // 2. hpfree.comからスクレイピング
        console.log(`[API] hpfree.comからデータ取得中...`);
        const webResponse = await fetch(HPFREE_URL, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        });

        if (!webResponse.ok) {
            throw new Error(`hpfree.com取得失敗: ${webResponse.status}`);
        }

        // Shift_JISでデコード（hpfree.comはShift_JISを使用）
        const buffer = await webResponse.arrayBuffer();
        const decoder = new TextDecoder('shift-jis');
        const html = decoder.decode(buffer);
        const webData = parsePage(html);

        console.log(`[API] Webから ${webData.size} 件の回号データを取得`);

        // 3. 更新対象を決定
        const roundsToCheck: number[] = [];
        if (targetRound) {
            roundsToCheck.push(targetRound - 2, targetRound - 1, targetRound);
        } else {
            roundsToCheck.push(...Array.from(webData.keys()));
        }

        // 4. データをマージ
        let updatedCount = 0;
        for (const rnd of roundsToCheck) {
            if (rnd <= 0) continue;
            const webRow = webData.get(rnd);
            if (!webRow) continue;

            if (existingData.has(rnd)) {
                // 既存行あり -> NULL項目のみ更新
                const row = existingData.get(rnd)!;
                let changed = false;
                for (const key of ['n3_rehearsal', 'n4_rehearsal', 'n3_winning', 'n4_winning'] as const) {
                    const newVal = webRow[key];
                    const oldVal = row[key];
                    if (newVal && newVal !== 'NULL' && newVal !== oldVal) {
                        row[key] = newVal;
                        changed = true;
                    }
                }
                if (changed) {
                    updatedCount++;
                }
            } else {
                // 新規追加
                existingData.set(rnd, {
                    round_number: String(rnd),
                    draw_date: 'NULL',
                    weekday: 'NULL',
                    n3_rehearsal: webRow.n3_rehearsal,
                    n4_rehearsal: webRow.n4_rehearsal,
                    n3_winning: webRow.n3_winning,
                    n4_winning: webRow.n4_winning,
                });
                updatedCount++;
                console.log(`[API] 第${rnd}回を追加`);
            }
        }

        console.log(`[API] 更新対象: ${updatedCount}件`);

        // 5. 更新があればGitHubにコミット
        if (updatedCount > 0) {
            const newCsvContent = toCsv(existingData);

            const updateResponse = await fetch(fileUrl, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${PAT_TOKEN}`,
                    'Accept': 'application/vnd.github.v3+json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: `chore: データ更新 (${updatedCount}件) [skip ci]`,
                    content: Buffer.from(newCsvContent, 'utf-8').toString('base64'),
                    sha: sha,
                    branch: GITHUB_BRANCH,
                }),
            });

            if (!updateResponse.ok) {
                const errorData = await updateResponse.json();
                throw new Error(`GitHub更新失敗: ${JSON.stringify(errorData)}`);
            }

            const result = await updateResponse.json();
            console.log(`[API] GitHubに更新をコミット: ${result.commit?.html_url}`);
        }

        // 6. 結果を返す
        const targetRoundData = targetRound ? existingData.get(targetRound) : null;

        return NextResponse.json({
            success: true,
            updated_count: updatedCount,
            target_round: targetRound,
            data: targetRoundData ? {
                round_number: targetRound,
                n3_rehearsal: targetRoundData.n3_rehearsal === 'NULL' ? null : targetRoundData.n3_rehearsal,
                n4_rehearsal: targetRoundData.n4_rehearsal === 'NULL' ? null : targetRoundData.n4_rehearsal,
                n3_winning: targetRoundData.n3_winning === 'NULL' ? null : targetRoundData.n3_winning,
                n4_winning: targetRoundData.n4_winning === 'NULL' ? null : targetRoundData.n4_winning,
                exists: true,
            } : null,
        });

    } catch (error) {
        console.error('[API] データ更新エラー:', error);
        return NextResponse.json(
            {
                error: 'データ更新に失敗しました',
                detail: error instanceof Error ? error.message : String(error)
            },
            { status: 500 }
        );
    }
}
