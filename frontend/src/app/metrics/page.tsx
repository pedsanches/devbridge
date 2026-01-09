"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, TrendingUp, Users, Clock, AlertTriangle, Loader2 } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";

export default function MetricsPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push("/login");
        }
    }, [authLoading, isAuthenticated, router]);

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
                    <div className="mb-8">
                        <h1 className="flex items-center gap-3 text-2xl font-semibold tracking-tight text-[var(--foreground)]">
                            <BarChart3 className="h-6 w-6" />
                            Métricas
                        </h1>
                        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                            Acompanhe a performance do seu time com métricas DORA e SPACE
                        </p>
                    </div>

                    {/* DORA Metrics */}
                    <section className="mb-8">
                        <h2 className="mb-4 text-lg font-medium text-[var(--foreground)]">
                            DORA Metrics
                        </h2>
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            <MetricCard
                                title="Deployment Frequency"
                                value="—"
                                description="Deploys por dia"
                                icon={TrendingUp}
                                status="coming-soon"
                            />
                            <MetricCard
                                title="Lead Time"
                                value="—"
                                description="Tempo até deploy"
                                icon={Clock}
                                status="coming-soon"
                            />
                            <MetricCard
                                title="Change Failure Rate"
                                value="—"
                                description="Taxa de falhas"
                                icon={AlertTriangle}
                                status="coming-soon"
                            />
                            <MetricCard
                                title="MTTR"
                                value="—"
                                description="Tempo de recuperação"
                                icon={Clock}
                                status="coming-soon"
                            />
                        </div>
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
    status?: "coming-soon" | "active";
}

function MetricCard({ title, value, description, icon: Icon, status = "active" }: MetricCardProps) {
    return (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm font-medium text-[var(--muted-foreground)]">{title}</p>
                    <p className="mt-1 text-2xl font-bold text-[var(--foreground)]">{value}</p>
                    <p className="mt-1 text-xs text-[var(--muted-foreground)]">{description}</p>
                </div>
                <div className="rounded-lg bg-[var(--muted)] p-2">
                    <Icon className="h-4 w-4 text-[var(--muted-foreground)]" />
                </div>
            </div>
            {status === "coming-soon" && (
                <div className="mt-3 rounded-md bg-[var(--muted)] px-2 py-1 text-center text-xs text-[var(--muted-foreground)]">
                    Em breve
                </div>
            )}
        </div>
    );
}
