import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ビルド最適化
  typescript: {
    // ビルド時の型チェックをスキップ（Vercelで型チェックが遅い場合）
    // 注意: 開発時は型チェックを実行することを推奨
    ignoreBuildErrors: false,
  },
  eslint: {
    // ビルド時のESLintチェックをスキップ（VercelでESLintが遅い場合）
    ignoreDuringBuilds: false,
  },
  // 実験的な機能でビルドを最適化
  experimental: {
    // インクリメンタルビルドを有効化
    optimizePackageImports: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-select'],
  },
};

export default nextConfig;
