import { GitBranch, RefreshCw, Plus } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { enUS } from "date-fns/locale";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useRepos } from "@/hooks/use-repos";

export function RepoStatusWidget() {
    const { repos, isLoading, error } = useRepos();

    if (isLoading) return <div className="h-32 animate-pulse rounded-xl bg-[var(--muted)]" />;

    // Fallback if no repos or error
    if (error || repos.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Repositories</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p className="text-sm text-secondary">No repositories connected.</p>
                    <Button asChild variant="outline" size="sm" className="w-full">
                        <Link href="/settings">
                            <Plus className="mr-2 h-4 w-4" />
                            Connect Repository
                        </Link>
                    </Button>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className="flex h-full max-h-[calc(100vh-8rem)] flex-col overflow-hidden">
            <CardHeader className="pb-3">
                <CardTitle className="text-lg">Active Repositories</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto pr-2">
                <div className="space-y-4">
                    {repos.map((repo) => (
                        <div key={repo.id} className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--muted)] text-[var(--muted-foreground)]">
                                    <GitBranch className="h-4 w-4" />
                                </div>
                                <div className="flex min-w-0 flex-col">
                                    <span className="truncate text-sm font-medium" title={repo.name}>{repo.name}</span>
                                    <span className="truncate text-[10px] text-secondary">{repo.owner}</span>
                                </div>
                            </div>
                            <div className="shrink-0">
                                {repo.last_synced_at ? (
                                    <div className="flex flex-col items-end gap-0.5">
                                        <div className="flex items-center gap-1.5 text-[10px] text-green-600 dark:text-green-500">
                                            <span className="relative flex h-1.5 w-1.5">
                                                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
                                                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-green-500"></span>
                                            </span>
                                            Synced
                                        </div>
                                        <span className="text-[10px] text-[var(--muted-foreground)]">
                                            {formatDistanceToNow(new Date(repo.last_synced_at), { addSuffix: true, locale: enUS })}
                                        </span>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-1.5">
                                        <RefreshCw className="h-3 w-3 animate-spin text-[var(--muted-foreground)]" />
                                        <span className="text-[10px] text-[var(--muted-foreground)]">Syncing...</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
