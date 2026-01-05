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
                <div key={i} className="h-40 animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-800" />
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

    return (
        <div className="space-y-4">
            {activities.map((activity, index) => (
                <div
                    key={activity.id}
                    className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-backwards"
                    style={{ animationDelay: `${index * 50}ms` }}
                >
                    <Card className="group overflow-hidden transition-all hover:shadow-md dark:hover:border-neutral-700">
                        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                            <div className="flex items-center gap-3">
                                <div className={cn(
                                    "flex h-8 w-8 items-center justify-center rounded-full bg-neutral-100 dark:bg-neutral-800",
                                    activity.type === "COMMIT" && "text-blue-500 dark:text-blue-400",
                                    activity.type === "PULL_REQUEST" && "text-purple-500 dark:text-purple-400"
                                )}>
                                    {activity.type === "COMMIT" ? <GitCommit className="h-4 w-4" /> : <GitPullRequest className="h-4 w-4" />}
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <CardTitle className="text-base font-medium leading-none">
                                            {activity.title}
                                        </CardTitle>
                                        {activity.business_update && (
                                            <Badge variant={getImpactBadgeVariant(activity.business_update.impact_level)} className="h-5 px-1.5 font-normal">
                                                {getImpactIcon(activity.business_update.impact_level)}
                                                {activity.business_update.impact_level}
                                            </Badge>
                                        )}
                                    </div>
                                    <div className="mt-1 flex items-center gap-2 text-xs text-secondary">
                                        <span>{activity.author}</span>
                                        <span>•</span>
                                        <span>
                                            {activity.occurred_at
                                                ? format(new Date(activity.occurred_at), "d 'de' MMM, HH:mm", { locale: ptBR })
                                                : format(new Date(activity.created_at), "d 'de' MMM", { locale: ptBR })
                                            }
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {activity.business_update ? (
                                <div className="rounded-md bg-neutral-50 p-3 text-sm text-neutral-600 dark:bg-neutral-800/50 dark:text-neutral-300">
                                    {activity.business_update.summary}
                                </div>
                            ) : (
                                <p className="text-sm italic text-secondary">Aguardando análise de negócio...</p>
                            )}

                            {activity.business_update?.category && (
                                <div className="mt-3">
                                    <Badge variant="outline" className="text-[10px] text-secondary">
                                        {activity.business_update.category}
                                    </Badge>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            ))}
        </div>
    );
}
