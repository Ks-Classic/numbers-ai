"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        Sentry.captureException(error);
        console.error("Global error:", error);
    }, [error]);

    return (
        <html lang="ja">
            <body>
                <div
                    style={{
                        minHeight: "100vh",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        padding: "2rem",
                        fontFamily: "system-ui, sans-serif",
                        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
                        color: "#ffffff",
                    }}
                >
                    <div style={{ textAlign: "center", maxWidth: "500px" }}>
                        <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>🚨</div>
                        <h1 style={{ fontSize: "1.5rem", fontWeight: "bold", marginBottom: "1rem" }}>
                            予期しないエラーが発生しました
                        </h1>
                        <p style={{ color: "#94a3b8", marginBottom: "2rem", lineHeight: "1.6" }}>
                            申し訳ありません。問題が発生しました。
                        </p>
                        <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
                            <button
                                onClick={() => reset()}
                                style={{
                                    padding: "0.75rem 1.5rem",
                                    background: "#3b82f6",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "0.5rem",
                                    cursor: "pointer",
                                    fontSize: "1rem",
                                    fontWeight: "500",
                                }}
                            >
                                もう一度試す
                            </button>
                            <button
                                onClick={() => (window.location.href = "/")}
                                style={{
                                    padding: "0.75rem 1.5rem",
                                    background: "transparent",
                                    color: "#94a3b8",
                                    border: "1px solid #475569",
                                    borderRadius: "0.5rem",
                                    cursor: "pointer",
                                    fontSize: "1rem",
                                }}
                            >
                                ホームに戻る
                            </button>
                        </div>
                    </div>
                </div>
            </body>
        </html>
    );
}
