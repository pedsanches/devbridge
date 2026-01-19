"use client";

import { useEffect, useMemo, useState } from "react";
import { ThumbsUp, ThumbsDown, Check, AlertCircle } from "lucide-react";
import { submitFeedback, FeedbackType, Persona } from "@/services/api";


interface FeedbackButtonsProps {
    messageId: string;
    conversationId?: string | undefined; // Optional because optimistic messages might not have it yet
    generationId: string;
    promptVersionId: string;
    traceId?: string | undefined;
    persona?: Persona | undefined;
    initialSelection?: FeedbackType | null | undefined;
    onSelectionChange?: ((selection: FeedbackType | null) => void) | undefined;
}

export function FeedbackButtons({
    messageId,
    conversationId,
    generationId,
    promptVersionId,
    traceId,
    persona,
    initialSelection,
    onSelectionChange,
}: FeedbackButtonsProps) {
    const selectionKey = useMemo(() => initialSelection ?? null, [initialSelection]);

    const [status, setStatus] = useState<"idle" | "sending" | "success" | "error">("idle");
    const [localSelection, setLocalSelection] = useState<FeedbackType | null>(selectionKey);

    // Sync local state when initialSelection prop changes
    useEffect(() => {
        setLocalSelection(selectionKey);
        setStatus("idle");
    }, [selectionKey]);

    const handleFeedback = async (type: FeedbackType, reason?: string) => {
        if (status === "sending" || !conversationId) return;

        // Optimistic update
        setLocalSelection(type);
        onSelectionChange?.(type);
        setStatus("sending");

        try {
            await submitFeedback({
                feedback_type: type,
                message_id: messageId,
                conversation_id: conversationId,
                generation_id: generationId,
                prompt_version_id: promptVersionId,
                trace_id: traceId,
                persona,
                metadata: reason ? { reason } : undefined,
            });
            setStatus("success");
        } catch (error) {
            console.error("Feedback failed:", error);
            setStatus("error");
            setTimeout(() => {
                setStatus("idle");
                // Don't reset selection largely to keep UI stable,
                // but allow retry.
            }, 3000);
        }
    };

    return (
        <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => handleFeedback("thumbs_up")}
                        disabled={status === "sending"}
                        className={`p-1.5 rounded-md transition-colors ${(localSelection ?? selectionKey) === "thumbs_up"
                            ? "text-[var(--color-success)] bg-[var(--color-success)]/10 dark:bg-[var(--color-success)]/20"
                            : "text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                            } ${(localSelection ?? selectionKey) === "thumbs_down" ? "opacity-50" : ""}`}
                        title="Resposta útil"
                        aria-label="Resposta útil"
                    >
                        <ThumbsUp className="h-3.5 w-3.5" />
                    </button>
                    <button
                        onClick={() => handleFeedback("thumbs_down")}
                        disabled={status === "sending"}
                        className={`p-1.5 rounded-md transition-colors ${(localSelection ?? selectionKey) === "thumbs_down"
                            ? "text-[var(--color-error)] bg-[var(--color-error)]/10 dark:bg-[var(--color-error)]/20"
                            : "text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                            } ${(localSelection ?? selectionKey) === "thumbs_up" ? "opacity-50" : ""}`}
                        title="Resposta não útil"
                        aria-label="Resposta não útil"
                    >
                        <ThumbsDown className="h-3.5 w-3.5" />
                    </button>
                </div>

                {status === "success" && (
                    <div className="flex items-center gap-1 text-xs text-[var(--color-success)] animate-in fade-in duration-300">
                        <Check className="h-3 w-3" />
                        <span className="sr-only">Feedback enviado</span>
                    </div>
                )}

                {status === "error" && (
                    <div className="flex items-center gap-1 text-xs text-[var(--color-error)] animate-in fade-in duration-300">
                        <AlertCircle className="h-3 w-3" />
                    </div>
                )}
            </div>

            {/* Negative Feedback Reasons */}
            {(localSelection ?? selectionKey) === "thumbs_down" && (
                <div className="flex flex-wrap gap-1 animate-in slide-in-from-top-1 fade-in duration-200">
                    {["Alucinação", "Faltou Contexto", "Tom Inadequado"].map((reason) => (
                        <button
                            key={reason}
                            onClick={() => handleFeedback("thumbs_down", reason)}
                            className="px-2 py-0.5 text-[10px] rounded-full border border-[var(--border)] text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 dark:hover:bg-neutral-800 dark:hover:text-neutral-200 transition-colors bg-[var(--card)]"
                        >
                            {reason}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
