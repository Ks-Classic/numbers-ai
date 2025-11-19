import { NextResponse } from 'next/server';
import { readFileSync } from 'fs';
import { join } from 'path';
import { fetchPastResultsFromGitHub, shouldUseGitHubData } from '@/lib/data-loader/github-data';

/**
 * データの最新状態をチェックするAPI
 * CSVファイルの最新回号を取得して返す
 * 本番環境ではGitHubから、ローカル環境ではローカルファイルから取得
 */
export async function GET() {
  try {
    let csvContent: string;
    let lastModified: Date;
    const useGitHub = shouldUseGitHubData();
    
    console.log('[check-data-status] データソース決定:', {
      useGitHub,
      NODE_ENV: process.env.NODE_ENV,
      VERCEL: process.env.VERCEL,
      USE_GITHUB_DATA: process.env.USE_GITHUB_DATA,
    });
    
    // 環境に応じてデータソースを決定
    if (useGitHub) {
      // GitHubから取得
      console.log('[check-data-status] GitHubからpast_results.csvを取得中...');
      csvContent = await fetchPastResultsFromGitHub();
      // GitHubから取得した場合は現在時刻を使用（正確な更新日時は取得できない）
      lastModified = new Date();
      console.log('[check-data-status] GitHubからデータ取得完了:', {
        contentLength: csvContent.length,
        firstLine: csvContent.split('\n')[0],
      });
    } else {
      // ローカルファイルから取得
      console.log('[check-data-status] ローカルファイルからpast_results.csvを取得中...');
      const csvPath = join(process.cwd(), 'data', 'past_results.csv');
      csvContent = readFileSync(csvPath, 'utf-8');
      
      // ファイルの更新日時を取得
      const fs = require('fs');
      const stats = fs.statSync(csvPath);
      lastModified = stats.mtime;
      console.log('[check-data-status] ローカルファイルからデータ取得完了:', {
        contentLength: csvContent.length,
        firstLine: csvContent.split('\n')[0],
        lastModified: lastModified.toISOString(),
      });
    }
    
    const lines = csvContent.trim().split('\n');
    
    // ヘッダー行をスキップして、最初のデータ行から最新回号を取得
    if (lines.length < 2) {
      console.error('[check-data-status] ❌ データファイルが空です');
      return NextResponse.json(
        { error: 'データファイルが空です' },
        { status: 500 }
      );
    }
    
    // 最初のデータ行（最新のデータ）を取得
    const firstDataLine = lines[1];
    const columns = firstDataLine.split(',');
    const latestRoundNumber = parseInt(columns[0], 10);
    
    const source = useGitHub ? 'github' : 'local';
    console.log('[check-data-status] ✅ データ取得完了:', {
      latestRoundNumber,
      dataCount: lines.length - 1,
      source,
      lastModified: lastModified.toISOString(),
    });
    
    return NextResponse.json({
      success: true,
      latestRoundNumber,
      lastModified: lastModified.toISOString(),
      dataCount: lines.length - 1, // ヘッダーを除いたデータ行数
      source,
    });
  } catch (error) {
    console.error('[check-data-status] ❌ エラー:', error);
    return NextResponse.json(
      { 
        error: 'データ状態の取得に失敗しました',
        detail: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}

