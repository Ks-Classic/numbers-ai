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
    const WORKFLOW_FILE = '.github/workflows/auto-update-data.yml';

    if (!GITHUB_TOKEN) {
      return NextResponse.json(
        { error: 'GitHubトークンが設定されていません。環境変数GITHUB_TOKENを設定してください。' },
        { status: 500 }
      );
    }

    // GitHub Actions APIでワークフローを手動実行
    // workflow_dispatchイベントをトリガー
    const response = await fetch(
      `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ref: 'main', // mainブランチで実行
        }),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`GitHub Actions API エラー: ${response.status} - ${errorText}`);
      return NextResponse.json(
        { 
          error: 'データ更新の開始に失敗しました',
          detail: errorText 
        },
        { status: response.status }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'データ更新を開始しました。数分後に完了します。',
    });
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

