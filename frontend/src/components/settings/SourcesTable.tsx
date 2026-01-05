"use client";

import { Database, ExternalLink, RefreshCw, CheckCircle, Clock, AlertTriangle } from "lucide-react";
import { DataSource } from "@/services/api";

interface SourcesTableProps {
    sources: DataSource[];
    onSync: (sourceId: string) => void;
    isSyncing?: string | null;
}

const statusConfig = {
    indexed: { icon: CheckCircle, color: "text-green-500", label: "Indexado" },
    indexing: { icon: RefreshCw, color: "text-blue-500 animate-spin", label: "Indexando..." },
    pending: { icon: Clock, color: "text-neutral-400", label: "Pendente" },
    error: { icon: AlertTriangle, color: "text-red-500", label: "Erro" },
};

export function SourcesTable({ sources, onSync, isSyncing }: SourcesTableProps) {
    if (sources.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-neutral-300 bg-neutral-50 py-12 text-center dark:border-neutral-700 dark:bg-neutral-900">
                <Database className="mb-3 h-10 w-10 text-neutral-400" />
                <h3 className="font-medium text-neutral-700 dark:text-neutral-300">Nenhuma fonte conectada</h3>
                <p className="mt-1 text-sm text-neutral-500">
                    Conecte o GitHub para sincronizar seus repositórios
                </p>
            </div>
        );
    }

    return (
        <div className="overflow-hidden rounded-xl border border-neutral-200 dark:border-neutral-800">
            <table className="w-full">
                <thead className="bg-neutral-50 dark:bg-neutral-900">
                    <tr className="text-left text-xs font-medium uppercase tracking-wider text-neutral-500">
                        <th className="px-4 py-3">Repositório</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Atividades</th>
                        <th className="px-4 py-3 text-right">Ações</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 bg-white dark:divide-neutral-800 dark:bg-neutral-950">
                    {sources.map((source) => {
                        const { icon: StatusIcon, color, label } = statusConfig[source.indexing_status];
                        const isCurrentSyncing = isSyncing === source.id;

                        return (
                            <tr key={source.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-900">
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium text-neutral-900 dark:text-white">
                                            {source.name}
                                        </span>
                                        <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-neutral-400 hover:text-primary"
                                        >
                                            <ExternalLink className="h-3.5 w-3.5" />
                                        </a>
                                    </div>
                                    {source.last_synced_at && (
                                        <p className="text-xs text-neutral-500">
                                            Último sync: {new Date(source.last_synced_at).toLocaleDateString("pt-BR")}
                                        </p>
                                    )}
                                </td>
                                <td className="px-4 py-3">
                                    <div className={`flex items-center gap-1.5 text-sm ${color}`}>
                                        <StatusIcon className="h-4 w-4" />
                                        <span>{label}</span>
                                    </div>
                                    {source.vectors_count > 0 && (
                                        <p className="text-xs text-neutral-500">{source.vectors_count} vectors</p>
                                    )}
                                </td>
                                <td className="px-4 py-3 text-sm text-neutral-600 dark:text-neutral-400">
                                    {source.activities_count} atividades
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <button
                                        onClick={() => onSync(source.id)}
                                        disabled={isCurrentSyncing}
                                        className="inline-flex items-center gap-1 rounded-lg border border-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 transition-colors hover:bg-neutral-100 disabled:opacity-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                                    >
                                        <RefreshCw className={`h-3.5 w-3.5 ${isCurrentSyncing ? "animate-spin" : ""}`} />
                                        Sync
                                    </button>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
