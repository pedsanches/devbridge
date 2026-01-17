"use client";

import React, { memo, useState } from "react";
import { Bot, User } from "lucide-react";
import { Streamdown } from "streamdown";
import type { BundledTheme } from "shiki";
import { SourcesIndicator } from "./SourcesIndicator";
import { MessageActions } from "./MessageActions";

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
    /** Whether this message is currently being streamed */
    isStreaming?: boolean;
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
    isStreaming = false,
}: ChatMessageProps) {
    const isUser = role === "user";
    const [showActions, setShowActions] = useState(false);

    // Streamdown render mode: streaming for active streams, static for completed content
    // No need for useMemo - this is a simple conditional
    const renderMode = isStreaming ? "streaming" : "static";

    // Don't show actions while streaming or for user messages
    const canShowActions = !isUser && !isStreaming && content.length > 0;

    return (
        <div
            className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
            onMouseEnter={() => canShowActions && setShowActions(true)}
            onMouseLeave={() => setShowActions(false)}
            role="listitem"
        >
            {!isUser && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-white">
                    <Bot className="h-4 w-4" />
                </div>
            )}

            <div
                className={`rounded-2xl px-4 py-3 transition-opacity duration-150 ${isUser
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
                    />
                )}

                {/* Message actions (Copy, Share, Rate) - shown on hover */}
                {showActions && (
                    <MessageActions content={content} />
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
