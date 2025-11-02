'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Navigation } from '@/components/shared/Navigation';
import { Settings as SettingsIcon, Bell, Moon, Palette, Trash2, Download, Info, FileText, Shield } from 'lucide-react';

export default function SettingsPage() {
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [displayCount, setDisplayCount] = useState('10');

  return (
    <div className="min-h-screen bg-background pb-16">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-4 md:p-6">
        <div className="flex items-center gap-3">
          <SettingsIcon className="w-7 h-7 md:w-8 md:h-8" />
          <h1 className="text-xl md:text-2xl font-bold">設定</h1>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto space-y-6 md:space-y-8">
        {/* 通知設定 */}
        <Card className="p-4 md:p-6">
          <div className="flex items-center gap-3 mb-6">
            <Bell className="w-6 h-6 text-primary" />
            <h2 className="text-xl md:text-2xl font-semibold">通知設定</h2>
          </div>

          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="space-y-2">
                <Label htmlFor="notifications" className="text-lg">
                  🔔 抽選時刻リマインド
                </Label>
                <p className="text-sm md:text-base text-muted-foreground">
                  ナンバーズの抽選時刻に通知を送ります
                </p>
              </div>
              <Switch
                id="notifications"
                checked={notifications}
                onCheckedChange={setNotifications}
                className="self-start sm:self-center"
              />
            </div>

            <div className="space-y-3">
              <Label className="text-base text-muted-foreground">通知時刻</Label>
              <Select defaultValue="18:00">
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="18:00">18:00</SelectItem>
                  <SelectItem value="19:00">19:00</SelectItem>
                  <SelectItem value="20:00">20:00</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        {/* 表示設定 */}
        <Card className="p-4 md:p-6">
          <div className="flex items-center gap-3 mb-6">
            <Palette className="w-6 h-6 text-primary" />
            <h2 className="text-xl md:text-2xl font-semibold">表示設定</h2>
          </div>

          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="space-y-2">
                <Label htmlFor="darkMode" className="text-lg">
                  🌙 ダークモード
                </Label>
                <p className="text-sm md:text-base text-muted-foreground">
                  アプリ全体をダークモードで表示します
                </p>
              </div>
              <Switch
                id="darkMode"
                checked={darkMode}
                onCheckedChange={setDarkMode}
                className="self-start sm:self-center"
              />
            </div>

            <div className="space-y-3">
              <Label className="text-lg">📊 表示件数</Label>
              <p className="text-sm md:text-base text-muted-foreground">
                一覧画面で表示する最大件数を設定します
              </p>
              <Select value={displayCount} onValueChange={setDisplayCount}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5件</SelectItem>
                  <SelectItem value="10">10件</SelectItem>
                  <SelectItem value="20">20件</SelectItem>
                  <SelectItem value="50">50件</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        {/* データ管理 */}
        <Card className="p-4 md:p-6">
          <div className="flex items-center gap-3 mb-6">
            <Trash2 className="w-6 h-6 text-primary" />
            <h2 className="text-xl md:text-2xl font-semibold">データ管理</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Button variant="outline" className="justify-start text-red-600 border-red-200 hover:bg-red-50 h-12">
              <Trash2 className="w-5 h-5 mr-3" />
              履歴をクリア
            </Button>

            <Button variant="outline" className="justify-start h-12">
              <Download className="w-5 h-5 mr-3" />
              データをエクスポート
            </Button>
          </div>
        </Card>

        {/* アプリ情報 */}
        <Card className="p-4 md:p-6">
          <div className="flex items-center gap-3 mb-6">
            <Info className="w-6 h-6 text-primary" />
            <h2 className="text-xl md:text-2xl font-semibold">アプリ情報</h2>
          </div>

          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
              <span className="text-base">ℹ️ バージョン</span>
              <span className="text-base md:text-lg font-medium">1.0.0</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Button variant="ghost" className="justify-start p-4 h-auto">
                <FileText className="w-5 h-5 mr-3" />
                <span className="text-base">利用規約</span>
              </Button>

              <Button variant="ghost" className="justify-start p-4 h-auto">
                <Shield className="w-5 h-5 mr-3" />
                <span className="text-base">プライバシーポリシー</span>
              </Button>
            </div>
          </div>
        </Card>
      </main>

      {/* ナビゲーション */}
      <Navigation />
    </div>
  );
}

