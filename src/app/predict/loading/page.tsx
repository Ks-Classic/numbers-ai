'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { usePredictionStore } from '@/lib/store';
import type { PredictionItem } from '@/types/prediction';
import { getPatternLabel } from '@/lib/utils/pattern-label';
import { ArrowLeft, Bot, CheckCircle, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import Link from 'next/link';

// APIリクエストのタイムアウト設定（秒）
const API_TIMEOUT_MS = 30000; // 30秒

// エラータイプ
type ApiError = {
  code: string;
  message: string;
  details?: any;
};

export default function LoadingPage() {
  const router = useRouter();
  const {
    currentSession,
    setAxisCandidates,
    setFinalPredictions,
    setSessionData,
    setN3Data,
    setN4Data,
  } = usePredictionStore();

  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const steps = [
    '過去データ分析中...',
    '罫線パターン解析中...',
    'リハーサル文脈分析中...',
    'AI予測実行中...'
  ];

  // API呼び出し処理
  const callPredictAPI = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setProgress(0);
      setCompletedSteps([]);

      // プログレスバーのアニメーション開始
      let stepIndex = 0;
      const stepInterval = setInterval(() => {
        if (stepIndex < steps.length) {
          const step = steps[stepIndex];
          setCurrentStep(step);
          setProgress(((stepIndex + 1) / (steps.length + 1)) * 100);
          stepIndex++;
        }
      }, 1000);

      // APIリクエストの準備
      const requestBody = {
        roundNumber: currentSession.roundNumber,
        ...(currentSession.rehearsalN3 && { n3Rehearsal: currentSession.rehearsalN3 }),
        ...(currentSession.rehearsalN4 && { n4Rehearsal: currentSession.rehearsalN4 }),
        useGitHubData: currentSession.useGitHubData,
      };

      console.log('========================================');
      console.log('[フロントエンド] 予測APIリクエスト開始');
      console.log('リクエストURL:', '/api/predict');
      console.log('リクエストメソッド:', 'POST');
      console.log('リクエストボディ:', JSON.stringify(requestBody, null, 2));
      console.log('========================================');

      // タイムアウト付きAPI呼び出し
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

      try {
        const requestStartTime = performance.now();
        const response = await fetch('/api/predict', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
          signal: controller.signal,
        });
        const requestEndTime = performance.now();

        console.log('========================================');
        console.log('[フロントエンド] 予測APIレスポンス受信');
        console.log('レスポンスステータス:', response.status, response.statusText);
        console.log('レスポンスヘッダー:', Object.fromEntries(response.headers.entries()));
        console.log('レスポンス時間:', Math.round(requestEndTime - requestStartTime), 'ms');
        console.log('========================================');

        clearTimeout(timeoutId);
        clearInterval(stepInterval);

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
            console.error('========================================');
            console.error('[フロントエンド] エラーレスポンスボディ:', JSON.stringify(errorData, null, 2));
            console.error('========================================');
          } catch (parseError) {
            const errorText = await response.text();
            console.error('========================================');
            console.error('[フロントエンド] エラーレスポンステキスト:', errorText);
            console.error('========================================');
            errorData = {
              error: { code: 'UNKNOWN_ERROR', message: '予測処理に失敗しました' }
            };
          }

          throw new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('========================================');
        console.log('[フロントエンド] 予測APIレスポンスパース成功');
        console.log('成功フラグ:', result.success);
        console.log('データキー:', Object.keys(result.data || {}));
        console.log('========================================');

        if (!result.success) {
          throw new Error(result.error?.message || '予測処理に失敗しました');
        }

        // プログレス100%に設定
        setProgress(100);
        setCurrentStep('予測完了');
        setCompletedSteps(steps);

        // APIレスポンスをストアに保存
        const data = result.data;

        console.log('APIレスポンス受信:', {
          hasN3: !!data.n3,
          hasN4: !!data.n4,
          n3AxisCount: data.n3?.box?.axisCandidates?.length || 0,
          n4AxisCount: data.n4?.box?.axisCandidates?.length || 0,
        });

        // N3とN4の両方の予測結果を変換して保存
        let n3AxisCandidates: any[] = [];
        let n3FinalPredictions: any = null;
        let n4AxisCandidates: any[] = [];
        let n4FinalPredictions: any = null;

        if (data.n3) {
          try {
            console.log('N3データ変換開始:', {
              boxAxisCandidatesCount: data.n3.box.axisCandidates?.length || 0,
              straightAxisCandidatesCount: data.n3.straight.axisCandidates?.length || 0,
              boxNumberCandidatesCount: data.n3.box.numberCandidates?.length || 0,
              straightNumberCandidatesCount: data.n3.straight.numberCandidates?.length || 0,
            });

            // N3軸数字候補を変換
            n3AxisCandidates = data.n3.box.axisCandidates.map((item: any) => {
              const axisDigit = item.digit;

              // 各軸数字に対して、その軸数字を含む組み合わせのみをフィルタリング
              const boxCandidates = (data.n3.box.numberCandidates || [])
                .filter((c: any) => c.numbers && c.numbers.includes(axisDigit.toString()))
                .map((c: any) => ({
                  number: c.numbers,
                  score: c.score,
                  probability: c.confidence / 100,
                  reason: `スコア: ${c.score}`,
                  source: c.source as any,
                }));

              const straightCandidates = (data.n3.straight.numberCandidates || [])
                .filter((c: any) => c.numbers && c.numbers.includes(axisDigit.toString()))
                .map((c: any) => ({
                  number: c.numbers,
                  score: c.score,
                  probability: c.confidence / 100,
                  reason: `スコア: ${c.score}`,
                  source: c.source as any,
                }));

              console.log(`軸数字${axisDigit}の候補数:`, {
                box: boxCandidates.length,
                straight: straightCandidates.length,
                boxSample: boxCandidates.slice(0, 3).map((c: PredictionItem) => c.number),
                straightSample: straightCandidates.slice(0, 3).map((c: PredictionItem) => c.number),
              });

              return {
                axis: axisDigit,
                score: item.score,
                confidence: item.confidence,
                chart_score: item.score,
                rehearsal_score: 0,
                reason: `${getPatternLabel(item.source)}から予測`,
                source: item.source as any,
                candidates: {
                  box: boxCandidates,
                  straight: straightCandidates,
                },
              };
            });

            // N3最終予測結果を変換
            n3FinalPredictions = {
              box: (data.n3.box.numberCandidates || []).map((c: any) => ({
                number: c.numbers,
                score: c.score,
                probability: c.confidence / 100,
                reason: `スコア: ${c.score}`,
                source: c.source as any,
              })),
              straight: (data.n3.straight.numberCandidates || []).map((c: any) => ({
                number: c.numbers,
                score: c.score,
                probability: c.confidence / 100,
                reason: `スコア: ${c.score}`,
                source: c.source as any,
              })),
            };
          } catch (e: any) {
            console.error('N3データ変換エラー:', e);
            throw new Error(`N3データの変換に失敗しました: ${e.message}`);
          }
        }

        if (data.n4) {
          try {
            console.log('N4データ変換開始:', {
              boxAxisCandidatesCount: data.n4.box.axisCandidates?.length || 0,
              straightAxisCandidatesCount: data.n4.straight.axisCandidates?.length || 0,
              boxNumberCandidatesCount: data.n4.box.numberCandidates?.length || 0,
              straightNumberCandidatesCount: data.n4.straight.numberCandidates?.length || 0,
            });

            // N4軸数字候補を変換
            n4AxisCandidates = data.n4.box.axisCandidates.map((item: any) => {
              const axisDigit = item.digit;

              // 各軸数字に対して、その軸数字を含む組み合わせのみをフィルタリング
              const boxCandidates = (data.n4.box.numberCandidates || [])
                .filter((c: any) => c.numbers && c.numbers.includes(axisDigit.toString()))
                .map((c: any) => ({
                  number: c.numbers,
                  score: c.score,
                  probability: c.confidence / 100,
                  reason: `スコア: ${c.score}`,
                  source: c.source as any,
                }));

              const straightCandidates = (data.n4.straight.numberCandidates || [])
                .filter((c: any) => c.numbers && c.numbers.includes(axisDigit.toString()))
                .map((c: any) => ({
                  number: c.numbers,
                  score: c.score,
                  probability: c.confidence / 100,
                  reason: `スコア: ${c.score}`,
                  source: c.source as any,
                }));

              console.log(`軸数字${axisDigit}の候補数:`, {
                box: boxCandidates.length,
                straight: straightCandidates.length,
                boxSample: boxCandidates.slice(0, 3).map((c: PredictionItem) => c.number),
                straightSample: straightCandidates.slice(0, 3).map((c: PredictionItem) => c.number),
              });

              return {
                axis: axisDigit,
                score: item.score,
                confidence: item.confidence,
                chart_score: item.score,
                rehearsal_score: 0,
                reason: `${getPatternLabel(item.source)}から予測`,
                source: item.source as any,
                candidates: {
                  box: boxCandidates,
                  straight: straightCandidates,
                },
              };
            });

            // N4最終予測結果を変換
            n4FinalPredictions = {
              box: (data.n4.box.numberCandidates || []).map((c: any) => ({
                number: c.numbers,
                score: c.score,
                probability: c.confidence / 100,
                reason: `スコア: ${c.score}`,
                source: c.source as any,
              })),
              straight: (data.n4.straight.numberCandidates || []).map((c: any) => ({
                number: c.numbers,
                score: c.score,
                probability: c.confidence / 100,
                reason: `スコア: ${c.score}`,
                source: c.source as any,
              })),
            };
          } catch (e: any) {
            console.error('N4データ変換エラー:', e);
            throw new Error(`N4データの変換に失敗しました: ${e.message}`);
          }
        }

        // 現在選択されているnumbersTypeに応じてデータを設定
        const target = currentSession.numbersType.toLowerCase() as 'n3' | 'n4';
        const currentAxisCandidates = target === 'n3' ? n3AxisCandidates : n4AxisCandidates;
        const currentFinalPredictions = target === 'n3' ? n3FinalPredictions : n4FinalPredictions;

        // データが存在するか確認
        if (!currentAxisCandidates || currentAxisCandidates.length === 0) {
          const errorMsg = `予測結果が取得できませんでした（${target}）。データ: ${JSON.stringify({ hasN3: !!data.n3, hasN4: !!data.n4 })}`;
          console.error(errorMsg);
          throw new Error(errorMsg);
        }

        // 最良パターンをストアに保存
        const bestPattern = target === 'n3'
          ? (data.n3?.box.axisCandidates[0]?.source || 'A1')
          : (data.n4?.box.axisCandidates[0]?.source || 'A1');
        setSessionData({ patternType: bestPattern });

        // ストアに保存（N3/N4別に保存）
        console.log('ストアに保存開始:', {
          n3AxisCandidatesCount: n3AxisCandidates.length,
          n4AxisCandidatesCount: n4AxisCandidates.length,
          currentTarget: target,
        });

        // N3とN4のデータを別々に保存
        if (n3AxisCandidates.length > 0) {
          setN3Data(n3AxisCandidates, n3FinalPredictions);
          console.log('N3データをストアに保存完了');
        }

        if (n4AxisCandidates.length > 0) {
          setN4Data(n4AxisCandidates, n4FinalPredictions);
          console.log('N4データをストアに保存完了');
        }

        // 現在選択されているnumbersTypeに応じてメインのデータも設定
        if (target === 'n3' && n3AxisCandidates.length > 0) {
          setAxisCandidates(n3AxisCandidates);
          setFinalPredictions(n3FinalPredictions);
        } else if (target === 'n4' && n4AxisCandidates.length > 0) {
          setAxisCandidates(n4AxisCandidates);
          setFinalPredictions(n4FinalPredictions);
        }

        // ローディング状態を解除
        setIsLoading(false);

        console.log('予測完了、画面遷移を実行します');

        // 少し待ってから次の画面へ
        setTimeout(() => {
          console.log('画面遷移実行:', '/predict/result');
          router.push('/predict/result');
        }, 1000);
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        clearInterval(stepInterval);

        if (fetchError.name === 'AbortError') {
          throw new Error('TIMEOUT_ERROR');
        }
        throw fetchError;
      }
    } catch (err: any) {
      setIsLoading(false);
      setProgress(0);

      // エラーメッセージの処理
      let errorMessage = '予測処理中にエラーが発生しました';
      let errorCode = 'UNKNOWN_ERROR';

      if (err.message === 'TIMEOUT_ERROR') {
        errorMessage = '予測処理がタイムアウトしました。時間をおいて再度お試しください。';
        errorCode = 'TIMEOUT_ERROR';
      } else if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        errorMessage = 'ネットワークエラーが発生しました。インターネット接続を確認してください。';
        errorCode = 'NETWORK_ERROR';
      } else if (err.message.includes('HTTP')) {
        errorMessage = `サーバーエラー: ${err.message}`;
        errorCode = 'SERVER_ERROR';
      } else {
        errorMessage = err.message || errorMessage;
      }

      setError({
        code: errorCode,
        message: errorMessage,
      });
    }
  };

  useEffect(() => {
    // リハーサル数字が入力されているか確認
    if (!currentSession.rehearsalN3 && !currentSession.rehearsalN4) {
      router.push('/predict/rehearsal');
      return;
    }

    // API呼び出しを開始
    callPredictAPI();
  }, []); // 初回マウント時のみ実行

  return (
    <div className="min-h-screen bg-background">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-4">
        <div className="flex items-center gap-4">
          <Link href="/predict/rehearsal">
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <h1 className="text-xl font-bold">ナンバーズAI予測アプリ</h1>
        </div>
      </header>

      <main className="p-4 flex flex-col items-center justify-center min-h-[calc(100vh-80px)]">
        {/* AIキャラクター */}
        <div className="text-center mb-8">
          <div className="relative">
            <Bot className="w-20 h-20 mx-auto text-primary mb-4" />
            <div className="absolute -top-2 -right-2">
              <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            </div>
          </div>
          <h2 className="text-2xl font-bold mb-2">🤖</h2>
        </div>

        {/* タイトル */}
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold mb-4">AIが予測分析を実行中...</h2>

          {/* プログレスバー */}
          <div className="w-full max-w-md mx-auto mb-4">
            <Progress value={progress} className="h-3" />
            <p className="text-sm text-muted-foreground mt-2 text-center">
              {progress}%
            </p>
          </div>

          {/* 推定残り時間 */}
          <p className="text-sm text-muted-foreground">
            推定残り時間: {Math.max(0, Math.ceil((100 - progress) / 25))}秒
          </p>
        </div>

        {/* 実行ステップ */}
        <Card className="w-full max-w-md p-6">
          <div className="space-y-3">
            {steps.map((step, index) => {
              const isCompleted = completedSteps.includes(step);
              const isCurrent = step === currentStep && !isCompleted;

              return (
                <div
                  key={index}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${isCompleted
                    ? 'bg-green-50 text-green-700'
                    : isCurrent
                      ? 'bg-blue-50 text-blue-700'
                      : 'bg-muted/50 text-muted-foreground'
                    }`}
                >
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center ${isCompleted
                    ? 'bg-green-500 text-white'
                    : isCurrent
                      ? 'bg-blue-500 text-white animate-pulse'
                      : 'bg-muted-foreground/20'
                    }`}>
                    {isCompleted ? (
                      <CheckCircle className="w-3 h-3" />
                    ) : isCurrent ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <div className="w-2 h-2 bg-muted-foreground/40 rounded-full" />
                    )}
                  </div>
                  <span className={`text-sm ${isCurrent ? 'font-medium' : ''}`}>
                    {isCompleted ? `✓ ${step}` : step}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>

        {/* エラー表示 */}
        {error && (
          <Alert variant="destructive" className="w-full max-w-md mt-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>エラーが発生しました</AlertTitle>
            <AlertDescription className="mt-2">
              {error.message}
            </AlertDescription>
            <div className="mt-4 flex gap-2">
              <Button
                onClick={() => router.push('/predict/rehearsal')}
                variant="outline"
                size="sm"
              >
                戻る
              </Button>
              <Button
                onClick={() => {
                  setError(null);
                  callPredictAPI();
                }}
                variant="default"
                size="sm"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                再試行
              </Button>
            </div>
          </Alert>
        )}

        {/* 説明テキスト */}
        {!error && (
          <div className="text-center mt-6 text-sm text-muted-foreground max-w-md">
            <p>
              AIが過去の当選データとリハーサル数字を分析し、
              最適な軸数字を予測しています。
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

