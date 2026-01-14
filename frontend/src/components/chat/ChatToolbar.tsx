"use client";

import React from "react";
import { Briefcase, Code, Layers, Calendar, Folder, ChevronDown, Users } from "lucide-react";
import { Persona, Team } from "@/services/api";

interface ToolbarChipProps {
    icon: React.ReactNode;
    label: string;
    count?: number;
    onClick?: () => void;
    active?: boolean;
}

function ToolbarChip({ icon, label, count, onClick, active }: ToolbarChipProps) {
    return (
        <button
            onClick={onClick}
            className={`
                inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium
                transition-all border
                ${active
                    ? "bg-primary/10 text-primary border-primary/30"
                    : "bg-[var(--muted)] text-[var(--muted-foreground)] border-transparent hover:border-[var(--border)] hover:bg-[var(--card)]"
                }
            `}
        >
            {icon}
            <span className="truncate max-w-[100px]">{label}</span>
            {count && count > 1 && (
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/20 text-[10px] text-primary">
                    +{count - 1}
                </span>
            )}
            <ChevronDown className="h-3 w-3 opacity-50" />
        </button>
    );
}

const PERSONA_CONFIG: Record<Persona, { label: string; icon: React.ElementType }> = {
    executive: { label: "Executivo", icon: Briefcase },
    product: { label: "Produto", icon: Layers },
    technical: { label: "Técnico", icon: Code },
};

const PERIOD_OPTIONS = [
    { value: 1, label: "24h" },
    { value: 7, label: "7 dias" },
    { value: 30, label: "30 dias" },
    { value: 90, label: "3 meses" },
    { value: 365, label: "1 ano" },
];

interface ChatToolbarProps {
    persona: Persona;
    selectedRepos: string[];
    days: number;
    selectedTeamId: string | null;
    teamName?: string | undefined;
    onOpenPersonaSelector: () => void;
    onOpenRepoSelector: () => void;
    onOpenTeamSelector: () => void;
    onOpenPeriodSelector: () => void;
}

export function ChatToolbar({
    persona,
    selectedRepos,
    days,
    selectedTeamId,
    teamName,
    onOpenPersonaSelector,
    onOpenRepoSelector,
    onOpenTeamSelector,
    onOpenPeriodSelector,
}: ChatToolbarProps) {
    const PersonaIcon = PERSONA_CONFIG[persona].icon;
    const periodLabel = PERIOD_OPTIONS.find(p => p.value === days)?.label || `${days} dias`;

    return (
        <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border)] bg-[var(--card)]/50 backdrop-blur-sm overflow-x-auto">
            {/* Persona Chip */}
            <ToolbarChip
                icon={<PersonaIcon className="h-3.5 w-3.5" />}
                label={PERSONA_CONFIG[persona].label}
                onClick={onOpenPersonaSelector}
                active
            />

            {/* Divider */}
            <div className="h-4 w-px bg-[var(--border)] shrink-0" />

            {/* Team Chip */}
            <ToolbarChip
                icon={<Users className="h-3.5 w-3.5" />}
                label={selectedTeamId ? (teamName || "Time") : "Todos os times"}
                onClick={onOpenTeamSelector}
                active={!!selectedTeamId}
            />

            {/* Repository Chip */}
            <ToolbarChip
                icon={<Folder className="h-3.5 w-3.5" />}
                label={selectedRepos.length > 0 ? (selectedRepos[0] || "") : "Todos os projetos"}
                count={selectedRepos.length}
                onClick={onOpenRepoSelector}
                active={selectedRepos.length > 0}
            />

            {/* Period Chip */}
            <ToolbarChip
                icon={<Calendar className="h-3.5 w-3.5" />}
                label={periodLabel}
                onClick={onOpenPeriodSelector}
            />

            {/* RAG Indicator - pushed to the right */}
            <div className="ml-auto flex items-center gap-1.5 text-xs text-[var(--muted-foreground)] shrink-0">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                <span>RAG ativo</span>
            </div>
        </div>
    );
}
