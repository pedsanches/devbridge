"use client";

import React, { useState } from "react";
import { Copy, Check, Share, ThumbsUp, ThumbsDown } from "lucide-react";

interface MessageActionsProps {
    content: string;
    onRate?: (positive: boolean) => void;
}

export function MessageActions({ content, onRate }: MessageActionsProps) {
    const [copied, setCopied] = useState(false);
    const [rated, setRated] = useState<"up" | "down" | null>(null);
    const [shared, setShared] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleShare = async () => {
        // Try native share API first (mobile)
        if (navigator.share) {
            try {
                await navigator.share({
                    title: "DevBridge - Resposta",
                    text: content,
                });
            } catch {
                // User cancelled or not supported
            }
        } else {
            // Fallback: copy formatted content with header
            const formattedContent = `📊 Via DevBridge:\n\n${content}`;
            await navigator.clipboard.writeText(formattedContent);
            setShared(true);
            setTimeout(() => setShared(false), 2000);
        }
    };

    const handleRate = (positive: boolean) => {
        setRated(positive ? "up" : "down");
        onRate?.(positive);
    };

    return (
        <div className="mt-2 flex items-center gap-1 pt-2 border-t border-neutral-200 dark:border-neutral-700">
            {/* Copy Button */}
            <button
                onClick={handleCopy}
                className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-neutral-500 transition-colors hover:bg-neutral-200 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-700 dark:hover:text-neutral-200"
                aria-label="Copiar mensagem"
            >
                {copied ? (
                    <>
                        <Check className="h-3.5 w-3.5 text-green-500" />
                        <span className="text-green-500">Copiado</span>
                    </>
                ) : (
                    <>
                        <Copy className="h-3.5 w-3.5" />
                        <span>Copiar</span>
                    </>
                )}
            </button>

            {/* Share Button */}
            <button
                onClick={handleShare}
                className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-neutral-500 transition-colors hover:bg-neutral-200 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-700 dark:hover:text-neutral-200"
                aria-label="Compartilhar mensagem"
            >
                {shared ? (
                    <>
                        <Check className="h-3.5 w-3.5 text-green-500" />
                        <span className="text-green-500">Link copiado</span>
                    </>
                ) : (
                    <>
                        <Share className="h-3.5 w-3.5" />
                        <span>Compartilhar</span>
                    </>
                )}
            </button>

            {/* Divider */}
            <div className="mx-1 h-4 w-px bg-neutral-200 dark:bg-neutral-700" />

            {/* Rate Buttons */}
            <button
                onClick={() => handleRate(true)}
                className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors ${rated === "up"
                        ? "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400"
                        : "text-neutral-500 hover:bg-neutral-200 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-700 dark:hover:text-neutral-200"
                    }`}
                aria-label="Resposta útil"
                disabled={rated !== null}
            >
                <ThumbsUp className="h-3.5 w-3.5" />
            </button>
            <button
                onClick={() => handleRate(false)}
                className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors ${rated === "down"
                        ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400"
                        : "text-neutral-500 hover:bg-neutral-200 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-700 dark:hover:text-neutral-200"
                    }`}
                aria-label="Resposta não útil"
                disabled={rated !== null}
            >
                <ThumbsDown className="h-3.5 w-3.5" />
            </button>
        </div>
    );
}
