
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { RepoStatusWidget } from "@/components/dashboard/RepoStatusWidget";

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

    return (
        <div className="flex min-h-screen flex-col bg-neutral-50 dark:bg-neutral-900">
            <main className="flex-1 py-8">
                <div className="container mx-auto max-w-6xl px-4">
                    <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-white">
                                Dashboard
                            </h1>
                            <p className="mt-2 text-lg text-secondary">
                                Visão geral das atividades e integridade do projeto
                            </p>
                        </div>
                    </div>

                    <div className="grid gap-8 lg:grid-cols-3">
                        {/* Main Stream */}
                        <div className="space-y-6 lg:col-span-2">
                            <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">Atividades Recentes</h2>
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
                            <RepoStatusWidget />
                            {/* Future widgets can go here */}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
