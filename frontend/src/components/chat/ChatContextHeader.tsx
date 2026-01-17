import React from "react";
import { Users, Calendar } from "lucide-react";

interface ChatContextHeaderProps {
    teamName?: string | undefined;
    days: number;
}

export function ChatContextHeader({ teamName, days }: ChatContextHeaderProps) {
    if (!teamName) return null;

    return (
        <div className="sticky top-0 z-10 flex w-full items-center justify-center border-b border-[var(--border)] bg-[var(--background)]/95 px-4 py-2 backdrop-blur supports-[backdrop-filter]:bg-[var(--background)]/60">
            <div className="flex items-center gap-3 rounded-full border border-[var(--border)] bg-[var(--card)]/50 px-3 py-1.5 text-xs text-[var(--muted-foreground)] shadow-sm">
                <div className="flex items-center gap-1.5">
                    <Users className="h-3.5 w-3.5 opacity-70" />
                    <span>
                        Contexto: <span className="font-medium text-[var(--foreground)]">{teamName}</span>
                    </span>
                </div>
                <div className="h-3 w-px bg-[var(--border)]" />
                <div className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 opacity-70" />
                    <span>
                        Últimos <span className="font-medium text-[var(--foreground)]">{days} dias</span>
                    </span>
                </div>
            </div>
        </div>
    );
}
