import { NextRequest, NextResponse } from 'next/server';

/**
 * データ更新API
 * 
 * 2つの更新方式をサポート:
 * 1. GitHub Actions方式（デフォルト）: ワークフローをトリガー（自動スクレイピング）
 * 2. シンプル方式: 手動でデータを追加
 * 
 * リクエストボディ（シンプル方式の場合）:
 * {
 *   "useSimple": true,
 *   "roundNumber": 6702,
 *   "drawDate": "2025-11-26",
 *   "n3Rehearsal": "123",
 *   "n4Rehearsal": "4567",
 *   "n3Winning": "456",  // オプション
 *   "n4Winning": "7890"  // オプション
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const useSimple = body.useSimple === true;

    const PAT_TOKEN = process.env.PAT_TOKEN;
    const GITHUB_REPO = process.env.GITHUB_REPO || 'Ks-Classic/numbers-ai';
    const GITHUB_BRANCH = process.env.GITHUB_BRANCH || 'main';

    if (!PAT_TOKEN) {
      return NextResponse.json(
        { error: 'PAT_TOKENが設定されていません' },
        { status: 500 }
      );
    }

    // シンプル方式: API経由で直接CSVを更新
    if (useSimple) {
      const { roundNumber, drawDate, n3Rehearsal, n4Rehearsal, n3Winning, n4Winning } = body;

      if (!roundNumber || !drawDate) {
        return NextResponse.json(
          { error: 'roundNumberとdrawDateは必須です' },
          { status: 400 }
        );
      }

      // 1. 現在のCSVファイルを取得
      const fileUrl = `https://api.github.com/repos/${GITHUB_REPO}/contents/data/past_results.csv?ref=${GITHUB_BRANCH}`;

      const getResponse = await fetch(fileUrl, {
        headers: {
          'Authorization': `Bearer ${PAT_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
        },
      });

      if (!getResponse.ok) {
        throw new Error(`ファイル取得失敗: ${getResponse.status}`);
      }

      const fileData = await getResponse.json();
      const currentContent = Buffer.from(fileData.content, 'base64').toString('utf-8');
      const sha = fileData.sha;

      // 2. 新しい行を追加
      const lines = currentContent.trim().split('\n');

      // 曜日を計算
      const date = new Date(drawDate);
      const dayOfWeek = date.getDay();
      const weekday = dayOfWeek >= 1 && dayOfWeek <= 5 ? dayOfWeek - 1 : null;

      // 新しい行を作成
      const newRow = [
        roundNumber,
        drawDate,
        weekday !== null ? weekday : 'NULL',
        n3Rehearsal || 'NULL',
        n4Rehearsal || 'NULL',
        n3Winning || 'NULL',
        n4Winning || 'NULL',
      ].join(',');

      // 既存の回号をチェック
      const existingRounds = lines.slice(1).map(line => {
        const cols = line.split(',');
        return parseInt(cols[0], 10);
      });

      if (existingRounds.includes(roundNumber)) {
        return NextResponse.json(
          { error: `回号${roundNumber}は既に存在します`, existingData: true },
          { status: 409 }
        );
      }

      // 新しい行を追加（最新が一番上）
      lines.splice(1, 0, newRow);
      const newContent = lines.join('\n') + '\n';

      // 3. GitHubにコミット
      const updateResponse = await fetch(fileUrl, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${PAT_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `chore: 回号${roundNumber}のデータを追加 [skip ci]`,
          content: Buffer.from(newContent, 'utf-8').toString('base64'),
          sha: sha,
          branch: GITHUB_BRANCH,
        }),
      });

      if (!updateResponse.ok) {
        const errorData = await updateResponse.json();
        throw new Error(`ファイル更新失敗: ${JSON.stringify(errorData)}`);
      }

      const result = await updateResponse.json();

      return NextResponse.json({
        success: true,
        message: `回号${roundNumber}のデータを追加しました（シンプル方式）`,
        method: 'simple',
        roundNumber,
        commitUrl: result.commit?.html_url,
      });
    }

    // GitHub Actions方式: ワークフローをトリガー
    const WORKFLOW_FILE = 'auto-update-data.yml';
    const apiUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;

    console.log(`GitHub Actions API呼び出し: ${apiUrl}`);

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${PAT_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ref: GITHUB_BRANCH,
      }),
    });

    const responseStatus = response.status;

    if (responseStatus === 204 || (responseStatus >= 200 && responseStatus < 300)) {
      return NextResponse.json({
        success: true,
        message: 'データ更新を開始しました（GitHub Actions方式）',
        method: 'github_actions',
        detail: 'ワークフローが実行されています。GitHubのActionsタブで進捗を確認できます。',
        workflowUrl: `https://github.com/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}`,
      });
    }

    const errorText = await response.text();
    return NextResponse.json(
      {
        error: 'データ更新の開始に失敗しました',
        detail: errorText,
        status: responseStatus,
      },
      { status: responseStatus }
    );

  } catch (error) {
    console.error('データ更新API エラー:', error);
    return NextResponse.json(
      {
        error: 'データ更新に失敗しました',
        detail: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}
