"use client";

import React, { useMemo, useState, useRef } from "react";
import { Copy, Check, Share, ThumbsUp, ThumbsDown, AlertCircle } from "lucide-react";
import { submitFeedback, FeedbackType, Persona } from "@/services/api";

interface MessageActionsProps {
    content: string;
    // Feedback props (optional)
    messageId?: string | undefined;
    conversationId?: string | undefined;
    generationId?: string | undefined;
    promptVersionId?: string | undefined;
    traceId?: string | undefined;
    persona?: Persona | undefined;
    initialFeedbackSelection?: FeedbackType | null | undefined;
    onFeedbackSelectionChange?: ((selection: FeedbackType | null) => void) | undefined;
}

export function MessageActions({
    content,
    messageId,
    conversationId,
    generationId,
    promptVersionId,
    traceId,
    persona,
    initialFeedbackSelection,
    onFeedbackSelectionChange,
}: MessageActionsProps) {
    const [copied, setCopied] = useState(false);
    const [shared, setShared] = useState(false);

    // Feedback state
    const selectionKey = useMemo(() => initialFeedbackSelection ?? null, [initialFeedbackSelection]);
    const [feedbackStatus, setFeedbackStatus] = useState<"idle" | "sending" | "success" | "error">("idle");
    const [localFeedbackSelection, setLocalFeedbackSelection] = useState<FeedbackType | null>(selectionKey);

    // Track previous selectionKey to detect prop changes and reset state
    const prevSelectionKeyRef = useRef(selectionKey);
    if (prevSelectionKeyRef.current !== selectionKey) {
        prevSelectionKeyRef.current = selectionKey;
        // This is safe because we're synchronously updating during render
        // React 19 pattern: derive state from props without useEffect
        setLocalFeedbackSelection(selectionKey);
        setFeedbackStatus("idle");
    }

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
            const formattedContent = `Via DevBridge:\n\n${content}`;
            await navigator.clipboard.writeText(formattedContent);
            setShared(true);
            setTimeout(() => setShared(false), 2000);
        }
    };

    const handleFeedback = async (type: FeedbackType) => {
        if (feedbackStatus === "sending") return;

        // Debug: log when feedback is blocked due to missing values
        if (!conversationId || !generationId || !promptVersionId) {
            console.warn("[Feedback] Missing required values:", {
                messageId,
                conversationId: conversationId ?? "MISSING",
                generationId: generationId ?? "MISSING",
                promptVersionId: promptVersionId ?? "MISSING",
            });
            return;
        }

        // Optimistic update
        setLocalFeedbackSelection(type);
        onFeedbackSelectionChange?.(type);
        setFeedbackStatus("sending");

        try {
            await submitFeedback({
                feedback_type: type,
                message_id: messageId!,
                conversation_id: conversationId,
                generation_id: generationId,
                prompt_version_id: promptVersionId,
                trace_id: traceId,
                persona,
            });
            setFeedbackStatus("success");
        } catch (error) {
            console.error("Feedback failed:", error);
            setFeedbackStatus("error");
            // Reset selection after error so user can try again
            setTimeout(() => {
                setFeedbackStatus("idle");
                setLocalFeedbackSelection(null);
                onFeedbackSelectionChange?.(null);
            }, 3000);
        }
    };

    // Determine if feedback buttons should be shown
    const canShowFeedback = generationId && promptVersionId && conversationId && messageId;
    const currentFeedbackSelection = localFeedbackSelection ?? selectionKey;

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
                        <Check className="h-3.5 w-3.5 text-[var(--color-success)]" />
                        <span className="text-[var(--color-success)]">Copiado</span>
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
                        <Check className="h-3.5 w-3.5 text-[var(--color-success)]" />
                        <span className="text-[var(--color-success)]">Link copiado</span>
                    </>
                ) : (
                    <>
                        <Share className="h-3.5 w-3.5" />
                        <span>Compartilhar</span>
                    </>
                )}
            </button>

            {/* Divider before feedback buttons (if feedback is available) */}
            {canShowFeedback && (
                <>
                    <div className="mx-1 h-4 w-px bg-neutral-200 dark:bg-neutral-700" />

                    {/* Thumbs Up Button */}
                    <button
                        onClick={() => handleFeedback("thumbs_up")}
                        disabled={feedbackStatus === "sending"}
                        className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs transition-colors ${currentFeedbackSelection === "thumbs_up"
                            ? "text-[var(--color-success)] bg-[var(--color-success)]/10 dark:bg-[var(--color-success)]/20"
                            : "text-neutral-500 hover:bg-neutral-200 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-700 dark:hover:text-neutral-200"
                            } ${feedbackStatus === "sending" ? "opacity-50 cursor-not-allowed" : ""} ${currentFeedbackSelection === "thumbs_down" ? "opacity-50" : ""}`}
                        title="Resposta útil"
                        aria-label="Resposta útil"
                    >
                        <ThumbsUp className="h-3.5 w-3.5" />
                        <span>Útil</span>
                    </button>

                    {/* Thumbs Down Button */}
                    <button
                        onClick={() => handleFeedback("thumbs_down")}
                        disabled={feedbackStatus === "sending"}
                        className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs transition-colors ${currentFeedbackSelection === "thumbs_down"
                            ? "text-[var(--color-error)] bg-[var(--color-error)]/10 dark:bg-[var(--color-error)]/20"
                            : "text-neutral-500 hover:bg-neutral-200 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-700 dark:hover:text-neutral-200"
                            } ${feedbackStatus === "sending" ? "opacity-50 cursor-not-allowed" : ""} ${currentFeedbackSelection === "thumbs_up" ? "opacity-50" : ""}`}
                        title="Resposta não útil"
                        aria-label="Resposta não útil"
                    >
                        <ThumbsDown className="h-3.5 w-3.5" />
                        <span>Não útil</span>
                    </button>

                    {/* Feedback status indicator */}
                    {feedbackStatus === "success" && (
                        <div className="flex items-center gap-1 text-xs text-[var(--color-success)] animate-in fade-in duration-300 ml-1">
                            <Check className="h-3 w-3" />
                            <span className="sr-only">Feedback enviado</span>
                        </div>
                    )}

                    {feedbackStatus === "error" && (
                        <div className="flex items-center gap-1 text-xs text-[var(--color-error)] animate-in fade-in duration-300 ml-1">
                            <AlertCircle className="h-3 w-3" />
                            <span className="sr-only">Erro ao enviar feedback</span>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
