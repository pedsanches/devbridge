"use client";

import { ChevronDown } from "lucide-react";

interface PeriodSelectorProps {
    days: number;
    onChange: (days: number) => void;
}

export function PeriodSelector({ days, onChange }: PeriodSelectorProps) {
    return (
        <div className="relative">
            <select
                value={days}
                onChange={(e) => onChange(Number(e.target.value))}
                className="h-9 w-[140px] appearance-none rounded-md border border-[var(--border)] bg-[var(--card)] px-3 py-2 text-sm text-[var(--foreground)] shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
                <option value={1}>Últimas 24h</option>
                <option value={7}>Últimos 7 dias</option>
                <option value={30}>Últimos 30 dias</option>
                <option value={90}>Últimos 3 meses</option>
                <option value={365}>Último ano</option>
            </select>
            <div className="pointer-events-none absolute right-2 top-2.5 text-[var(--muted-foreground)]">
                <ChevronDown className="h-4 w-4" />
            </div>
        </div>
    );
}

// Version for the popover content (buttons list)
export function PeriodSelectorContent({ days, onChange }: PeriodSelectorProps) {
    const options = [
        { value: 1, label: "Últimas 24h" },
        { value: 7, label: "Últimos 7 dias" },
        { value: 30, label: "Últimos 30 dias" },
        { value: 90, label: "Últimos 3 meses" },
        { value: 365, label: "Último ano" },
    ];

    return (
        <div className="flex flex-col gap-1 p-1 min-w-[200px]">
            {options.map((opt) => (
                <button
                    key={opt.value}
                    onClick={() => onChange(opt.value)}
                    className={`text-left rounded-md px-3 py-2 text-sm transition-colors ${days === opt.value
                            ? "bg-primary/10 text-primary font-medium"
                            : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800"
                        }`}
                >
                    {opt.label}
                </button>
            ))}
        </div>
    );
}
