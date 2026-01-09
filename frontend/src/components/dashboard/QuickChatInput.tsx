"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MessageSquare, ArrowRight, Sparkles } from "lucide-react";

const QUICK_PROMPTS = [
    "O que fizemos essa semana?",
    "Quais foram os principais riscos?",
    "Resumo para o PM",
    "Dívida técnica acumulada",
];

export function QuickChatInput() {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const [isFocused, setIsFocused] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        // Navigate to chat with the query as a parameter
        const encodedQuery = encodeURIComponent(query.trim());
        router.push(`/chat?q=${encodedQuery}`);
    };

    const handleQuickPrompt = (prompt: string) => {
        const encodedQuery = encodeURIComponent(prompt);
        router.push(`/chat?q=${encodedQuery}`);
    };

    return (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 transition-all hover:shadow-md">
            <form onSubmit={handleSubmit} className="space-y-3">
                {/* Input */}
                <div
                    className={`
                        flex items-center gap-3 rounded-lg border px-4 py-3 transition-all
                        ${isFocused
                            ? "border-primary bg-white shadow-sm dark:bg-[var(--background)]"
                            : "border-[var(--border)] bg-[var(--muted)]"
                        }
                    `}
                >
                    <MessageSquare className="h-5 w-5 flex-shrink-0 text-primary" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        placeholder="Pergunte algo sobre seus projetos..."
                        className="flex-1 bg-transparent text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none"
                    />
                    <button
                        type="submit"
                        disabled={!query.trim()}
                        className={`
                            flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-all
                            ${query.trim()
                                ? "bg-primary text-white hover:bg-[var(--color-primary-hover)]"
                                : "bg-[var(--muted)] text-[var(--muted-foreground)] cursor-not-allowed"
                            }
                        `}
                    >
                        <span className="hidden sm:inline">Enviar</span>
                        <ArrowRight className="h-4 w-4" />
                    </button>
                </div>

                {/* Quick Prompts */}
                <div className="flex flex-wrap items-center gap-2">
                    <Sparkles className="h-3.5 w-3.5 text-[var(--muted-foreground)]" />
                    {QUICK_PROMPTS.map((prompt) => (
                        <button
                            key={prompt}
                            type="button"
                            onClick={() => handleQuickPrompt(prompt)}
                            className="rounded-full border border-[var(--border)] bg-[var(--background)] px-3 py-1 text-xs text-[var(--muted-foreground)] transition-colors hover:border-primary hover:text-primary"
                        >
                            {prompt}
                        </button>
                    ))}
                </div>
            </form>
        </div>
    );
}
