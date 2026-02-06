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
    state: { status: "idle" as TeamStoreStatus, teams: [] as Team[] },
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
                    variant="ghost"
                    role="combobox"
                    aria-expanded={open}
                    className={cn(
                        "glass hover-lift active:scale-[0.98] w-[220px] justify-between border-0 shadow-lg",
                        "hover:bg-white/10 data-[state=open]:bg-white/10 data-[state=open]:ring-2 data-[state=open]:ring-primary/20",
                        className
                    )}
                    disabled={disabled || isLoading}
                >
                    <div className="flex items-center gap-2 truncate">
                        {selectedTeam?.color ? (
                            <span
                                className="h-2 w-2 rounded-full ring-1 ring-white/20"
                                style={{ backgroundColor: selectedTeam.color }}
                            />
                        ) : (
                            <Users className="h-4 w-4 shrink-0 opacity-70" />
                        )}
                        <span className="truncate font-medium">
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
            <PopoverContent
                className="glass-panel w-[220px] p-0 border-0 shadow-2xl backdrop-blur-3xl"
                align="start"
                sideOffset={8}
            >
                <TeamSelectorContent
                    selectedTeamId={selectedTeamId}
                    onTeamChange={(id, team) => {
                        onTeamChange(id, team);
                        setOpen(false);
                    }}
                    allowAll={allowAll}
                    allLabel={allLabel}
                    teams={teams}
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
        <Command className="bg-transparent">
            <CommandInput placeholder="Procurar time..." className="border-none focus:ring-0" />
            <CommandList className="max-h-[240px] sidebar-scroll p-1">
                <CommandEmpty className="py-2 text-center text-sm text-muted-foreground">
                    Time não encontrado.
                </CommandEmpty>

                {allowAll && (
                    <>
                        <CommandGroup>
                            <CommandItem
                                value="all-teams-global-view"
                                onSelect={() => onTeamChange(null, null)}
                                className={cn(
                                    "flex items-center gap-2 rounded-lg px-2 py-2 aria-selected:bg-primary/10 aria-selected:text-primary",
                                    selectedTeamId === null && "bg-primary/10 text-primary"
                                )}
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
                        <CommandSeparator className="my-1 h-px bg-white/10" />
                    </>
                )}

                <CommandGroup heading="Meus Times" className="text-muted-foreground">
                    {teams.map((team) => (
                        <CommandItem
                            key={team.id}
                            value={team.name}
                            onSelect={() => onTeamChange(team.id, team)}
                            className={cn(
                                "flex items-center gap-2 rounded-lg px-2 py-2 aria-selected:bg-primary/10 aria-selected:text-primary",
                                selectedTeamId === team.id && "bg-primary/10 text-primary"
                            )}
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
                                    className="h-2 w-2 rounded-full ring-1 ring-white/10"
                                    style={{ backgroundColor: team.color }}
                                />
                            ) : (
                                <span className="h-2 w-2 rounded-full bg-neutral-300" />
                            )}
                            <span className="truncate">{team.name}</span>
                            {team.is_default && (
                                <span className="ml-auto text-[10px] text-muted-foreground border border-border px-1 rounded-sm">
                                    Padrão
                                </span>
                            )}
                        </CommandItem>
                    ))}
                </CommandGroup>
            </CommandList>
            <div className="border-t border-white/10 p-1.5">
                <Link
                    href="/settings/members"
                    className="
                        flex w-full items-center justify-center gap-2 rounded-lg px-2 py-2 text-xs font-medium
                        text-muted-foreground transition-all duration-200
                        hover:bg-primary/10 hover:text-primary group
                        border border-dashed border-muted-foreground/30 hover:border-primary/30
                    "
                >
                    <Settings className="h-3.5 w-3.5 group-hover:rotate-45 transition-transform" />
                    Gerenciar times
                </Link>
            </div>
        </Command>
    );
}
