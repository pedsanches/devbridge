"use client";

import { Bot, User } from "lucide-react";

interface ChatMessageProps {
    role: "user" | "assistant";
    content: string;
    timestamp?: string;
}

export function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
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
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
                {timestamp && (
                    <span
                        className={`mt-1 block text-xs ${isUser ? "text-white/70" : "text-neutral-500"
                            }`}
                    >
                        {timestamp}
                    </span>
                )}
            </div>

            {isUser && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-neutral-200 dark:bg-neutral-700">
                    <User className="h-4 w-4" />
                </div>
            )}
        </div>
    );
}
