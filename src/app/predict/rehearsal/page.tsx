'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePredictionStore } from '@/lib/store';
import { ArrowLeft, Sparkles } from 'lucide-react';
import Link from 'next/link';

export default function RehearsalPage() {
  const router = useRouter();
  const { currentSession, setSessionData } = usePredictionStore();

  const [formData, setFormData] = useState({
    rehearsalN3: currentSession.rehearsalN3 || '',
    rehearsalN4: currentSession.rehearsalN4 || '',
  });

  // フォーカス移動用のref
  const n4InputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const n3InputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // ストアにデータを設定
    setSessionData({
      rehearsalN3: formData.rehearsalN3,
      rehearsalN4: formData.rehearsalN4,
    });

    // AI分析中画面へ遷移
    router.push('/predict/loading');
  };

  const handleInputChange = (field: 'rehearsalN3' | 'rehearsalN4', index: number, value: string) => {
    // 数字のみ許可
    const numericValue = value.replace(/[^0-9]/g, '');
    
    if (numericValue.length > 1) {
      // 複数文字入力の場合、最初の1文字のみ使用
      const firstChar = numericValue[0];
      const newValue = formData[field].split('');
      newValue[index] = firstChar;
      const updatedValue = newValue.join('').slice(0, field === 'rehearsalN3' ? 3 : 4);
      
      setFormData(prev => ({
        ...prev,
        [field]: updatedValue
      }));

      // 次の入力欄にフォーカス移動
      const maxIndex = field === 'rehearsalN3' ? 2 : 3;
      if (index < maxIndex) {
        const refs = field === 'rehearsalN3' ? n3InputRefs : n4InputRefs;
        setTimeout(() => {
          refs.current[index + 1]?.focus();
        }, 0);
      }
    } else {
      // 1文字入力の場合
      const newValue = formData[field].split('');
      newValue[index] = numericValue;
      const updatedValue = newValue.join('').slice(0, field === 'rehearsalN3' ? 3 : 4);
      
      setFormData(prev => ({
        ...prev,
        [field]: updatedValue
      }));

      // 数字が入力されたら次の入力欄にフォーカス移動
      if (numericValue && index < (field === 'rehearsalN3' ? 2 : 3)) {
        const refs = field === 'rehearsalN3' ? n3InputRefs : n4InputRefs;
        setTimeout(() => {
          refs.current[index + 1]?.focus();
        }, 0);
      }
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-3 md:p-4">
        <div className="flex items-center gap-2">
          <Link href="/predict">
            <ArrowLeft className="w-6 h-6 md:w-7 md:h-7" />
          </Link>
          <h1 className="text-base md:text-lg font-semibold">リハーサル数字</h1>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto">
        {/* タイトル */}
        <div className="mb-4">
          <h2 className="text-lg md:text-xl font-semibold mb-1">第{currentSession.roundNumber}回</h2>
        </div>

        {/* 説明カード */}
        <Card className="p-4 md:p-5 mb-5 bg-blue-50 border-blue-200">
          <div className="flex items-start gap-3">
            <div className="text-xl md:text-2xl">📢</div>
            <div>
              <h3 className="font-semibold text-blue-900 mb-2 text-base md:text-lg">重要な予測キー</h3>
              <p className="text-sm md:text-base text-blue-700">
                当選発表前の試験抽出数字です。この数字が予測の重要な手がかりとなります。
              </p>
            </div>
          </div>
        </Card>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* ナンバーズ4入力 */}
          <Card className="p-4 md:p-5">
            <div className="space-y-3">
              <Label className="text-base md:text-lg font-semibold">ナンバーズ4:</Label>
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <div className="flex gap-3">
                  {[0, 1, 2, 3].map((index) => (
                    <Input
                      key={index}
                      ref={(el) => {
                        n4InputRefs.current[index] = el;
                      }}
                      type="tel"
                      maxLength={1}
                      value={formData.rehearsalN4[index] || ''}
                      onChange={(e) => handleInputChange('rehearsalN4', index, e.target.value)}
                      onKeyDown={(e) => {
                        // バックスペースで前の入力欄に移動
                        if (e.key === 'Backspace' && !formData.rehearsalN4[index] && index > 0) {
                          e.preventDefault();
                          n4InputRefs.current[index - 1]?.focus();
                        }
                      }}
                      className="w-14 h-14 md:w-16 md:h-16 text-center text-xl md:text-2xl font-mono font-bold"
                      placeholder="0"
                      inputMode="numeric"
                      pattern="[0-9]*"
                    />
                  ))}
                </div>
                <div className="text-sm md:text-base text-muted-foreground font-medium">
                  千　百　十　一
                </div>
              </div>
            </div>
          </Card>

          {/* ナンバーズ3入力 */}
          <Card className="p-4 md:p-5">
            <div className="space-y-3">
              <Label className="text-base md:text-lg font-semibold">ナンバーズ3:</Label>
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <div className="flex gap-3">
                  {[0, 1, 2].map((index) => (
                    <Input
                      key={index}
                      ref={(el) => {
                        n3InputRefs.current[index] = el;
                      }}
                      type="tel"
                      maxLength={1}
                      value={formData.rehearsalN3[index] || ''}
                      onChange={(e) => handleInputChange('rehearsalN3', index, e.target.value)}
                      onKeyDown={(e) => {
                        // バックスペースで前の入力欄に移動
                        if (e.key === 'Backspace' && !formData.rehearsalN3[index] && index > 0) {
                          e.preventDefault();
                          n3InputRefs.current[index - 1]?.focus();
                        }
                      }}
                      className="w-14 h-14 md:w-16 md:h-16 text-center text-xl md:text-2xl font-mono font-bold"
                      placeholder="0"
                      inputMode="numeric"
                      pattern="[0-9]*"
                    />
                  ))}
                </div>
                <div className="text-sm md:text-base text-muted-foreground font-medium">
                  百　十　一
                </div>
              </div>
            </div>
          </Card>

          {/* AI予測実行ボタン */}
          <div className="pt-4">
            <Button
              type="submit"
              className="w-full h-12 md:h-14 text-base md:text-lg font-semibold"
              size="lg"
              disabled={!formData.rehearsalN3 || !formData.rehearsalN4}
            >
              <Sparkles className="w-5 h-5 mr-2" />
              🔮 AI予測を実行
            </Button>
          </div>
        </form>
      </main>
    </div>
  );
}

