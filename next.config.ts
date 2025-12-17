import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ビルド最適化
  typescript: {
    // ビルド時の型チェックをスキップ（メモリ不足回避・デプロイ高速化）
    ignoreBuildErrors: true,
  },
  eslint: {
    // ビルド時のESLintチェックをスキップ（メモリ不足回避・デプロイ高速化）
    ignoreDuringBuilds: true,
  },
  // 実験的な機能でビルドを最適化
  experimental: {
    // インクリメンタルビルドを有効化
    optimizePackageImports: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-select'],
  },
  // CORS設定
  async headers() {
    return [
      {
        // 全APIルートに適用
        source: "/api/:path*",
        headers: [
          { key: "Access-Control-Allow-Credentials", value: "true" },
          { key: "Access-Control-Allow-Origin", value: "*" },
          { key: "Access-Control-Allow-Methods", value: "GET,DELETE,PATCH,POST,PUT,OPTIONS" },
          { key: "Access-Control-Allow-Headers", value: "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version" },
        ]
      }
    ]
  }
};

export default nextConfig;
