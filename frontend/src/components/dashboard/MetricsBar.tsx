"use client";

import { useEffect, useState } from "react";
import { TrendingUp, Clock, AlertTriangle, RefreshCw, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface MetricData {
    value: string | number;
    formatted?: string;
    change?: number | null;
    trend?: "up" | "down" | "stable";
    status?: "elite" | "high" | "medium" | "low";
}

interface MetricsResponse {
    deployment_frequency: MetricData;
    lead_time: MetricData;
    change_failure_rate: MetricData;
    mttr: MetricData;
    overall_level?: string;
}

const statusColors = {
    elite: "text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20",
    high: "text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20",
    medium: "text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20",
    low: "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20",
};

const statusLabels = {
    elite: "Elite",
    high: "High",
    medium: "Medium",
    low: "Low",
};

export function MetricsBar({ teamId }: { teamId?: string | null }) {
    const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                setIsLoading(true);
                const query = teamId ? `&team_id=${teamId}` : "";
                const response = await fetch(`${API_BASE_URL}/metrics/dora?days=30${query}`, {
                    credentials: "include",
                });

                if (response.ok) {
                    const data = await response.json();
                    // Map API response to component format
                    setMetrics({
                        deployment_frequency: {
                            value: data.deployment_frequency.formatted,
                            change: data.deployment_frequency.change,
                            trend: data.deployment_frequency.trend as "up" | "down" | "stable",
                            status: data.deployment_frequency.status as "elite" | "high" | "medium" | "low",
                        },
                        lead_time: {
                            value: data.lead_time.formatted,
                            change: data.lead_time.change,
                            trend: data.lead_time.trend as "up" | "down" | "stable",
                            status: data.lead_time.status as "elite" | "high" | "medium" | "low",
                        },
                        change_failure_rate: {
                            value: data.change_failure_rate.formatted,
                            change: data.change_failure_rate.change,
                            trend: data.change_failure_rate.trend as "up" | "down" | "stable",
                            status: data.change_failure_rate.status as "elite" | "high" | "medium" | "low",
                        },
                        mttr: {
                            value: data.mttr.formatted,
                            change: data.mttr.change,
                            trend: data.mttr.trend as "up" | "down" | "stable",
                            status: data.mttr.status as "elite" | "high" | "medium" | "low",
                        },
                        overall_level: data.overall_level,
                    });
                } else {
                    // Use placeholder if API call fails
                    throw new Error("API not available");
                }
            } catch (err) {
                console.error("Error fetching metrics, using placeholder:", err);
                // Placeholder data for demo
                setMetrics({
                    deployment_frequency: { value: "—", status: "medium", trend: "stable" },
                    lead_time: { value: "—", status: "medium", trend: "stable" },
                    change_failure_rate: { value: "—", status: "medium", trend: "stable" },
                    mttr: { value: "—", status: "medium", trend: "stable" },
                });
            } finally {
                setIsLoading(false);
            }
        };

        fetchMetrics();
    }, [teamId]);

    if (isLoading) {
        return (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[1, 2, 3, 4].map((i) => (
                    <div
                        key={i}
                        className="animate-pulse rounded-xl border border-[var(--border)] bg-[var(--card)] p-4"
                    >
                        <div className="h-4 w-24 rounded bg-[var(--muted)]" />
                        <div className="mt-2 h-8 w-16 rounded bg-[var(--muted)]" />
                        <div className="mt-2 h-3 w-12 rounded bg-[var(--muted)]" />
                    </div>
                ))}
            </div>
        );
    }

    if (!metrics) return null;

    return (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
                title="Deployment Frequency"
                icon={TrendingUp}
                value={metrics.deployment_frequency.value}
                change={metrics.deployment_frequency.change}
                trend={metrics.deployment_frequency.trend}
                status={metrics.deployment_frequency.status}
                description="Deploys per day"
            />
            <MetricCard
                title="Lead Time"
                icon={Clock}
                value={metrics.lead_time.value}
                change={metrics.lead_time.change}
                trend={metrics.lead_time.trend}
                status={metrics.lead_time.status}
                description="Time to deploy"
                invertTrend // Lower is better
            />
            <MetricCard
                title="Change Failure Rate"
                icon={AlertTriangle}
                value={metrics.change_failure_rate.value}
                change={metrics.change_failure_rate.change}
                trend={metrics.change_failure_rate.trend}
                status={metrics.change_failure_rate.status}
                description="Failure rate"
                invertTrend // Lower is better
            />
            <MetricCard
                title="MTTR"
                icon={RefreshCw}
                value={metrics.mttr.value}
                change={metrics.mttr.change}
                trend={metrics.mttr.trend}
                status={metrics.mttr.status}
                description="Recovery time"
                invertTrend // Lower is better
            />
        </div>
    );
}

interface MetricCardProps {
    title: string;
    icon: React.ElementType;
    value: string | number;
    change?: number | null | undefined;
    trend?: "up" | "down" | "stable" | undefined;
    status?: "elite" | "high" | "medium" | "low" | undefined;
    description: string;
    invertTrend?: boolean; // If true, "down" trend is good
}

function MetricCard({
    title,
    icon: Icon,
    value,
    change,
    trend,
    status = "medium",
    description,
    invertTrend = false,
}: MetricCardProps) {
    const isPositive = invertTrend ? trend === "down" : trend === "up";
    const isNegative = invertTrend ? trend === "up" : trend === "down";

    // Format change as percentage
    const formattedChange = change != null
        ? `${change >= 0 ? "+" : ""}${Math.abs(change).toFixed(0)}%`
        : null;

    return (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 transition-all hover:shadow-md">
            <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wide">
                    {title}
                </span>
                <div className={`rounded-lg p-1.5 ${statusColors[status]}`}>
                    <Icon className="h-3.5 w-3.5" />
                </div>
            </div>

            <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-[var(--foreground)]">
                    {value}
                </span>
                {formattedChange && (
                    <span
                        className={`flex items-center text-xs font-medium ${isPositive
                            ? "text-green-600 dark:text-green-400"
                            : isNegative
                                ? "text-red-600 dark:text-red-400"
                                : "text-[var(--muted-foreground)]"
                            }`}
                    >
                        {trend === "up" && <ArrowUpRight className="h-3 w-3" />}
                        {trend === "down" && <ArrowDownRight className="h-3 w-3" />}
                        {trend === "stable" && <Minus className="h-3 w-3" />}
                        {formattedChange}
                    </span>
                )}
            </div>

            <div className="mt-1 flex items-center justify-between">
                <span className="text-xs text-[var(--muted-foreground)]">
                    {description}
                </span>
                {status && (
                    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${statusColors[status]}`}>
                        {statusLabels[status]}
                    </span>
                )}
            </div>
        </div>
    );
}
