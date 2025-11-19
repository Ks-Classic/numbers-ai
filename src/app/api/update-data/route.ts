import { NextRequest, NextResponse } from 'next/server';
import { readFileSync } from 'fs';
import { join } from 'path';
import { fetchPastResultsFromGitHub, shouldUseGitHubData } from '@/lib/data-loader/github-data';

/**
 * データ更新API
 * GitHub Actionsのワークフローを手動実行してデータを更新します
 * 事前に最新データかどうかをチェックします
 */
export async function POST(request: NextRequest) {
  try {
    // まず、現在のデータの最新回号を取得
    let currentLatestRound: number | null = null;
    try {
      let csvContent: string;
      
      // 環境に応じてデータソースを決定
      if (shouldUseGitHubData()) {
        // GitHubから取得
        csvContent = await fetchPastResultsFromGitHub();
      } else {
        // ローカルファイルから取得
        const csvPath = join(process.cwd(), 'data', 'past_results.csv');
        csvContent = readFileSync(csvPath, 'utf-8');
      }
      
      const lines = csvContent.trim().split('\n');
      if (lines.length >= 2) {
        const firstDataLine = lines[1];
        const columns = firstDataLine.split(',');
        currentLatestRound = parseInt(columns[0], 10);
      }
    } catch (error) {
      console.warn('現在のデータファイルの読み込みに失敗:', error);
    }

    // 外部から最新回号を取得（簡易版：GitHub Actionsに任せる）
    // 実際の最新回号チェックはGitHub Actions側で行うため、
    // ここではワークフローをトリガーするだけ
    
    // GitHub Actions APIを使用してワークフローを手動実行
    const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
    const GITHUB_REPO = process.env.GITHUB_REPO || 'Ks-Classic/numbers-ai';
    const WORKFLOW_FILE = 'auto-update-data.yml'; // ファイル名のみ（.github/workflows/からの相対パス）

    if (!GITHUB_TOKEN) {
      console.error('GITHUB_TOKENが設定されていません');
      return NextResponse.json(
        { error: 'GitHubトークンが設定されていません。環境変数GITHUB_TOKENを設定してください。' },
        { status: 500 }
      );
    }

    const apiUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;
    console.log(`GitHub Actions API呼び出し: ${apiUrl}`);
    console.log(`リポジトリ: ${GITHUB_REPO}`);
    console.log(`ワークフローファイル: ${WORKFLOW_FILE}`);
    console.log(`現在の最新回号: ${currentLatestRound || '不明'}`);

    // GitHub Actions APIでワークフローを手動実行
    // workflow_dispatchイベントをトリガー
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ref: 'main', // mainブランチで実行
      }),
    });

    const responseStatus = response.status;
    const responseText = await response.text();
    
    console.log(`GitHub Actions API レスポンス: ${responseStatus}`);
    console.log(`レスポンス本文: ${responseText}`);

    // GitHub Actions APIは成功時に204 No Contentを返すことがある
    if (responseStatus === 204 || (responseStatus >= 200 && responseStatus < 300)) {
      // ワークフローIDを取得（ファイル名から）
      // ワークフローIDを取得するために、ワークフローファイルのIDを取得
      const workflowInfoUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}`;
      let workflowId: string | null = null;
      
      try {
        const workflowInfoResponse = await fetch(workflowInfoUrl, {
          headers: {
            'Authorization': `Bearer ${GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json',
          },
        });
        
        if (workflowInfoResponse.ok) {
          const workflowInfo = await workflowInfoResponse.json();
          workflowId = workflowInfo.id?.toString() || WORKFLOW_FILE;
        } else {
          workflowId = WORKFLOW_FILE; // フォールバック
        }
      } catch (error) {
        console.warn('ワークフローID取得に失敗:', error);
        workflowId = WORKFLOW_FILE; // フォールバック
      }
      
      return NextResponse.json({
        success: true,
        message: 'データ更新を開始しました。数分後に完了します。',
        detail: `GitHub Actionsワークフローをトリガーしました（ステータス: ${responseStatus}）。GitHubリポジトリの「Actions」タブで実行状況を確認できます。`,
        workflowUrl: `https://github.com/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}`,
        workflowId: workflowId,
        currentLatestRound,
      });
    }

    // エラーレスポンスの場合
    let errorDetail;
    try {
      errorDetail = JSON.parse(responseText);
    } catch {
      errorDetail = responseText;
    }

    console.error(`GitHub Actions API エラー: ${responseStatus} - ${JSON.stringify(errorDetail)}`);
    
    return NextResponse.json(
      { 
        error: 'データ更新の開始に失敗しました',
        detail: errorDetail,
        status: responseStatus,
        apiUrl: apiUrl,
      },
      { status: responseStatus }
    );
  } catch (error) {
    console.error('データ更新API エラー:', error);
    return NextResponse.json(
      { 
        error: 'データ更新の開始に失敗しました',
        detail: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}

