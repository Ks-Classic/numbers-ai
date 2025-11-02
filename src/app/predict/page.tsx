'use client';

import { useState } from 'react';
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

  const handleSubmit = () => {
    const roundNum = parseInt(formData.roundNumber);
    
    if (!formData.roundNumber || formData.roundNumber.length !== 4 || isNaN(roundNum) || roundNum < 1000 || roundNum > 9999) {
      alert('回号は4桁の数字で入力してください');
      return;
    }

    setSessionData({
      roundNumber: roundNum,
      numbersType: 'N3',
      patternType: 'A',
    });

    router.push('/predict/rehearsal');
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit();
  };

  return (
    <div className="min-h-screen bg-background">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-3 md:p-4">
        <div className="flex items-center gap-2">
          <Link href="/">
            <ArrowLeft className="w-6 h-6 md:w-7 md:h-7" />
          </Link>
          <h1 className="text-base md:text-lg font-semibold">回号設定</h1>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto">
        {/* タイトル */}
        <div className="mb-4">
          <h2 className="text-lg md:text-xl font-semibold mb-1">第{formData.roundNumber}回</h2>
        </div>

        {/* 説明カード */}
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
          {/* 回号入力 */}
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

          {/* 次へボタン */}
          <div className="pt-4">
            <Button 
              type="submit"
              className="w-full h-12 md:h-14 text-base md:text-lg font-semibold" 
              size="lg"
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

