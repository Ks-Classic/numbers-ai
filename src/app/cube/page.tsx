'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { fetchCubes, gridToTSV, type CubeData } from '@/lib/cube-api';
import { Copy, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function CubePage() {
  const [roundNumber, setRoundNumber] = useState<number | ''>('');
  const [cubes, setCubes] = useState<CubeData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!roundNumber || roundNumber < 1) {
      toast.error('有効な回号を入力してください');
      return;
    }

    setLoading(true);
    setError(null);
    setCubes([]);

    try {
      const data = await fetchCubes(roundNumber);
      setCubes(data.cubes);
      toast.success(`${data.cubes.length}個のCUBEを生成しました`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'CUBE生成に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (cube: CubeData) => {
    try {
      const tsv = gridToTSV(cube.grid, cube.rows, cube.cols);
      await navigator.clipboard.writeText(tsv);
      toast.success('クリップボードにコピーしました。Excelに貼り付けてください。');
    } catch (err) {
      toast.error('コピーに失敗しました');
    }
  };

  const getCubeTitle = (cube: CubeData): string => {
    const keisenLabel = cube.keisen_type === 'current' ? '現罫線' : '新罫線';
    const cubeTypeLabel = cube.cube_type === 'extreme' ? '極CUBE' : '通常CUBE';
    const targetLabel = cube.target.toUpperCase();
    const patternLabel = cube.pattern || '';
    
    return `${keisenLabel} - ${cubeTypeLabel} ${targetLabel} ${patternLabel}`;
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl md:text-3xl font-bold mb-6">CUBE生成</h1>

        {/* 回号入力フォーム */}
        <Card className="p-4 mb-6">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label htmlFor="round-number" className="block text-sm font-medium mb-2">
                回号
              </label>
              <Input
                id="round-number"
                type="number"
                value={roundNumber}
                onChange={(e) => setRoundNumber(e.target.value ? parseInt(e.target.value) : '')}
                placeholder="例: 6850"
                min={1}
                disabled={loading}
                className="w-full"
              />
            </div>
            <Button
              onClick={handleGenerate}
              disabled={loading || !roundNumber}
              className="min-w-[120px]"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  生成中...
                </>
              ) : (
                'CUBE生成'
              )}
            </Button>
          </div>
        </Card>

        {/* エラーメッセージ */}
        {error && (
          <Card className="p-4 mb-6 bg-destructive/10 border-destructive">
            <p className="text-destructive font-semibold mb-2">エラーが発生しました</p>
            <p className="text-destructive whitespace-pre-wrap text-sm">{error}</p>
            <p className="text-muted-foreground text-xs mt-2">
              ブラウザのコンソール（F12）で詳細なログを確認できます。
            </p>
          </Card>
        )}

        {/* CUBE表示 */}
        {cubes.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cubes.map((cube) => (
              <Card key={cube.id} className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-semibold text-sm">{getCubeTitle(cube)}</h3>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleCopy(cube)}
                    className="h-8"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    コピー
                  </Button>
                </div>
                <div className="overflow-x-auto">
                  <table className="border-collapse border border-gray-300 text-xs">
                    <thead>
                      <tr>
                        <th className="border border-gray-300 bg-gray-100 p-1 w-8"></th>
                        {Array.from({ length: cube.cols }, (_, i) => (
                          <th key={i} className="border border-gray-300 bg-gray-100 p-1 w-8">
                            {i + 1}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Array.from({ length: cube.rows }, (_, rowIdx) => (
                        <tr key={rowIdx}>
                          <th className="border border-gray-300 bg-gray-100 p-1">
                            {rowIdx + 1}
                          </th>
                          {Array.from({ length: cube.cols }, (_, colIdx) => {
                            const value = cube.grid[rowIdx + 1]?.[colIdx + 1];
                            return (
                              <td
                                key={colIdx}
                                className="border border-gray-300 p-1 text-center min-w-[32px]"
                              >
                                {value !== null && value !== undefined ? value : ''}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

