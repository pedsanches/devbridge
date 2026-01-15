"use client";

import React, { memo, useState } from "react";
import { Bot, User, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { SourcesIndicator } from "./SourcesIndicator";
import { MessageActions } from "./MessageActions";

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
    isStreaming?: boolean;
}

const REMARK_PLUGINS = [remarkGfm];

// Code block component with syntax highlighting and copy button
function CodeBlock({ language, children }: { language: string | null; children: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(children);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="group relative my-2">
            {/* Copy button */}
            <button
                onClick={handleCopy}
                className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-md bg-neutral-700 text-neutral-300 opacity-0 transition-opacity hover:bg-neutral-600 hover:text-white group-hover:opacity-100"
                aria-label="Copiar código"
            >
                {copied ? (
                    <Check className="h-3.5 w-3.5 text-green-400" />
                ) : (
                    <Copy className="h-3.5 w-3.5" />
                )}
            </button>

            {/* Language badge */}
            {language && (
                <span className="absolute left-3 top-2 text-[10px] font-medium uppercase text-neutral-500">
                    {language}
                </span>
            )}

            <SyntaxHighlighter
                style={oneDark}
                language={language || "text"}
                PreTag="div"
                className="!mt-0 !rounded-lg !text-sm"
                customStyle={{
                    margin: 0,
                    paddingTop: language ? "2rem" : "1rem",
                }}
            >
                {children}
            </SyntaxHighlighter>
        </div>
    );
}

export const ChatMessage = memo(function ChatMessage({
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
                className={`rounded-2xl px-4 py-3 ${isUser
                    ? "max-w-[80%] bg-primary text-white"
                    : "max-w-[680px] bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white"
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
                                    <a
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary hover:underline"
                                        {...props}
                                    />
                                ),
                                pre: ({ children }) => <>{children}</>,
                                code: ({ className, children, ...props }) => {
                                    const match = /language-(\w+)/.exec(className || "");
                                    const codeString = String(children).replace(/\n$/, "");

                                    // Check if this is a code block (has language) or inline code
                                    if (match && match[1]) {
                                        return <CodeBlock language={match[1]}>{codeString}</CodeBlock>;
                                    }

                                    // Inline code
                                    return (
                                        <code
                                            className="rounded bg-neutral-200 px-1 py-0.5 text-sm dark:bg-neutral-900"
                                            {...props}
                                        >
                                            {children}
                                        </code>
                                    );
                                },
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
