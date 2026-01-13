"use client";

import { useState, useEffect, useCallback } from "react";
import { Users, Check, ChevronsUpDown, Settings } from "lucide-react";
import { getTeams, Team } from "@/services/api";
import { Button } from "@/components/ui/button";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
    CommandSeparator,
} from "@/components/ui/command";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface TeamSelectorProps {
    selectedTeamId: string | null;
    onTeamChange: (teamId: string | null, team: Team | null) => void;
    disabled?: boolean;
    allowAll?: boolean; // If true, shows "Todos os times" option
    className?: string;
    allLabel?: string; // Custom label for "All" option
}

export function TeamSelector({
    selectedTeamId,
    onTeamChange,
    disabled = false,
    allowAll = false,
    className = "",
    allLabel = "Visão Global",
}: TeamSelectorProps) {
    const [teams, setTeams] = useState<Team[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [open, setOpen] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchTeams = useCallback(async () => {
        try {
            setIsLoading(true);
            const response = await getTeams(1, 100);
            setTeams(response.items);
            setError(null);

            // Auto-select default team if none selected and NOT allowing all
            if (!selectedTeamId && !allowAll && response.items.length > 0) {
                const defaultTeam = response.items.find(t => t.is_default) ?? response.items[0];
                if (defaultTeam) {
                    onTeamChange(defaultTeam.id, defaultTeam);
                }
            }
        } catch (err) {
            setError("Erro ao carregar times");
            console.error("Failed to fetch teams:", err);
        } finally {
            setIsLoading(false);
        }
    }, [allowAll, selectedTeamId, onTeamChange]);

    useEffect(() => {
        fetchTeams();
    }, [fetchTeams]);

    const selectedTeam = teams.find(t => t.id === selectedTeamId);

    if (error) {
        return (
            <div className="text-xs text-red-500">
                {error}
            </div>
        );
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={open}
                    className={cn("w-[220px] justify-between", className)}
                    disabled={disabled || isLoading}
                >
                    <div className="flex items-center gap-2 truncate">
                        {selectedTeam?.color ? (
                            <span
                                className="h-2 w-2 rounded-full"
                                style={{ backgroundColor: selectedTeam.color }}
                            />
                        ) : (
                            <Users className="h-4 w-4 shrink-0 opacity-50" />
                        )}
                        <span className="truncate">
                            {selectedTeam
                                ? selectedTeam.name
                                : allowAll
                                    ? allLabel
                                    : "Selecionar time..."}
                        </span>
                    </div>
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[220px] p-0" align="start">
                <Command>
                    <CommandInput placeholder="Procurar time..." />
                    <CommandList>
                        <CommandEmpty>Time não encontrado.</CommandEmpty>

                        {allowAll && (
                            <>
                                <CommandGroup>
                                    <CommandItem
                                        value="all-teams-global-view"
                                        onSelect={() => {
                                            onTeamChange(null, null);
                                            setOpen(false);
                                        }}
                                        className="flex items-center gap-2"
                                    >
                                        <Check
                                            className={cn(
                                                "h-4 w-4",
                                                selectedTeamId === null ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                        <Users className="h-4 w-4 opacity-50" />
                                        {allLabel}
                                    </CommandItem>
                                </CommandGroup>
                                <CommandSeparator />
                            </>
                        )}

                        <CommandGroup heading="Meus Times">
                            {teams.map((team) => (
                                <CommandItem
                                    key={team.id}
                                    value={team.name}
                                    onSelect={() => {
                                        onTeamChange(team.id, team);
                                        setOpen(false);
                                    }}
                                    className="flex items-center gap-2"
                                >
                                    <Check
                                        className={cn(
                                            "h-4 w-4",
                                            selectedTeamId === team.id
                                                ? "opacity-100"
                                                : "opacity-0"
                                        )}
                                    />
                                    {team.color ? (
                                        <span
                                            className="h-2 w-2 rounded-full"
                                            style={{ backgroundColor: team.color }}
                                        />
                                    ) : (
                                        <span className="h-2 w-2 rounded-full bg-neutral-300" />
                                    )}
                                    <span className="truncate">{team.name}</span>
                                    {team.is_default && (
                                        <span className="ml-auto text-[10px] text-muted-foreground">
                                            Padrão
                                        </span>
                                    )}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    </CommandList>
                    <div className="border-t p-1">
                        <Link
                            href="/settings"
                            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            onClick={() => setOpen(false)}
                        >
                            <Settings className="h-3 w-3" />
                            Gerenciar times
                        </Link>
                    </div>
                </Command>
            </PopoverContent>
        </Popover>
    );
}
