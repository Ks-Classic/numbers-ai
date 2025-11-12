import { NextRequest, NextResponse } from 'next/server';

/**
 * GitHub Actionsワークフロー実行状況を確認するAPI
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const workflowId = searchParams.get('workflow_id');
    
    if (!workflowId) {
      return NextResponse.json(
        { error: 'workflow_idパラメータが必要です' },
        { status: 400 }
      );
    }

    const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
    const GITHUB_REPO = process.env.GITHUB_REPO || 'Ks-Classic/numbers-ai';

    if (!GITHUB_TOKEN) {
      return NextResponse.json(
        { error: 'GitHubトークンが設定されていません' },
        { status: 500 }
      );
    }

    // ワークフローIDからワークフローファイル名を取得
    // workflow_idは数値IDまたはファイル名
    const apiUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/runs?workflow_id=${workflowId}&per_page=1`;
    
    const response = await fetch(apiUrl, {
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { 
          error: 'ワークフロー実行状況の取得に失敗しました',
          detail: errorText
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    const runs = data.workflow_runs || [];
    
    if (runs.length === 0) {
      return NextResponse.json({
        success: true,
        status: 'not_found',
        message: 'ワークフロー実行が見つかりませんでした',
      });
    }

    const latestRun = runs[0];
    
    return NextResponse.json({
      success: true,
      status: latestRun.status, // queued, in_progress, completed
      conclusion: latestRun.conclusion, // success, failure, cancelled, null
      runId: latestRun.id,
      runNumber: latestRun.run_number,
      createdAt: latestRun.created_at,
      updatedAt: latestRun.updated_at,
      htmlUrl: latestRun.html_url,
      workflowUrl: latestRun.workflow_url,
    });
  } catch (error) {
    console.error('ワークフロー実行状況取得エラー:', error);
    return NextResponse.json(
      { 
        error: 'ワークフロー実行状況の取得に失敗しました',
        detail: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}

