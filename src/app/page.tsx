import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Target } from 'lucide-react';
import { Navigation } from '@/components/shared/Navigation';

export default function Home() {
  return (
    <>
      <div className="min-h-screen bg-background flex flex-col pb-16">
        {/* ヘッダー */}
        <header className="bg-primary text-primary-foreground p-3 md:p-4">
          <div className="flex items-center gap-2">
            <Target className="w-6 h-6 md:w-7 md:h-7" />
            <h1 className="text-base md:text-lg font-semibold">ナンバーズAI予測</h1>
          </div>
        </header>

        {/* メインコンテンツ - 中央配置 */}
        <main className="flex-1 flex items-center justify-center p-4 md:p-6">
          <div className="w-full max-w-md">
            <Link href="/predict" className="block w-full">
              <Button className="w-full h-20 md:h-24 text-lg md:text-xl font-semibold" size="lg">
                🎯 新規予測を開始
              </Button>
            </Link>
          </div>
        </main>

        {/* ナビゲーション */}
        <Navigation />
      </div>
    </>
  );
}

