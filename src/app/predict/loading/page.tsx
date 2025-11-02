'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { usePredictionStore } from '@/lib/store';
import { sampleAxisCandidates } from '@/lib/sample-data';
import { ArrowLeft, Bot, CheckCircle, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function LoadingPage() {
  const router = useRouter();
  const { setAxisCandidates } = usePredictionStore();

  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);

  const steps = [
    '過去データ分析完了',
    '罫線パターン解析完了',
    'リハーサル文脈分析完了',
    '軸数字を予測中...'
  ];

  useEffect(() => {
    let currentStepIndex = 0;

    const interval = setInterval(() => {
      if (currentStepIndex < steps.length) {
        const step = steps[currentStepIndex];

        if (currentStepIndex < steps.length - 1) {
          setCompletedSteps(prev => [...prev, step]);
        }

        setCurrentStep(step);
        setProgress((currentStepIndex + 1) * 25);
        currentStepIndex++;
      } else {
        clearInterval(interval);

        // サンプルデータをストアに設定
        setAxisCandidates(sampleAxisCandidates);

        // 少し待ってから次の画面へ
        setTimeout(() => {
          router.push('/predict/axis');
        }, 1000);
      }
    }, 800);

    return () => clearInterval(interval);
  }, [router, setAxisCandidates]);

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
                  className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                    isCompleted
                      ? 'bg-green-50 text-green-700'
                      : isCurrent
                      ? 'bg-blue-50 text-blue-700'
                      : 'bg-muted/50 text-muted-foreground'
                  }`}
                >
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                    isCompleted
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

        {/* 説明テキスト */}
        <div className="text-center mt-6 text-sm text-muted-foreground max-w-md">
          <p>
            AIが過去の当選データとリハーサル数字を分析し、
            最適な軸数字を予測しています。
          </p>
        </div>
      </main>
    </div>
  );
}

