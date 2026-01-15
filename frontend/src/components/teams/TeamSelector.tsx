"use client";

import { useState, useEffect, useRef, useSyncExternalStore } from "react";
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

type TeamStoreStatus = "idle" | "loading" | "loaded" | "error";

interface TeamStoreState {
    status: TeamStoreStatus;
    teams: Team[];
}

const teamStore = {
    state: { status: "idle", teams: [] as Team[] },
    listeners: new Set<() => void>(),
};

const getTeamStoreSnapshot = (): TeamStoreState => teamStore.state;

const subscribeTeamStore = (listener: () => void) => {
    teamStore.listeners.add(listener);
    return () => teamStore.listeners.delete(listener);
};

const notifyTeamStore = () => {
    teamStore.listeners.forEach((listener) => listener());
};

const setTeamStoreState = (state: TeamStoreState) => {
    teamStore.state = state;
    notifyTeamStore();
};

const ensureTeamsLoaded = async () => {
    if (teamStore.state.status !== "idle") {
        return;
    }

    setTeamStoreState({ ...teamStore.state, status: "loading" });

    try {
        const response = await getTeams(1, 100);
        setTeamStoreState({ status: "loaded", teams: response.items });
    } catch (error) {
        console.error("Failed to fetch teams:", error);
        setTeamStoreState({ status: "error", teams: [] });
    }
};

function useTeamsStore(enabled: boolean): TeamStoreState {
    const snapshot = useSyncExternalStore(
        subscribeTeamStore,
        getTeamStoreSnapshot,
        getTeamStoreSnapshot
    );

    useEffect(() => {
        if (enabled && snapshot.status === "idle") {
            void ensureTeamsLoaded();
        }
    }, [enabled, snapshot.status]);

    return snapshot;
}

export function TeamSelector({
    selectedTeamId,
    onTeamChange,
    disabled = false,
    allowAll = false,
    className = "",
    allLabel = "Visão Global",
}: TeamSelectorProps) {
    const [open, setOpen] = useState(false);
    // We need to know the selected team name for the trigger button,
    // so we might need a local fetch or lift the state up.
    // For now, let's keep it simple: TeamSelectorContent handles selection.
    // Ideally, `selectedTeam` object should be passed as prop.
    // To avoid breaking changes, we'll fetch briefly just to get the name if needed,
    // or rely on a "dumb" trigger if data isn't available yet.

    // Quick fix: Use a lightweight fetch or just accept that we might not have the name immediately
    // if we fully decouple. However, the original component did fetch.

    // Let's rely on TeamSelectorContent? No, because trigger is outside content.
    // So we keep the fetch logic here (or shared hook) to populate the trigger label.

    const teamSnapshot = useTeamsStore(true);
    const teams = teamSnapshot.teams;
    const isLoading = teamSnapshot.status === "loading";

    // Track if we've attempted to set the default team
    const hasSetDefault = useRef(false);

    useEffect(() => {
        if (!selectedTeamId && !hasSetDefault.current && teams.length > 0) {
            const defaultTeam = teams.find((team) => team.is_default) ?? teams[0] ?? null;

            // If we found a default team, select it (even if allowAll is true)
            // This forces the "Default Team" to be the initial view
            if (defaultTeam && defaultTeam.is_default) {
                onTeamChange(defaultTeam.id, defaultTeam);
            }

            hasSetDefault.current = true;
        }
    }, [onTeamChange, selectedTeamId, teams]);

    const selectedTeam = teams.find((team) => team.id === selectedTeamId);

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
                <TeamSelectorContent
                    selectedTeamId={selectedTeamId}
                    onTeamChange={(id, team) => {
                        onTeamChange(id, team);
                        setOpen(false);
                    }}
                    allowAll={allowAll}
                    allLabel={allLabel}
                    teams={teams} // Pass pre-fetched teams to avoid double fetch if possible, or let it fetch
                />
            </PopoverContent>
        </Popover>
    );
}

interface TeamSelectorContentProps extends Omit<TeamSelectorProps, "disabled" | "className"> {
    teams?: Team[]; // Optional pre-fetched teams
}

export function TeamSelectorContent({
    selectedTeamId,
    onTeamChange,
    allowAll = false,
    allLabel = "Visão Global",
    teams: parentTeams,
}: TeamSelectorContentProps) {
    const teamSnapshot = useTeamsStore(!parentTeams);
    const teams = parentTeams ?? teamSnapshot.teams;

    return (
        <Command>
            <CommandInput placeholder="Procurar time..." />
            <CommandList>
                <CommandEmpty>Time não encontrado.</CommandEmpty>

                {allowAll && (
                    <>
                        <CommandGroup>
                            <CommandItem
                                value="all-teams-global-view"
                                onSelect={() => onTeamChange(null, null)}
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
                            onSelect={() => onTeamChange(team.id, team)}
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
                >
                    <Settings className="h-3 w-3" />
                    Gerenciar times
                </Link>
            </div>
        </Command>
    );
}
