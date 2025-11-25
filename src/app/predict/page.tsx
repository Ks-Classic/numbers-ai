'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePredictionStore } from '@/lib/store';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function PredictPage() {
  const router = useRouter();
  const { currentSession, setSessionData } = usePredictionStore();

  const [formData, setFormData] = useState({
    roundNumber: currentSession.roundNumber ? currentSession.roundNumber.toString() : '6701',
  });

  const [isChecking, setIsChecking] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [dataStatus, setDataStatus] = useState<{
    status: 'checking' | 'found' | 'not_found' | 'updating' | 'update_success' | 'error';
    message?: string;
    githubData?: any;
  }>({ status: 'checking' });

  // データ確認（API: /api/check-latest-data）
  const checkData = async (roundNum: number, forceUpdate: boolean = false) => {
    if (isNaN(roundNum) || roundNum < 1000) return;

    setIsChecking(true);
    setDataStatus({ status: 'checking', message: '最新データを確認中...' });

    try {
      // API: check-latest-data (Pythonスクリプト実行)
      const checkRes = await fetch(`/api/check-latest-data?round=${roundNum}`);
      const checkData = await checkRes.json();

      if (checkData.success && checkData.hasRequiredData && !forceUpdate) {
        // データあり → 更新不要
        setDataStatus({
          status: 'found',
          message: '最新データを取得しました',
          githubData: checkData // 変数名はgithubDataのまま（整合性維持）
        });
      } else {
        // データなし or 強制更新 → 更新実行
        setDataStatus({
          status: 'updating',
          message: 'データを更新中です。しばらくお待ちください...'
        });
        setIsUpdating(true);

        try {
          // データ更新APIを呼び出し (POST: /api/update-data)
          const updateRes = await fetch('/api/update-data', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ roundNumber: roundNum }),
          });

          const updateResult = await updateRes.json();

          if (updateResult.success) {
             // 更新成功後、再度データを整形してstateにセット
             // APIレスポンスには更新後のデータが含まれていると想定
             const updatedData = {
                 targetRoundData: updateResult.data ? {
                    round: updateResult.data.round_number,
                    n3Rehearsal: updateResult.data.n3_rehearsal === 'NULL' ? null : updateResult.data.n3_rehearsal,
                    n4Rehearsal: updateResult.data.n4_rehearsal === 'NULL' ? null : updateResult.data.n4_rehearsal,
                 } : null
             };

            setDataStatus({
              status: 'update_success',
              message: `${updateResult.updated_count}件のデータを更新しました。`,
              githubData: updatedData // 最新データをセット
            });
          } else {
            // エラー
            setDataStatus({
              status: 'error',
              message: updateResult.error || 'データ更新に失敗しました'
            });
          }
        } catch (updateError) {
          console.error('データ更新エラー:', updateError);
          setDataStatus({
            status: 'error',
            message: `データ更新に失敗しました: ${updateError instanceof Error ? updateError.message : 'ネットワークエラー'}`
          });
        } finally {
          setIsUpdating(false);
        }
      }
    } catch (error) {
      console.error('データ確認エラー:', error);
      setDataStatus({
        status: 'error',
        message: `データの確認に失敗しました: ${error instanceof Error ? error.message : 'ネットワークエラー'}`
      });
      setIsUpdating(false);
    } finally {
      setIsChecking(false);
    }
  };

  // 回号が変更されたらチェック（デバウンス）
  useEffect(() => {
    const timer = setTimeout(() => {
      const roundNum = parseInt(formData.roundNumber);
      if (!isNaN(roundNum) && formData.roundNumber.length === 4) {
        checkData(roundNum);
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, [formData.roundNumber]);

  const handleSubmit = () => {
    const roundNum = parseInt(formData.roundNumber);

    if (!formData.roundNumber || formData.roundNumber.length !== 4 || isNaN(roundNum) || roundNum < 1000 || roundNum > 9999) {
      alert('回号は4桁の数字で入力してください');
      return;
    }

    // データが見つかった（または更新成功した）場合に使用
    const useGitHub = dataStatus.status === 'found' || dataStatus.status === 'update_success';

    // リハーサル数字があれば自動入力用に保存
    let rehearsalN3 = '';
    let rehearsalN4 = '';

    if (useGitHub && dataStatus.githubData?.targetRoundData) {
      rehearsalN3 = dataStatus.githubData.targetRoundData.n3Rehearsal || '';
      rehearsalN4 = dataStatus.githubData.targetRoundData.n4Rehearsal || '';
    }

    setSessionData({
      roundNumber: roundNum,
      numbersType: 'N3',
      patternType: 'A1',
      useGitHubData: useGitHub,
      rehearsalN3: rehearsalN3,
      rehearsalN4: rehearsalN4,
    });

    router.push('/predict/rehearsal');
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit();
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="bg-primary text-primary-foreground p-3 md:p-4">
        <div className="flex items-center gap-2">
          <Link href="/">
            <ArrowLeft className="w-6 h-6 md:w-7 md:h-7" />
          </Link>
          <h1 className="text-base md:text-lg font-semibold">回号設定</h1>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto">
        <div className="mb-4 flex justify-between items-end">
          <h2 className="text-lg md:text-xl font-semibold mb-1">第{formData.roundNumber}回</h2>
          <Button
            variant="outline"
            size="sm"
            onClick={() => checkData(parseInt(formData.roundNumber), true)} // 強制更新ボタン
            disabled={isChecking || isUpdating}
          >
            {isChecking ? '確認中...' : isUpdating ? '更新中...' : 'データ確認・更新'}
          </Button>
        </div>

        {dataStatus.status === 'checking' && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-blue-800 text-sm">
            🔄 {dataStatus.message}
          </div>
        )}

        {dataStatus.status === 'updating' && (
          <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-md text-purple-800 text-sm">
            ⏳ {dataStatus.message}
          </div>
        )}

        {dataStatus.status === 'update_success' && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-800 text-sm">
            ✅ {dataStatus.message}
            {dataStatus.githubData?.targetRoundData?.n3Rehearsal && (
              <div className="mt-1 text-xs text-green-700">
                ※リハーサル数字も自動入力されます
              </div>
            )}
          </div>
        )}

        {dataStatus.status === 'found' && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-800 text-sm">
            ✅ 最新データが見つかりました。このまま進むと自動的に適用されます。
            {dataStatus.githubData?.targetRoundData?.n3Rehearsal && (
              <div className="mt-1 text-xs text-green-700">
                ※リハーサル数字も自動入力されます
              </div>
            )}
          </div>
        )}

        {dataStatus.status === 'not_found' && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-800 text-sm">
            ⚠️ 必要なデータが見つかりませんでした。手動で入力してください。
          </div>
        )}

        {dataStatus.status === 'error' && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
            ❌ {dataStatus.message}
          </div>
        )}

        <Card className="p-4 md:p-5 mb-5 bg-blue-50 border-blue-200">
          <div className="flex items-start gap-3">
            <div className="text-xl md:text-2xl">ℹ️</div>
            <div>
              <h3 className="font-semibold text-blue-900 mb-2 text-base md:text-lg">AI分析</h3>
              <p className="text-sm md:text-base text-blue-700">
                ナンバーズ3と4、それぞれに存在する予測表の異なるシナリオを同時に、かつ多角的に分析します。
              </p>
              <p className="text-sm md:text-base text-blue-700 mt-2">
                AIが全ての分析を終えた後、最も有望な候補を統合し、ランキング表示します。
              </p>
            </div>
          </div>
        </Card>

        <form onSubmit={handleFormSubmit} className="space-y-5">
          <Card className="p-4 md:p-5">
            <div className="space-y-3">
              <Label htmlFor="round" className="text-base md:text-lg font-semibold">
                回号
              </Label>
              <Input
                id="round"
                type="tel"
                value={formData.roundNumber}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '' || (/^\d+$/.test(value) && value.length <= 4)) {
                    setFormData(prev => ({
                      ...prev,
                      roundNumber: value
                    }));
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                className="text-lg md:text-xl h-12 md:h-14 font-semibold"
                placeholder="6701"
                maxLength={4}
                inputMode="numeric"
                pattern="[0-9]*"
              />
            </div>
          </Card>

          <div className="pt-4">
            <Button
              type="submit"
              className="w-full h-12 md:h-14 text-base md:text-lg font-semibold"
              size="lg"
              disabled={isChecking || isUpdating}
            >
              次へ（リハーサル数字入力）
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </form>
      </main>
    </div>
  );
}
