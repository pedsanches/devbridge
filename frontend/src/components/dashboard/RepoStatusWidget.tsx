import { GitBranch } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useRepos } from "@/hooks/use-repos";

export function RepoStatusWidget() {
    const { repos, isLoading, error } = useRepos();

    if (isLoading) return <div className="h-32 animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-800" />;

    // Fallback if no repos or error
    if (error || repos.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Repositórios</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-secondary">Nenhum repositório conectado.</p>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card>
            <CardHeader className="pb-3">
                <CardTitle className="text-lg">Repositórios Ativos</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
                {repos.map((repo) => (
                    <div key={repo.id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
                                <GitBranch className="h-4 w-4" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-sm font-medium">{repo.name}</span>
                                <span className="text-[10px] text-secondary">{repo.owner}</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {repo.last_synced_at ? (
                                <div className="flex items-center gap-1.5 text-[10px] text-green-600 dark:text-green-500">
                                    <span className="relative flex h-2 w-2">
                                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
                                        <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500"></span>
                                    </span>
                                    Sync
                                </div>
                            ) : (
                                <Badge variant="secondary" className="text-[10px]">Pendente</Badge>
                            )}
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}
