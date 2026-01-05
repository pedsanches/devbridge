"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, Loader2, GitCommit, GitPullRequest, TrendingUp, TrendingDown, Minus } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";

interface ActivityItem {
    id: string;
    repository_id: string;
    external_id: string;
    type: "COMMIT" | "PULL_REQUEST";
    title: string;
    content: string | null;
    author: string;
    created_at: string;
    occurred_at: string | null;
    business_update: {
        id: string;
        summary: string;
        impact_level: "LOW" | "MEDIUM" | "HIGH";
        category: string | null;
    } | null;
}

interface PaginatedResponse {
    data: ActivityItem[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function DashboardPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuth();
    const router = useRouter();
    const [activities, setActivities] = useState<ActivityItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push("/login");
        }
    }, [authLoading, isAuthenticated, router]);

    useEffect(() => {
        if (!isAuthenticated) return;

        const fetchActivities = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/activities?page=1&page_size=20`, {
                    credentials: "include",
                });
                if (!response.ok) throw new Error("Failed to fetch activities");
                const data: PaginatedResponse = await response.json();
                setActivities(data.data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Erro ao carregar atividades");
            } finally {
                setIsLoading(false);
            }
        };

        fetchActivities();
    }, [isAuthenticated]);

    if (authLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!isAuthenticated) {
        return null; // Will redirect
    }

    const getImpactIcon = (level: string) => {
        switch (level) {
            case "HIGH":
                return <TrendingUp className="h-4 w-4 text-green-500" />;
            case "MEDIUM":
                return <Minus className="h-4 w-4 text-yellow-500" />;
            default:
                return <TrendingDown className="h-4 w-4 text-neutral-400" />;
        }
    };

    const getImpactBadge = (level: string) => {
        const colors = {
            HIGH: "bg-green-100 text-green-700 ring-1 ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20",
            MEDIUM: "bg-yellow-100 text-yellow-700 ring-1 ring-yellow-600/20 dark:bg-yellow-500/10 dark:text-yellow-400 dark:ring-yellow-500/20",
            LOW: "bg-neutral-100 text-neutral-600 ring-1 ring-neutral-500/10 dark:bg-neutral-800 dark:text-neutral-400 dark:ring-neutral-700/30",
        };
        return colors[level as keyof typeof colors] || colors.LOW;
    };

    return (
        <div className="flex min-h-screen flex-col bg-neutral-50 dark:bg-neutral-900">


            <main className="flex-1 py-8">
                <div className="container mx-auto max-w-4xl px-4">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-white">
                            Dashboard
                        </h1>
                        <p className="mt-2 text-lg text-secondary">
                            Atividades recentes traduzidas para linguagem de negócio
                        </p>
                    </div>

                    {isLoading ? (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="h-10 w-10 animate-spin text-primary/50" />
                        </div>
                    ) : error ? (
                        <div className="rounded-xl bg-red-50 p-6 text-red-600 ring-1 ring-red-100 dark:bg-red-900/10 dark:text-red-400 dark:ring-red-900/20">
                            {error}
                        </div>
                    ) : activities.length === 0 ? (
                        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-neutral-200 bg-neutral-50/50 py-20 text-center dark:border-neutral-800 dark:bg-neutral-900/50">
                            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-neutral-100 dark:bg-neutral-800 dark:ring-neutral-700">
                                <Activity className="h-8 w-8 text-primary/80" />
                            </div>
                            <h2 className="mb-2 text-xl font-semibold text-neutral-900 dark:text-white">Nenhuma atividade ainda</h2>
                            <p className="max-w-md text-secondary">
                                Conecte um repositório GitHub para começar a ver suas atividades técnicas traduzidas.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {activities.map((activity) => (
                                <div
                                    key={activity.id}
                                    className="group relative overflow-hidden rounded-xl border border-neutral-200 bg-white p-5 hover-lift dark:border-neutral-800 dark:bg-neutral-900"
                                >
                                    <div className="mb-4 flex items-start justify-between gap-4">
                                        <div className="flex items-center gap-3">
                                            <div className={`flex h-10 w-10 items-center justify-center rounded-full ${activity.type === 'COMMIT' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400' : 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400'}`}>
                                                {activity.type === "COMMIT" ? (
                                                    <GitCommit className="h-5 w-5" />
                                                ) : (
                                                    <GitPullRequest className="h-5 w-5" />
                                                )}
                                            </div>
                                            <div>
                                                <h3 className="font-medium text-neutral-900 dark:text-white">
                                                    {activity.title}
                                                </h3>
                                            </div>
                                        </div>
                                        {activity.business_update && (
                                            <span
                                                className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium shadow-sm transition-colors ${getImpactBadge(activity.business_update.impact_level)}`}
                                            >
                                                {getImpactIcon(activity.business_update.impact_level)}
                                                {activity.business_update.impact_level}
                                            </span>
                                        )}
                                    </div>

                                    {activity.business_update ? (
                                        <div className="rounded-lg bg-neutral-50 p-4 transition-colors group-hover:bg-primary/5 dark:bg-neutral-800 dark:group-hover:bg-primary/10">
                                            <p className="text-sm leading-relaxed text-neutral-700 dark:text-neutral-300">
                                                {activity.business_update.summary}
                                            </p>
                                            {activity.business_update.category && (
                                                <div className="mt-3 flex gap-2">
                                                    <span className="inline-flex items-center rounded-md bg-white px-2 py-1 text-xs font-medium text-secondary shadow-sm ring-1 ring-neutral-200 dark:bg-neutral-900 dark:ring-neutral-700">
                                                        {activity.business_update.category}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="text-sm italic text-secondary">
                                            Tradução pendente...
                                        </p>
                                    )}

                                    <div className="mt-3 flex flex-col gap-1 text-[10px] text-secondary sm:flex-row sm:items-center sm:justify-between sm:text-xs">
                                        <div className="flex items-center gap-2">
                                            <span>por {activity.author}</span>
                                            <span className="hidden sm:inline">•</span>
                                            <span>{activity.type === "COMMIT" ? "Commit" : "Pull Request"}</span>
                                        </div>
                                        <div className="flex flex-col gap-1 sm:flex-row sm:gap-4">
                                            {activity.occurred_at && (
                                                <span title="Data real do evento no GitHub">
                                                    Ocorrido em: {new Date(activity.occurred_at).toLocaleDateString("pt-BR", {
                                                        day: "2-digit",
                                                        month: "short",
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    })}
                                                </span>
                                            )}
                                            <span title="Data em que foi sincronizado com DevBridge">
                                                Sincro em: {new Date(activity.created_at).toLocaleDateString("pt-BR", {
                                                    day: "2-digit",
                                                    month: "short",
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                })}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
