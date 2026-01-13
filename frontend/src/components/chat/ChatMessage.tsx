import React, { memo } from "react";
import { Bot, User } from "lucide-react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SourcesIndicator } from "./SourcesIndicator";

interface Source {
    title: string;
    repository: string;
    type: string;
    author?: string | null;
    url?: string | null;
}

interface ChatMessageProps {
    role: "user" | "assistant";
    content: string;
    timestamp?: string | undefined;
    sources?: Source[] | undefined;
    activitiesCount?: number | undefined;
    confidenceScore?: number | undefined;
}

const REMARK_PLUGINS = [remarkGfm];

export const ChatMessage = memo(function ChatMessage({ role, content, timestamp, sources, activitiesCount, confidenceScore }: ChatMessageProps) {
    const isUser = role === "user";

    return (
        <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
            {!isUser && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-white">
                    <Bot className="h-4 w-4" />
                </div>
            )}

            <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${isUser
                    ? "bg-primary text-white"
                    : "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white"
                    }`}
            >
                {isUser ? (
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
                ) : (
                    <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed">
                        <ReactMarkdown
                            remarkPlugins={REMARK_PLUGINS}
                            components={{
                                a: ({ ...props }) => (
                                    <a target="_blank" rel="noopener noreferrer" className="text-primary hover:underline" {...props} />
                                ),
                                pre: ({ ...props }) => (
                                    <pre className="overflow-x-auto rounded bg-neutral-200 p-2 dark:bg-neutral-900" {...props} />
                                ),
                                code: ({ ...props }) => (
                                    <code className="rounded bg-neutral-200 px-1 py-0.5 dark:bg-neutral-900" {...props} />
                                )
                            }}
                        >
                            {content}
                        </ReactMarkdown>
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
                    <SourcesIndicator sources={sources} activitiesCount={activitiesCount || sources.length} confidenceScore={confidenceScore} />
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
