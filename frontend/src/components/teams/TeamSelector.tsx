"use client";

import { useState, useEffect, useCallback } from "react";
import { Users, ChevronDown, Check, Settings } from "lucide-react";
import { getTeams, Team } from "@/services/api";

interface TeamSelectorProps {
    selectedTeamId: string | null;
    onTeamChange: (teamId: string | null, team: Team | null) => void;
    disabled?: boolean;
    allowAll?: boolean; // If true, shows "Todos os repositórios" option
    className?: string;
}

export function TeamSelector({
    selectedTeamId,
    onTeamChange,
    disabled = false,
    allowAll = false,
    className = "",
}: TeamSelectorProps) {
    const [teams, setTeams] = useState<Team[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isOpen, setIsOpen] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchTeams = useCallback(async () => {
        try {
            setIsLoading(true);
            const response = await getTeams();
            setTeams(response.items);
            setError(null);

            // Auto-select default team if none selected
            if (!selectedTeamId && response.items.length > 0) {
                const defaultTeam = response.items.find(t => t.is_default) || response.items[0];
                onTeamChange(defaultTeam.id, defaultTeam);
            }
        } catch (err) {
            setError("Erro ao carregar times");
            console.error("Failed to fetch teams:", err);
        } finally {
            setIsLoading(false);
        }
    }, [selectedTeamId, onTeamChange]);

    useEffect(() => {
        fetchTeams();
    }, [fetchTeams]);

    const selectedTeam = teams.find(t => t.id === selectedTeamId);

    const handleSelect = (team: Team | null) => {
        onTeamChange(team?.id || null, team);
        setIsOpen(false);
    };

    if (error) {
        return (
            <div className="text-xs text-red-500">
                {error}
            </div>
        );
    }

    return (
        <div className={`relative ${className}`}>
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                disabled={disabled || isLoading}
                className={`
                    flex items-center gap-2 rounded-lg border px-3 py-2 text-sm
                    transition-all duration-200
                    ${disabled || isLoading
                        ? "cursor-not-allowed opacity-50"
                        : "hover:border-primary hover:bg-primary/5"
                    }
                    ${isOpen ? "border-primary ring-2 ring-primary/20" : "border-neutral-200 dark:border-neutral-700"}
                    bg-white dark:bg-neutral-800
                `}
            >
                {selectedTeam?.color ? (
                    <span
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: selectedTeam.color }}
                    />
                ) : (
                    <Users className="h-4 w-4 text-neutral-500" />
                )}
                <span className="max-w-[150px] truncate font-medium">
                    {isLoading
                        ? "Carregando..."
                        : selectedTeam?.name || (allowAll ? "Todos os times" : "Selecionar time")
                    }
                </span>
                {selectedTeam && (
                    <span className="text-xs text-neutral-400">
                        ({selectedTeam.repositories_count})
                    </span>
                )}
                <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
            </button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 z-40"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Dropdown */}
                    <div className="absolute left-0 top-full z-50 mt-1 w-64 rounded-lg border border-neutral-200 bg-white shadow-lg dark:border-neutral-700 dark:bg-neutral-800">
                        <div className="max-h-64 overflow-y-auto p-1">
                            {/* All repos option */}
                            {allowAll && (
                                <button
                                    onClick={() => handleSelect(null)}
                                    className={`
                                        flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm
                                        transition-colors hover:bg-neutral-100 dark:hover:bg-neutral-700
                                        ${!selectedTeamId ? "bg-primary/10 text-primary" : ""}
                                    `}
                                >
                                    <Users className="h-4 w-4 text-neutral-400" />
                                    <div className="flex-1">
                                        <div className="font-medium">Todos os repositórios</div>
                                        <div className="text-xs text-neutral-500">
                                            Sem filtro de time
                                        </div>
                                    </div>
                                    {!selectedTeamId && (
                                        <Check className="h-4 w-4 text-primary" />
                                    )}
                                </button>
                            )}

                            {/* Divider */}
                            {allowAll && teams.length > 0 && (
                                <div className="my-1 border-t border-neutral-200 dark:border-neutral-700" />
                            )}

                            {/* Teams */}
                            {teams.length === 0 && !isLoading && (
                                <div className="px-3 py-4 text-center text-sm text-neutral-500">
                                    Nenhum time encontrado.
                                    <br />
                                    <a href="/settings" className="text-primary hover:underline">
                                        Criar time
                                    </a>
                                </div>
                            )}

                            {teams.map((team) => (
                                <button
                                    key={team.id}
                                    onClick={() => handleSelect(team)}
                                    className={`
                                        flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm
                                        transition-colors hover:bg-neutral-100 dark:hover:bg-neutral-700
                                        ${selectedTeamId === team.id ? "bg-primary/10 text-primary" : ""}
                                    `}
                                >
                                    {team.color ? (
                                        <span
                                            className="h-3 w-3 flex-shrink-0 rounded-full"
                                            style={{ backgroundColor: team.color }}
                                        />
                                    ) : (
                                        <span className="h-3 w-3 flex-shrink-0 rounded-full bg-neutral-300" />
                                    )}
                                    <div className="flex-1 overflow-hidden">
                                        <div className="flex items-center gap-2">
                                            <span className="truncate font-medium">{team.name}</span>
                                            {team.is_default && (
                                                <span className="rounded bg-primary/20 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                                                    Padrão
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-xs text-neutral-500">
                                            {team.repositories_count} {team.repositories_count === 1 ? "repositório" : "repositórios"}
                                        </div>
                                    </div>
                                    {selectedTeamId === team.id && (
                                        <Check className="h-4 w-4 flex-shrink-0 text-primary" />
                                    )}
                                </button>
                            ))}
                        </div>

                        {/* Footer actions */}
                        <div className="border-t border-neutral-200 p-2 dark:border-neutral-700">
                            <a
                                href="/settings"
                                className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-neutral-600 transition-colors hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-700"
                            >
                                <Settings className="h-4 w-4" />
                                Gerenciar times
                            </a>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
