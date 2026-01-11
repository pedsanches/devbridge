
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { RepoStatusWidget } from "@/components/dashboard/RepoStatusWidget";
import { MetricsBar } from "@/components/dashboard/MetricsBar";
import { QuickChatInput } from "@/components/dashboard/QuickChatInput";
import { TeamSelector } from "@/components/teams/TeamSelector";

// Copied interface to match ActivityFeed expectation
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
    value_tags?: string[] | null;
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
    const { isAuthenticated, isLoading: authLoading, user } = useAuth();
    const router = useRouter();
    const [activities, setActivities] = useState<ActivityItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push("/login");
        }
    }, [authLoading, isAuthenticated, router]);

    useEffect(() => {
        if (!isAuthenticated) return;

        const fetchActivities = async () => {
            try {
                const query = selectedTeamId ? `&team_id=${selectedTeamId}` : "";
                const response = await fetch(`${API_BASE_URL}/activities?page=1&page_size=20${query}`, {
                    credentials: "include",
                });
                if (!response.ok) throw new Error("Failed to fetch activities");
                const data: PaginatedResponse = await response.json();
                setActivities(data.data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Error loading activities");
            } finally {
                setIsLoading(false);
            }
        };

        fetchActivities();
    }, [isAuthenticated, selectedTeamId]);

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

    // Get greeting based on time of day
    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return "Bom dia";
        if (hour < 18) return "Boa tarde";
        return "Boa noite";
    };

    const userName = user?.name || user?.email?.split("@")[0] || "usuário";

    return (
        <div className="flex min-h-screen flex-col bg-[var(--background)]">
            <main className="flex-1 py-8">
                <div className="container mx-auto max-w-6xl px-4">
                    {/* Header with greeting */}
                    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <h1 className="text-2xl font-semibold tracking-tight text-[var(--foreground)]">
                                {getGreeting()}, {userName} 👋
                            </h1>
                            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                                Aqui está o resumo da sua organização
                            </p>
                        </div>
                        <TeamSelector
                            selectedTeamId={selectedTeamId}
                            onTeamChange={(id) => setSelectedTeamId(id)}
                            allowAll
                            allLabel="Visão Global"
                        />
                    </div>

                    {/* Quick Chat Input */}
                    <div className="mb-6">
                        <QuickChatInput />
                    </div>

                    {/* Metrics Bar */}
                    <div className="mb-8">
                        <h2 className="mb-4 text-sm font-medium text-[var(--muted-foreground)] uppercase tracking-wide">
                            Métricas DORA
                        </h2>
                        <MetricsBar teamId={selectedTeamId} />
                    </div>

                    {/* Main Content Grid */}
                    <div className="grid gap-8 lg:grid-cols-3">
                        {/* Main Stream */}
                        <div className="space-y-4 lg:col-span-2">
                            <h2 className="text-sm font-medium text-[var(--muted-foreground)] uppercase tracking-wide">
                                Atividades Recentes
                            </h2>
                            {error ? (
                                <div className="rounded-xl bg-red-50 p-6 text-red-600 ring-1 ring-red-100 dark:bg-red-900/10 dark:text-red-400 dark:ring-red-900/20">
                                    {error}
                                </div>
                            ) : (
                                <ActivityFeed activities={activities} isLoading={isLoading} />
                            )}
                        </div>

                        {/* Sidebar Widgets */}
                        <div className="space-y-6">
                            <h2 className="text-sm font-medium text-[var(--muted-foreground)] uppercase tracking-wide">
                                Repositórios
                            </h2>
                            <RepoStatusWidget />
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
