import { GitCommit, GitPullRequest, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

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

interface ActivityFeedProps {
    activities: ActivityItem[];
    isLoading?: boolean;
}

export function ActivityFeed({ activities, isLoading }: ActivityFeedProps) {
    if (isLoading) {
        return <div className="space-y-4">
            {[1, 2, 3].map((i) => (
                <div key={i} className="h-40 animate-pulse rounded-xl bg-[var(--muted)]" />
            ))}
        </div>
    }

    if (activities.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-center text-secondary">
                <p>Nenhuma atividade encontrada.</p>
            </div>
        );
    }

    const getImpactBadgeVariant = (level: string) => {
        switch (level) {
            case "HIGH": return "success";
            case "MEDIUM": return "warning";
            default: return "secondary";
        }
    };

    const getImpactIcon = (level: string) => {
        switch (level) {
            case "HIGH": return <TrendingUp className="mr-1 h-3 w-3" />;
            case "MEDIUM": return <Minus className="mr-1 h-3 w-3" />;
            default: return <TrendingDown className="mr-1 h-3 w-3" />;
        }
    };

    const VALUE_TAG_COLORS: Record<string, string> = {
        RISK_MITIGATION: "bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400",
        VELOCITY_ENABLER: "bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400",
        COST_SAVING: "bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400",
        FEATURE_DELIVERY: "bg-purple-100 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400",
        TECH_DEBT: "bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400",
    };

    const VALUE_TAG_LABELS: Record<string, string> = {
        RISK_MITIGATION: "Risco",
        VELOCITY_ENABLER: "Velocidade",
        COST_SAVING: "Custo",
        FEATURE_DELIVERY: "Feature",
        TECH_DEBT: "Tech Debt",
    };

    return (
        <div className="space-y-4">
            {activities.map((activity, index) => {
                const dateToUse = activity.occurred_at || activity.created_at;
                const isOccurredAtAvailable = !!activity.occurred_at;

                return (
                    <div
                        key={activity.id}
                        className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-backwards"
                        style={{ animationDelay: `${index * 50}ms` }}
                    >
                        <Card className="group overflow-hidden transition-all hover:shadow-md dark:hover:border-neutral-700">
                            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
                                <div className="flex items-start gap-4">
                                    <div className={cn(
                                        "mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--muted)]",
                                        activity.type === "COMMIT" && "text-blue-500 dark:text-blue-400",
                                        activity.type === "PULL_REQUEST" && "text-purple-500 dark:text-purple-400"
                                    )}>
                                        {activity.type === "COMMIT" ? <GitCommit className="h-5 w-5" /> : <GitPullRequest className="h-5 w-5" />}
                                    </div>
                                    <div className="space-y-1">
                                        <CardTitle className="text-base font-medium leading-tight">
                                            {activity.title}
                                        </CardTitle>
                                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-secondary">
                                            <span className="font-medium text-[var(--foreground)]">{activity.author}</span>
                                            <span>•</span>
                                            <span title={isOccurredAtAvailable ? "Data de ocorrência (Original)" : "Data de criação (Sistema)"}>
                                                {format(new Date(dateToUse), "d 'de' MMM, HH:mm", { locale: ptBR })}
                                            </span>
                                            <span className="font-mono text-[10px] opacity-60">#{activity.external_id.substring(0, 7)}</span>
                                        </div>
                                    </div>
                                </div>
                                {activity.business_update && (
                                    <Badge variant={getImpactBadgeVariant(activity.business_update.impact_level)} className="shrink-0 h-6 px-2 font-normal">
                                        {getImpactIcon(activity.business_update.impact_level)}
                                        {activity.business_update.impact_level}
                                    </Badge>
                                )}
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {activity.business_update ? (
                                    <div className="rounded-lg bg-[var(--muted)] p-3 text-sm text-[var(--muted-foreground)]">
                                        {activity.business_update.summary}
                                    </div>
                                ) : (
                                    <p className="text-sm italic text-secondary">Aguardando análise de negócio...</p>
                                )}

                                {/* Tags Section - Always render container if any tags exist to maintain layout stability */}
                                {(activity.value_tags?.length || activity.business_update?.category) ? (
                                    <div className="flex flex-wrap gap-2 pt-1">
                                        {activity.business_update?.category && (
                                            <Badge variant="outline" className="text-[10px] text-secondary border-[var(--border)]">
                                                {activity.business_update.category}
                                            </Badge>
                                        )}
                                        {activity.value_tags?.map((tag) => (
                                            <span
                                                key={tag}
                                                className={cn(
                                                    "inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-medium transition-colors border border-transparent",
                                                    VALUE_TAG_COLORS[tag] || "bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-400"
                                                )}
                                            >
                                                {VALUE_TAG_LABELS[tag] || tag}
                                            </span>
                                        ))}
                                    </div>
                                ) : null}
                            </CardContent>
                        </Card>
                    </div>
                );
            })}
        </div>
    );
}
