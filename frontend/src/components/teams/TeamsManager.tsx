"use client";

import { useState, useEffect, useCallback } from "react";
import {
    Users,
    Plus,
    Trash2,
    Edit2,
    Star,
    GitBranch,
    ExternalLink,
    Check,
    X,
    Loader2,
    RefreshCw,
    Sparkles,
    MessageSquare,
    BarChart3,
    Lightbulb,
} from "lucide-react";
import {
    getTeams,
    getTeam,
    createTeam,
    updateTeam,
    deleteTeam,
    setDefaultTeam,
    getDataSources,
    addRepositoriesToTeam,
    removeRepositoriesFromTeam,
    syncGitHubTeams,
    Team,
    TeamDetail,
    DataSource,
    TeamSyncResult,
} from "@/services/api";

// Color palette for teams
const TEAM_COLORS = [
    "#6366F1", // Indigo
    "#8B5CF6", // Violet
    "#EC4899", // Pink
    "#EF4444", // Red
    "#F97316", // Orange
    "#EAB308", // Yellow
    "#22C55E", // Green
    "#14B8A6", // Teal
    "#0EA5E9", // Sky
    "#3B82F6", // Blue
];

interface TeamFormData {
    name: string;
    description: string;
    color: string;
}

export function TeamsManager() {
    const [teams, setTeams] = useState<Team[]>([]);
    const [selectedTeam, setSelectedTeam] = useState<TeamDetail | null>(null);
    const [dataSources, setDataSources] = useState<DataSource[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState<TeamSyncResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showOnboardingCard, setShowOnboardingCard] = useState(() => {
        if (typeof window !== "undefined") {
            return localStorage.getItem("teams_onboarding_dismissed") !== "true";
        }
        return true;
    });

    const dismissOnboarding = () => {
        setShowOnboardingCard(false);
        if (typeof window !== "undefined") {
            localStorage.setItem("teams_onboarding_dismissed", "true");
        }
    };

    const [formData, setFormData] = useState<TeamFormData>({
        name: "",
        description: "",
        color: TEAM_COLORS[0],
    });

    const fetchTeams = useCallback(async () => {
        try {
            setIsLoading(true);
            const [teamsResponse, sourcesResponse] = await Promise.all([
                getTeams(),
                getDataSources(),
            ]);
            setTeams(teamsResponse.items);
            setDataSources(sourcesResponse.sources);
            setError(null);
        } catch (err) {
            setError("Erro ao carregar times");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTeams();
    }, [fetchTeams]);

    const handleSelectTeam = async (teamId: string) => {
        try {
            const detail = await getTeam(teamId);
            setSelectedTeam(detail);
            setIsEditing(false);
            setIsCreating(false);
        } catch (err) {
            console.error("Failed to fetch team details:", err);
        }
    };

    const handleCreateTeam = async () => {
        if (!formData.name.trim()) return;

        try {
            setIsSaving(true);
            const newTeam = await createTeam({
                name: formData.name,
                description: formData.description || undefined,
                color: formData.color,
            });
            setTeams([...teams, newTeam]);
            setFormData({ name: "", description: "", color: TEAM_COLORS[0] });
            setIsCreating(false);
            handleSelectTeam(newTeam.id);
        } catch (err) {
            console.error("Failed to create team:", err);
            setError("Erro ao criar time");
        } finally {
            setIsSaving(false);
        }
    };

    const handleUpdateTeam = async () => {
        if (!selectedTeam || !formData.name.trim()) return;

        try {
            setIsSaving(true);
            const updated = await updateTeam(selectedTeam.id, {
                name: formData.name,
                description: formData.description || undefined,
                color: formData.color,
            });
            setTeams(teams.map(t => (t.id === updated.id ? updated : t)));
            setSelectedTeam({ ...selectedTeam, ...updated });
            setIsEditing(false);
        } catch (err) {
            console.error("Failed to update team:", err);
            setError("Erro ao atualizar time");
        } finally {
            setIsSaving(false);
        }
    };

    const handleDeleteTeam = async (teamId: string) => {
        if (!confirm("Tem certeza que deseja excluir este time?")) return;

        try {
            await deleteTeam(teamId);
            setTeams(teams.filter(t => t.id !== teamId));
            if (selectedTeam?.id === teamId) {
                setSelectedTeam(null);
            }
        } catch (err) {
            console.error("Failed to delete team:", err);
            setError("Erro ao excluir time");
        }
    };

    const handleSetDefault = async (teamId: string) => {
        try {
            await setDefaultTeam(teamId);
            setTeams(teams.map(t => ({ ...t, is_default: t.id === teamId })));
            if (selectedTeam) {
                setSelectedTeam({ ...selectedTeam, is_default: selectedTeam.id === teamId });
            }
        } catch (err) {
            console.error("Failed to set default:", err);
        }
    };

    const handleToggleRepository = async (repoId: string, isInTeam: boolean) => {
        if (!selectedTeam) return;

        try {
            if (isInTeam) {
                await removeRepositoriesFromTeam(selectedTeam.id, [repoId]);
                setSelectedTeam({
                    ...selectedTeam,
                    repositories: selectedTeam.repositories.filter(r => r.id !== repoId),
                    repositories_count: selectedTeam.repositories_count - 1,
                });
            } else {
                await addRepositoriesToTeam(selectedTeam.id, [repoId]);
                const repo = dataSources.find(ds => ds.id === repoId);
                if (repo) {
                    setSelectedTeam({
                        ...selectedTeam,
                        repositories: [
                            ...selectedTeam.repositories,
                            {
                                id: repo.id,
                                name: repo.name,
                                url: repo.url,
                                is_active: repo.is_active,
                                activities_count: repo.activities_count,
                            },
                        ],
                        repositories_count: selectedTeam.repositories_count + 1,
                    });
                }
            }
            // Update team list count
            setTeams(teams.map(t =>
                t.id === selectedTeam.id
                    ? { ...t, repositories_count: t.repositories_count + (isInTeam ? -1 : 1) }
                    : t
            ));
        } catch (err) {
            console.error("Failed to toggle repository:", err);
        }
    };

    const startEditing = () => {
        if (selectedTeam) {
            setFormData({
                name: selectedTeam.name,
                description: selectedTeam.description || "",
                color: selectedTeam.color || TEAM_COLORS[0],
            });
            setIsEditing(true);
        }
    };

    const startCreating = () => {
        setFormData({ name: "", description: "", color: TEAM_COLORS[0] });
        setIsCreating(true);
        setSelectedTeam(null);
        setIsEditing(false);
    };

    const handleSyncGitHub = async () => {
        try {
            setIsSyncing(true);
            setSyncResult(null);
            setError(null);
            const result = await syncGitHubTeams();
            setSyncResult(result);
            // Refresh teams list
            await fetchTeams();
            // Clear success message after 5 seconds
            setTimeout(() => setSyncResult(null), 5000);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Erro ao sincronizar";
            if (message.includes("not connected")) {
                setError("Conecte o GitHub primeiro nas configurações de Fontes de Dados");
            } else {
                setError(message);
            }
            console.error("Sync failed:", err);
        } finally {
            setIsSyncing(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="grid h-full gap-6 lg:grid-cols-[300px_1fr]">
            {/* Sidebar - Team List */}
            <div className="rounded-xl border border-neutral-200 bg-white p-4 dark:border-neutral-700 dark:bg-neutral-800">
                <div className="mb-4 flex items-center justify-between">
                    <h3 className="font-semibold">Times</h3>
                    <button
                        onClick={startCreating}
                        className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary/90"
                    >
                        <Plus className="h-4 w-4" />
                        Novo
                    </button>
                </div>

                {/* Sync with GitHub */}
                <button
                    onClick={handleSyncGitHub}
                    disabled={isSyncing}
                    className="mb-4 flex w-full items-center justify-center gap-2 rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 disabled:opacity-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800"
                >
                    <RefreshCw className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
                    {isSyncing ? "Sincronizando..." : "Sincronizar com GitHub"}
                </button>

                {/* Sync Result */}
                {syncResult && (
                    <div className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
                        <p className="font-medium">{syncResult.message}</p>
                        <p className="mt-1 text-xs">
                            {syncResult.created_teams} criados • {syncResult.updated_teams} atualizados • {syncResult.total_repos_linked} repos vinculados
                        </p>
                    </div>
                )}

                {error && (
                    <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
                        {error}
                    </div>
                )}

                <div className="space-y-2">
                    {teams.length === 0 ? (
                        <p className="py-8 text-center text-sm text-neutral-500">
                            Nenhum time criado.
                            <br />
                            Crie um time para organizar seus repositórios.
                        </p>
                    ) : (
                        teams.map((team) => (
                            <button
                                key={team.id}
                                onClick={() => handleSelectTeam(team.id)}
                                className={`
                                    flex w-full items-center gap-3 rounded-lg p-3 text-left transition-colors
                                    ${selectedTeam?.id === team.id
                                        ? "bg-primary/10 ring-1 ring-primary"
                                        : "hover:bg-neutral-100 dark:hover:bg-neutral-700"
                                    }
                                `}
                            >
                                <span
                                    className="h-4 w-4 flex-shrink-0 rounded-full"
                                    style={{ backgroundColor: team.color || "#6B7280" }}
                                />
                                <div className="flex-1 overflow-hidden">
                                    <div className="flex items-center gap-2">
                                        <span className="truncate font-medium">{team.name}</span>
                                        {team.is_default && (
                                            <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                                        )}
                                    </div>
                                    <div className="text-xs text-neutral-500">
                                        {team.repositories_count} repos
                                    </div>
                                </div>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="rounded-xl border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-800">
                {/* Create Form */}
                {isCreating && (
                    <div>
                        <h3 className="mb-4 text-lg font-semibold">Criar Novo Time</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="mb-1 block text-sm font-medium">Nome</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Ex: Squad Pagamentos"
                                    className="w-full rounded-lg border border-neutral-200 bg-white px-4 py-2 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 dark:border-neutral-700 dark:bg-neutral-900"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-sm font-medium">Descrição (opcional)</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="Descreva o time..."
                                    rows={3}
                                    className="w-full rounded-lg border border-neutral-200 bg-white px-4 py-2 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 dark:border-neutral-700 dark:bg-neutral-900"
                                />
                            </div>
                            <div>
                                <label className="mb-2 block text-sm font-medium">Cor</label>
                                <div className="flex flex-wrap gap-2">
                                    {TEAM_COLORS.map((color) => (
                                        <button
                                            key={color}
                                            onClick={() => setFormData({ ...formData, color })}
                                            className={`
                                                h-8 w-8 rounded-full transition-transform
                                                ${formData.color === color ? "scale-110 ring-2 ring-offset-2 ring-neutral-400" : "hover:scale-105"}
                                            `}
                                            style={{ backgroundColor: color }}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={handleCreateTeam}
                                    disabled={!formData.name.trim() || isSaving}
                                    className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 font-medium text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
                                >
                                    {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                                    Criar Time
                                </button>
                                <button
                                    onClick={() => setIsCreating(false)}
                                    className="rounded-lg border px-4 py-2 transition-colors hover:bg-neutral-100 dark:hover:bg-neutral-700"
                                >
                                    Cancelar
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Team Details */}
                {selectedTeam && !isCreating && (
                    <div>
                        {/* Header */}
                        <div className="mb-6 flex items-start justify-between">
                            <div className="flex items-center gap-4">
                                <span
                                    className="h-10 w-10 rounded-xl"
                                    style={{ backgroundColor: selectedTeam.color || "#6B7280" }}
                                />
                                <div>
                                    {isEditing ? (
                                        <input
                                            type="text"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            className="rounded-lg border border-neutral-200 bg-white px-3 py-1 text-xl font-bold focus:border-primary focus:outline-none dark:border-neutral-700 dark:bg-neutral-900"
                                        />
                                    ) : (
                                        <h2 className="text-xl font-bold">{selectedTeam.name}</h2>
                                    )}
                                    <p className="text-sm text-neutral-500">
                                        {selectedTeam.repositories_count} repositórios • Criado em{" "}
                                        {new Date(selectedTeam.created_at).toLocaleDateString("pt-BR")}
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                {isEditing ? (
                                    <>
                                        <button
                                            onClick={handleUpdateTeam}
                                            disabled={isSaving}
                                            className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white hover:bg-primary/90"
                                        >
                                            {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                                            Salvar
                                        </button>
                                        <button
                                            onClick={() => setIsEditing(false)}
                                            className="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700"
                                        >
                                            <X className="h-4 w-4" />
                                            Cancelar
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <button
                                            onClick={startEditing}
                                            className="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700"
                                        >
                                            <Edit2 className="h-4 w-4" />
                                            Editar
                                        </button>
                                        {!selectedTeam.is_default && (
                                            <button
                                                onClick={() => handleSetDefault(selectedTeam.id)}
                                                className="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700"
                                            >
                                                <Star className="h-4 w-4" />
                                                Tornar Padrão
                                            </button>
                                        )}
                                        <button
                                            onClick={() => handleDeleteTeam(selectedTeam.id)}
                                            className="flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                            Excluir
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Color picker in edit mode */}
                        {isEditing && (
                            <div className="mb-6">
                                <label className="mb-2 block text-sm font-medium">Cor</label>
                                <div className="flex flex-wrap gap-2">
                                    {TEAM_COLORS.map((color) => (
                                        <button
                                            key={color}
                                            onClick={() => setFormData({ ...formData, color })}
                                            className={`
                                                h-8 w-8 rounded-full transition-transform
                                                ${formData.color === color ? "scale-110 ring-2 ring-offset-2" : "hover:scale-105"}
                                            `}
                                            style={{ backgroundColor: color }}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Description */}
                        {(selectedTeam.description || isEditing) && (
                            <div className="mb-6">
                                {isEditing ? (
                                    <textarea
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        placeholder="Descrição do time..."
                                        rows={2}
                                        className="w-full rounded-lg border border-neutral-200 bg-white px-4 py-2 text-sm focus:border-primary focus:outline-none dark:border-neutral-700 dark:bg-neutral-900"
                                    />
                                ) : (
                                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                                        {selectedTeam.description}
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Repositories */}
                        <div>
                            <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                                <GitBranch className="h-5 w-5" />
                                Repositórios
                            </h3>

                            <div className="space-y-2">
                                {dataSources.map((source) => {
                                    const isInTeam = selectedTeam.repositories.some(r => r.id === source.id);
                                    return (
                                        <div
                                            key={source.id}
                                            className={`
                                                flex items-center justify-between rounded-lg border p-3
                                                transition-all duration-300 ease-out
                                                ${isInTeam
                                                    ? "border-primary/30 bg-primary/5 shadow-sm shadow-primary/10 scale-[1.01]"
                                                    : "border-neutral-200 hover:border-neutral-300 dark:border-neutral-700 dark:hover:border-neutral-600"
                                                }
                                            `}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className={`
                                                    flex h-9 w-9 items-center justify-center rounded-lg transition-colors duration-300
                                                    ${isInTeam ? "bg-primary/10" : "bg-neutral-100 dark:bg-neutral-800"}
                                                `}>
                                                    <GitBranch className={`h-5 w-5 transition-colors duration-300 ${isInTeam ? "text-primary" : "text-neutral-500"}`} />
                                                </div>
                                                <div>
                                                    <div className="font-medium">{source.name}</div>
                                                    <div className="text-xs text-neutral-500">
                                                        {source.activities_count} atividades
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <a
                                                    href={source.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="p-1 text-neutral-400 transition-colors hover:text-neutral-600"
                                                >
                                                    <ExternalLink className="h-4 w-4" />
                                                </a>
                                                <button
                                                    onClick={() => handleToggleRepository(source.id, isInTeam)}
                                                    className={`
                                                        group relative overflow-hidden rounded-lg px-3 py-1.5 text-sm font-medium
                                                        transition-all duration-300
                                                        ${isInTeam
                                                            ? "bg-primary text-white shadow-md shadow-primary/25 hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/30"
                                                            : "border border-neutral-200 hover:bg-neutral-100 hover:border-primary/30 dark:border-neutral-700 dark:hover:bg-neutral-700"
                                                        }
                                                    `}
                                                >
                                                    {isInTeam ? (
                                                        <>
                                                            <Check className="mr-1 inline h-4 w-4 animate-[bounce_0.3s_ease-out]" />
                                                            Adicionado
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Plus className="mr-1 inline h-4 w-4 transition-transform group-hover:rotate-90" />
                                                            Adicionar
                                                        </>
                                                    )}
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })}

                                {dataSources.length === 0 && (
                                    <div className="rounded-lg border border-dashed border-neutral-300 p-8 text-center dark:border-neutral-600">
                                        <GitBranch className="mx-auto mb-2 h-8 w-8 text-neutral-400" />
                                        <p className="text-neutral-500">
                                            Nenhum repositório disponível.
                                            <br />
                                            Conecte sua conta GitHub nas integrações.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Onboarding Card */}
                {showOnboardingCard && teams.length > 0 && !selectedTeam && !isCreating && (
                    <div className="relative mb-6 overflow-hidden rounded-xl border border-primary/20 bg-gradient-to-br from-primary/5 via-primary/10 to-violet-500/5 p-6">
                        <button
                            onClick={dismissOnboarding}
                            className="absolute right-3 top-3 rounded-full p-1 text-neutral-400 transition-colors hover:bg-neutral-200 hover:text-neutral-600 dark:hover:bg-neutral-700"
                            aria-label="Fechar"
                        >
                            <X className="h-4 w-4" />
                        </button>
                        <div className="flex items-start gap-4">
                            <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-primary/10">
                                <Lightbulb className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h3 className="mb-1 font-semibold text-neutral-900 dark:text-neutral-100">
                                    💡 Dica: Times focam seu contexto
                                </h3>
                                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                                    Selecione um time para ver seus repositórios, ou crie um novo para organizar projetos relacionados.
                                    O chat e os relatórios usarão automaticamente o contexto do time selecionado.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Empty State - Enhanced */}
                {!selectedTeam && !isCreating && (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        {/* Decorative gradient background */}
                        <div className="relative mb-6">
                            <div className="absolute inset-0 blur-3xl">
                                <div className="h-24 w-24 rounded-full bg-gradient-to-br from-primary/30 to-violet-500/30" />
                            </div>
                            <div className="relative flex h-24 w-24 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-violet-500/10 ring-1 ring-primary/20">
                                <Users className="h-10 w-10 text-primary" />
                            </div>
                        </div>

                        <h3 className="mb-2 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
                            {teams.length === 0 ? "Crie seu primeiro time" : "Selecione um time"}
                        </h3>
                        <p className="mb-8 max-w-md text-neutral-500">
                            {teams.length === 0
                                ? "Times agrupam repositórios para contexto focado em relatórios e chat."
                                : "Clique em um time na lista à esquerda para gerenciar seus repositórios."
                            }
                        </p>

                        {/* Feature highlights - only show when no teams */}
                        {teams.length === 0 && (
                            <div className="mb-8 grid w-full max-w-lg gap-4 text-left sm:grid-cols-3">
                                <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-700 dark:bg-neutral-800/50">
                                    <MessageSquare className="mb-2 h-5 w-5 text-primary" />
                                    <h4 className="text-sm font-medium">Chat Focado</h4>
                                    <p className="text-xs text-neutral-500">Pergunte sobre o contexto do time</p>
                                </div>
                                <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-700 dark:bg-neutral-800/50">
                                    <BarChart3 className="mb-2 h-5 w-5 text-violet-500" />
                                    <h4 className="text-sm font-medium">Métricas DORA</h4>
                                    <p className="text-xs text-neutral-500">Acompanhe performance por time</p>
                                </div>
                                <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-700 dark:bg-neutral-800/50">
                                    <Sparkles className="mb-2 h-5 w-5 text-amber-500" />
                                    <h4 className="text-sm font-medium">Relatórios IA</h4>
                                    <p className="text-xs text-neutral-500">Gere resumos executivos</p>
                                </div>
                            </div>
                        )}

                        {teams.length === 0 && (
                            <button
                                onClick={startCreating}
                                className="group flex items-center gap-2 rounded-xl bg-primary px-6 py-3 font-medium text-white shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl hover:shadow-primary/30"
                            >
                                <Plus className="h-5 w-5 transition-transform group-hover:rotate-90" />
                                Criar Primeiro Time
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
