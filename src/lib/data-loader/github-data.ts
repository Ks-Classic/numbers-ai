/**
 * GitHubからpast_results.csvを取得するユーティリティ
 */

const GITHUB_REPO = process.env.GITHUB_REPO || 'Ks-Classic/numbers-ai';
const GITHUB_BRANCH = process.env.GITHUB_BRANCH || 'main';
const GITHUB_RAW_URL = `https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/data/past_results.csv`;

/**
 * GitHubからpast_results.csvを取得する
 * プライベートリポジトリの場合はGitHub APIを使用
 * 
 * @returns CSVファイルの内容
 * @throws Error 取得に失敗した場合
 */
export async function fetchPastResultsFromGitHub(): Promise<string> {
  const repo = process.env.GITHUB_REPO || GITHUB_REPO;
  const branch = process.env.GITHUB_BRANCH || GITHUB_BRANCH;
  
  // まず、raw.githubusercontent.comを試す（パブリックリポジトリの場合）
  const rawUrl = `https://raw.githubusercontent.com/${repo}/${branch}/data/past_results.csv`;
  const apiUrl = `https://api.github.com/repos/${repo}/contents/data/past_results.csv?ref=${branch}`;
  
  console.log('[fetchPastResultsFromGitHub] GitHub URL (raw):', rawUrl);
  console.log('[fetchPastResultsFromGitHub] GitHub URL (API):', apiUrl);
  console.log('[fetchPastResultsFromGitHub] 環境変数:', {
    GITHUB_REPO: process.env.GITHUB_REPO,
    GITHUB_BRANCH: process.env.GITHUB_BRANCH,
    GITHUB_TOKEN: process.env.GITHUB_TOKEN ? '***設定済み***' : '未設定',
    defaultRepo: repo,
    defaultBranch: branch,
  });
  
  // GITHUB_TOKENが設定されている場合はGitHub APIを使用
  const useApi = !!process.env.GITHUB_TOKEN;
  
  if (useApi) {
    // GitHub APIを使用（プライベートリポジトリ対応）
    try {
      console.log('[fetchPastResultsFromGitHub] GitHub APIを使用して取得中...');
      const response = await fetch(apiUrl, {
        headers: {
          'Authorization': `Bearer ${process.env.GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'numbers-ai',
        },
        cache: 'no-store',
      });

      console.log('[fetchPastResultsFromGitHub] APIレスポンス:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        console.error('[fetchPastResultsFromGitHub] APIエラーレスポンス:', {
          status: response.status,
          statusText: response.statusText,
          errorText: errorText.substring(0, 200),
        });
        throw new Error(`GitHub APIからデータを取得できませんでした: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // base64エンコードされたコンテンツをデコード
      if (!data.content) {
        throw new Error('GitHub APIレスポンスにcontentフィールドがありません');
      }
      
      const csvContent = Buffer.from(data.content, 'base64').toString('utf-8');
      console.log('[fetchPastResultsFromGitHub] ✅ GitHub APIからデータ取得成功:', {
        contentLength: csvContent.length,
        firstLine: csvContent.split('\n')[0],
        sha: data.sha,
      });
      
      return csvContent;
    } catch (error) {
      console.error('[fetchPastResultsFromGitHub] GitHub APIエラー:', error);
      // APIエラーの場合はraw URLを試す（フォールバック）
      console.log('[fetchPastResultsFromGitHub] raw URLを試行中...');
    }
  }
  
  // raw.githubusercontent.comを試す（パブリックリポジトリの場合、またはAPI失敗時のフォールバック）
  try {
    console.log('[fetchPastResultsFromGitHub] raw.githubusercontent.comから取得中...');
    const response = await fetch(rawUrl, {
      cache: 'no-store',
    });

    console.log('[fetchPastResultsFromGitHub] raw URLレスポンス:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
      url: response.url,
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      console.error('[fetchPastResultsFromGitHub] raw URLエラーレスポンス:', {
        status: response.status,
        statusText: response.statusText,
        errorText: errorText.substring(0, 200),
      });
      throw new Error(`GitHubからデータを取得できませんでした: ${response.status} ${response.statusText}`);
    }

    const csvContent = await response.text();
    console.log('[fetchPastResultsFromGitHub] ✅ raw URLからデータ取得成功:', {
      contentLength: csvContent.length,
      firstLine: csvContent.split('\n')[0],
    });
    return csvContent;
  } catch (error) {
    console.error('[fetchPastResultsFromGitHub] ❌ raw URLエラー:', error);
    throw new Error(
      `GitHubからpast_results.csvを取得できませんでした: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * 環境に応じてデータソースを決定する
 * 
 * @returns true: GitHubから取得, false: ローカルファイルから取得
 */
export function shouldUseGitHubData(): boolean {
  // 環境変数で明示的に指定されている場合
  if (process.env.USE_GITHUB_DATA === 'true') {
    return true;
  }
  if (process.env.USE_GITHUB_DATA === 'false') {
    return false;
  }

  // 本番環境（Vercel）ではGitHubから取得
  // ローカル開発環境ではローカルファイルから取得
  return process.env.NODE_ENV === 'production' || process.env.VERCEL === '1';
}

