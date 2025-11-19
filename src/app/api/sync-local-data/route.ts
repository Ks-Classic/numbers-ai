import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join } from 'path';
import { fetchPastResultsFromGitHub } from '@/lib/data-loader/github-data';

/**
 * ローカルファイルをGitHubの最新データで同期するAPI
 * ローカル環境でのみ使用（本番環境では不要）
 */
export async function POST() {
  console.log('[sync-local-data] API呼び出し開始');
  console.log('[sync-local-data] 環境変数:', {
    NODE_ENV: process.env.NODE_ENV,
    VERCEL: process.env.VERCEL,
  });
  
  try {
    // ローカル環境でのみ実行可能
    if (process.env.NODE_ENV === 'production' && process.env.VERCEL === '1') {
      console.log('[sync-local-data] ❌ 本番環境のため実行不可');
      return NextResponse.json(
        { error: '本番環境ではこのAPIは使用できません' },
        { status: 403 }
      );
    }

    console.log('[sync-local-data] GitHubから最新データを取得中...');
    // GitHubから最新データを取得
    const csvContent = await fetchPastResultsFromGitHub();
    console.log('[sync-local-data] GitHubからデータ取得完了:', {
      contentLength: csvContent.length,
      firstLine: csvContent.split('\n')[0],
    });
    
    // ローカルファイルに保存
    const csvPath = join(process.cwd(), 'data', 'past_results.csv');
    console.log('[sync-local-data] ローカルファイルに保存中:', csvPath);
    await fs.writeFile(csvPath, csvContent, 'utf-8');
    console.log('[sync-local-data] ✅ ローカルファイルに保存完了');
    
    // 最新回号を取得
    const lines = csvContent.trim().split('\n');
    let latestRoundNumber: number | null = null;
    if (lines.length >= 2) {
      const firstDataLine = lines[1];
      const columns = firstDataLine.split(',');
      latestRoundNumber = parseInt(columns[0], 10);
    }
    
    console.log('[sync-local-data] ✅ 同期完了:', {
      latestRoundNumber,
      dataCount: lines.length - 1,
    });
    
    return NextResponse.json({
      success: true,
      message: 'ローカルファイルをGitHubの最新データで更新しました',
      latestRoundNumber,
      dataCount: lines.length - 1,
    });
  } catch (error) {
    console.error('[sync-local-data] ❌ エラー:', error);
    return NextResponse.json(
      { 
        error: 'ローカルデータの同期に失敗しました',
        detail: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}

