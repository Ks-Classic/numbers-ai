import { NextRequest, NextResponse } from 'next/server';

/**
 * データ更新API
 * GitHub Actionsのワークフローを手動実行してデータを更新します
 */
export async function POST(request: NextRequest) {
  try {
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
      return NextResponse.json({
        success: true,
        message: 'データ更新を開始しました。数分後に完了します。',
        detail: `GitHub Actionsワークフローをトリガーしました（ステータス: ${responseStatus}）。GitHubリポジトリの「Actions」タブで実行状況を確認できます。`,
        workflowUrl: `https://github.com/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}`,
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

