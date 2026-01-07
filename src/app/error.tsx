"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import Link from "next/link";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        Sentry.captureException(error);
        console.error("Page error:", error);
    }, [error]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-8">
            <div className="text-center max-w-md">
                <div className="text-6xl mb-4">⚠️</div>
                <h1 className="text-2xl font-bold mb-2 text-white">
                    エラーが発生しました
                </h1>
                <p className="text-gray-400 mb-6">
                    ページの読み込み中に問題が発生しました。
                </p>
                <div className="flex gap-3 justify-center">
                    <button
                        onClick={() => reset()}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        再試行
                    </button>
                    <Link
                        href="/"
                        className="px-4 py-2 bg-gray-700 text-gray-200 rounded-lg hover:bg-gray-600 transition-colors"
                    >
                        ホームへ
                    </Link>
                </div>
            </div>
        </div>
    );
}
