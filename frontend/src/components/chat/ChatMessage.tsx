"use client";

import React, { memo } from "react";
import { Bot, User } from "lucide-react";
import { Streamdown } from "streamdown";
import type { BundledTheme } from "shiki";
import { SourcesIndicator } from "./SourcesIndicator";
import { MessageActions } from "./MessageActions";
import { logResponseDisplayed, Persona } from "@/services/api";
import { SmartReference, ReportSource } from "@/components/ui/SmartReference";
import { rehypeSmartReferences } from "@/lib/rehype-smart-references";

/**
 * Shiki themes for syntax highlighting in code blocks.
 * First theme is for light mode, second for dark mode.
 */
const SHIKI_THEME = ["github-light", "github-dark"] as [BundledTheme, BundledTheme];

interface Source {
    title: string;
    repository: string;
    type: string;
    author?: string | null;
    url?: string | null;
}

interface ChatMessageProps {
    /** Unique identifier for the message (used for Streamdown memoization) */
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp?: string | undefined;
    sources?: Source[] | undefined;
    activitiesCount?: number | undefined;
    confidenceScore?: number | undefined;
    confidenceExplanation?: string | undefined;
    /** Whether this message is currently being streamed */
    isStreaming?: boolean;
    // Lineage & Feedback
    generationId?: string | undefined;
    conversationId?: string | undefined;
    promptVersionId?: string | undefined;
    traceId?: string | undefined;
    persona?: Persona | undefined;
    feedbackSelection?: import("@/services/api").FeedbackType | null | undefined;
    onFeedbackSelectionChange?: ((selection: import("@/services/api").FeedbackType | null) => void) | undefined;
}

function stabilizeMarkdownForStreaming(markdown: string): string {
    // Stream-friendly heuristics: close common "open" structures temporarily for rendering.
    // This never touches what we persist; it's only used while streaming.

    // Fenced code blocks
    const fenceCount = (markdown.match(/```/g) || []).length;
    if (fenceCount % 2 === 1) {
        return `${markdown}\n\n\`\`\`\n`;
    }

    // Inline code (best-effort): if we have an odd number of backticks, close it.
    // Note: this is a heuristic; it may be fooled by edge-cases, but helps most common cases.
    const inlineTickCount = (markdown.match(/`/g) || []).length;
    if (inlineTickCount % 2 === 1) {
        return `${markdown}\``;
    }

    return markdown;
}

export const ChatMessage = memo(function ChatMessage({
    id,
    role,
    content,
    timestamp,
    sources,
    activitiesCount,
    confidenceScore,
    confidenceExplanation,
    isStreaming = false,
    generationId,
    promptVersionId,
    traceId,
    conversationId,
    persona,
    feedbackSelection,
    onFeedbackSelectionChange,
}: ChatMessageProps) {
    const isUser = role === "user";

    // Streamdown render mode: streaming for active streams, static for completed content
    // No need for useMemo - this is a simple conditional
    const renderMode = isStreaming ? "streaming" : "static";

    // Show actions for completed assistant messages
    const canShowActions = !isUser && !isStreaming && content.length > 0;

    // Log "Displayed" event after 2 seconds
    React.useEffect(() => {
        if (isStreaming || !generationId || isUser) return;

        const timer = setTimeout(() => {
            logResponseDisplayed({
                generation_id: generationId,
                message_id: id,
                trace_id: traceId,
            }).catch(() => { }); // Fire and forget
        }, 2000);

        return () => clearTimeout(timer);
    }, [isStreaming, generationId, id, traceId, isUser]);

    return (
        <div
            className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
            role="listitem"
        >
            {!isUser && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-white">
                    <Bot className="h-4 w-4" />
                </div>
            )}

            <div
                className={`group/message rounded-2xl px-4 py-3 ${isUser
                    ? "max-w-[80%] bg-primary text-white shadow-sm"
                    : "max-w-[680px] bg-[var(--card)] text-neutral-900 shadow-sm ring-1 ring-black/5 dark:bg-neutral-900/40 dark:text-white dark:ring-white/10"
                    }`}
            >
                {isUser ? (
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
                ) : (
                    <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed streamdown-content">
                        <Streamdown
                            key={id}
                            mode={renderMode}
                            isAnimating={isStreaming}
                            parseIncompleteMarkdown={true}
                            {...(isStreaming ? { caret: "block" as const } : {})}
                            shikiTheme={SHIKI_THEME}
                            rehypePlugins={[rehypeSmartReferences]}
                            components={{
                                // Override 'p' to 'div' to prevent nesting errors with block elements in references
                                // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Streamdown component types
                                "p": (props: any) => <div className="mb-4 last:mb-0" {...props} />,
                                // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Streamdown custom component types
                                "smart-ref": (props: any) => {
                                    // Parse ID from props or children
                                    const refId = props.id || props.children;

                                    // Map simple source structure to ReportSource for SmartReference
                                    // The chat defines Source differently than ReportSource, so we mitigate here
                                    const sourceDict = sources?.reduce((acc, src) => {
                                        // The backend 'Source' object doesn't strictly have a 'ref_id' field in the frontend type,
                                        // but it comes from the API. We assume the API provides it or we can infer it.
                                        // For now, let's assume the API sources have 'ref_id' if they are citations.
                                        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Backend API may add fields
                                        const s = src as any;
                                        if (s.ref_id) {
                                            acc[s.ref_id] = {
                                                ref_id: s.ref_id,
                                                external_id: s.external_id,
                                                title: s.title,
                                                repository: s.repository,
                                                type: s.type, // Enum or string
                                                url: s.url,
                                                // Chat sources might have author/status if rich
                                            } as ReportSource;
                                        }
                                        return acc;
                                    }, {} as Record<string, ReportSource>) || {};

                                    const source = sourceDict[refId];

                                    return <SmartReference id={refId} source={source} />;
                                }
                                // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Streamdown components type limitation
                            } as any}
                        >
                            {isStreaming ? stabilizeMarkdownForStreaming(content) : content}
                        </Streamdown>
                    </div>
                )}

                {timestamp && (
                    <span
                        className={`mt-1 block text-xs ${isUser ? "text-white/70" : "text-neutral-500"
                            }`}
                    >
                        {timestamp}
                    </span>
                )}

                {/* Sources indicator for assistant messages */}
                {!isUser && sources && sources.length > 0 && (
                    <SourcesIndicator
                        sources={sources}
                        activitiesCount={activitiesCount || sources.length}
                        confidenceScore={confidenceScore}
                        confidenceExplanation={confidenceExplanation}
                    />
                )}

                {/* Message actions (Copy, Share, Feedback) - always visible for completed assistant messages */}
                {canShowActions && (
                    <MessageActions
                        content={content}
                        messageId={id}
                        conversationId={conversationId}
                        generationId={generationId}
                        promptVersionId={promptVersionId}
                        traceId={traceId}
                        persona={persona}
                        initialFeedbackSelection={feedbackSelection}
                        onFeedbackSelectionChange={onFeedbackSelectionChange}
                    />
                )}
            </div>

            {isUser && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-neutral-200 dark:bg-neutral-700">
                    <User className="h-4 w-4" />
                </div>
            )}
        </div>
    );
});
