"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, TrendingUp, Users, Clock, AlertTriangle, Loader2 } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { TeamSelector } from "@/components/teams";
import { Team, getDoraMetrics, DoraMetricsResponse } from "@/services/api";

export default function MetricsPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuth();
    const router = useRouter();
    const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
    const [doraMetrics, setDoraMetrics] = useState<DoraMetricsResponse | null>(null);
    const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push("/login");
        }
    }, [authLoading, isAuthenticated, router]);

    useEffect(() => {
        const fetchMetrics = async () => {
            if (!isAuthenticated) return;

            setIsLoadingMetrics(true);
            try {
                const data = await getDoraMetrics(30, selectedTeam?.id);
                setDoraMetrics(data);
            } catch (error) {
                console.error("Failed to fetch DORA metrics:", error);
            } finally {
                setIsLoadingMetrics(false);
            }
        };

        fetchMetrics();
    }, [isAuthenticated, selectedTeam]);

    if (authLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="flex min-h-screen flex-col bg-[var(--background)]">
            <main className="flex-1 py-8">
                <div className="container mx-auto max-w-6xl px-4">
                    {/* Header */}
                    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <h1 className="flex items-center gap-3 text-2xl font-semibold tracking-tight text-[var(--foreground)]">
                                <BarChart3 className="h-6 w-6" />
                                Métricas
                            </h1>
                            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                                Acompanhe a performance do seu time com métricas DORA e SPACE
                            </p>
                        </div>
                        <div className="w-full sm:w-[250px]">
                            <TeamSelector
                                selectedTeamId={selectedTeam?.id || null}
                                onTeamChange={(_, team) => setSelectedTeam(team)}
                                allowAll
                            />
                        </div>
                    </div>

                    {/* DORA Metrics */}
                    <section className="mb-8">
                        <div className="mb-4 flex items-center justify-between">
                            <h2 className="text-lg font-medium text-[var(--foreground)]">
                                DORA Metrics
                            </h2>
                            {doraMetrics?.overall_level && (
                                <span className={`rounded-full px-3 py-1 text-xs font-medium border ${getStatusColor(doraMetrics.overall_level)}`}>
                                    Nível: <span className="uppercase">{doraMetrics.overall_level}</span>
                                </span>
                            )}
                        </div>

                        {isLoadingMetrics ? (
                            <div className="flex h-32 items-center justify-center">
                                <Loader2 className="h-8 w-8 animate-spin text-[var(--muted-foreground)]" />
                            </div>
                        ) : (
                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                                <MetricCard
                                    title="Deployment Frequency"
                                    value={doraMetrics?.deployment_frequency.formatted || "—"}
                                    description="Deploys por dia"
                                    icon={TrendingUp}
                                    status={doraMetrics?.deployment_frequency.status}
                                    trend={doraMetrics?.deployment_frequency.trend}
                                />
                                <MetricCard
                                    title="Lead Time"
                                    value={doraMetrics?.lead_time.formatted || "—"}
                                    description="Tempo até deploy"
                                    icon={Clock}
                                    status={doraMetrics?.lead_time.status}
                                    trend={doraMetrics?.lead_time.trend}
                                />
                                <MetricCard
                                    title="Change Failure Rate"
                                    value={doraMetrics?.change_failure_rate.formatted || "—"}
                                    description="Taxa de falhas"
                                    icon={AlertTriangle}
                                    status={doraMetrics?.change_failure_rate.status}
                                    trend={doraMetrics?.change_failure_rate.trend}
                                />
                                <MetricCard
                                    title="MTTR"
                                    value={doraMetrics?.mttr.formatted || "—"}
                                    description="Tempo de recuperação"
                                    icon={Clock}
                                    status={doraMetrics?.mttr.status}
                                    trend={doraMetrics?.mttr.trend}
                                />
                            </div>
                        )}
                    </section>

                    {/* SPACE Framework */}
                    <section className="mb-8">
                        <h2 className="mb-4 text-lg font-medium text-[var(--foreground)]">
                            SPACE Framework
                        </h2>
                        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-8 text-center">
                            <Users className="mx-auto mb-4 h-12 w-12 text-[var(--muted-foreground)] opacity-50" />
                            <h3 className="text-lg font-medium text-[var(--foreground)]">
                                Em breve
                            </h3>
                            <p className="mt-2 text-sm text-[var(--muted-foreground)]">
                                Métricas de produtividade holística: Satisfaction, Performance, Activity, Collaboration e Efficiency.
                            </p>
                        </div>
                    </section>

                    {/* Developer Profiles */}
                    <section>
                        <h2 className="mb-4 text-lg font-medium text-[var(--foreground)]">
                            Developer Profiles
                        </h2>
                        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-8 text-center">
                            <Users className="mx-auto mb-4 h-12 w-12 text-[var(--muted-foreground)] opacity-50" />
                            <h3 className="text-lg font-medium text-[var(--foreground)]">
                                Em breve
                            </h3>
                            <p className="mt-2 text-sm text-[var(--muted-foreground)]">
                                Perfis individuais com strength tags, padrões de contribuição e insights de colaboração.
                            </p>
                        </div>
                    </section>
                </div>
            </main>
        </div>
    );
}

interface MetricCardProps {
    title: string;
    value: string;
    description: string;
    icon: React.ElementType;
    status?: "elite" | "high" | "medium" | "low" | "coming-soon" | "active" | undefined;
    trend?: "up" | "down" | "stable" | null | undefined;
}

function MetricCard({ title, value, description, icon: Icon, status = "active", trend }: MetricCardProps) {
    const getStatusColor = (s: string) => {
        switch (s) {
            case "elite": return "text-green-500 bg-green-500/10 border-green-500/20";
            case "high": return "text-blue-500 bg-blue-500/10 border-blue-500/20";
            case "medium": return "text-yellow-500 bg-yellow-500/10 border-yellow-500/20";
            case "low": return "text-red-500 bg-red-500/10 border-red-500/20";
            default: return "text-[var(--muted-foreground)] bg-[var(--muted)]";
        }
    };

    const getTrendIcon = (t?: string | null) => {
        if (!t || t === "stable") return null;
        return t === "up" ? (
            <TrendingUp className="h-3 w-3 text-green-500" />
        ) : (
            <TrendingUp className="h-3 w-3 text-red-500 rotate-180" />
        );
    };

    return (
        <div className={`rounded-xl border p-4 ${status === "coming-soon" ? "bg-[var(--card)] border-[var(--border)]" : "bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800"}`}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm font-medium text-[var(--muted-foreground)]">{title}</p>
                    <div className="flex items-center gap-2 mt-1">
                        <p className="text-2xl font-bold text-[var(--foreground)]">{value}</p>
                        {trend && (
                            <div className="flex items-center">
                                {getTrendIcon(trend)}
                            </div>
                        )}
                    </div>
                    <p className="mt-1 text-xs text-[var(--muted-foreground)]">{description}</p>
                </div>
                <div className={`rounded-lg p-2 ${status === "coming-soon" ? "bg-[var(--muted)]" : getStatusColor(status || "")}`}>
                    <Icon className="h-4 w-4" />
                </div>
            </div>
            {status && status !== "active" && status !== "coming-soon" && (
                <div className={`mt-3 inline-flex rounded-md px-2 py-0.5 text-xs font-medium capitalize ${getStatusColor(status)}`}>
                    {status}
                </div>
            )}
            {status === "coming-soon" && (
                <div className="mt-3 rounded-md bg-[var(--muted)] px-2 py-1 text-center text-xs text-[var(--muted-foreground)]">
                    Em breve
                </div>
            )}
        </div>
    );
}

function getStatusColor(status: string) {
    switch (status) {
        case "elite": return "text-green-600 border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400";
        case "high": return "text-blue-600 border-blue-200 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-400";
        case "medium": return "text-yellow-600 border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-400";
        case "low": return "text-red-600 border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400";
        default: return "text-gray-600 border-gray-200 bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400";
    }
}
