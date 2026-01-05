"use client";

import { Github, Link2, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { IntegrationStatus, GitHubIntegration } from "@/services/api";

interface IntegrationCardProps {
    integration: GitHubIntegration;
    onConnect: () => void;
    onDisconnect: () => void;
    isLoading?: boolean;
}

const statusConfig: Record<IntegrationStatus, { icon: React.ElementType; color: string; label: string }> = {
    connected: { icon: CheckCircle, color: "text-green-500", label: "Conectado" },
    disconnected: { icon: XCircle, color: "text-neutral-400", label: "Desconectado" },
    error: { icon: XCircle, color: "text-red-500", label: "Erro" },
};

export function IntegrationCard({ integration, onConnect, onDisconnect, isLoading }: IntegrationCardProps) {
    const { icon: StatusIcon, color, label } = statusConfig[integration.status];
    const isConnected = integration.status === "connected";

    return (
        <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-neutral-900 dark:bg-white">
                        <Github className="h-6 w-6 text-white dark:text-neutral-900" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-neutral-900 dark:text-white">GitHub</h3>
                        <div className={`flex items-center gap-1.5 text-sm ${color}`}>
                            <StatusIcon className="h-4 w-4" />
                            <span>{label}</span>
                        </div>
                    </div>
                </div>

                <button
                    onClick={isConnected ? onDisconnect : onConnect}
                    disabled={isLoading}
                    className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${isConnected
                            ? "border border-red-200 text-red-600 hover:bg-red-50 dark:border-red-900 dark:hover:bg-red-950"
                            : "bg-neutral-900 text-white hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-100"
                        } disabled:opacity-50`}
                >
                    {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : isConnected ? (
                        "Desconectar"
                    ) : (
                        "Conectar"
                    )}
                </button>
            </div>

            {isConnected && (
                <div className="mt-4 flex items-center gap-4 border-t border-neutral-100 pt-4 text-sm text-neutral-500 dark:border-neutral-800">
                    {integration.organization_name && (
                        <div className="flex items-center gap-1">
                            <Link2 className="h-3.5 w-3.5" />
                            <span>{integration.organization_name}</span>
                        </div>
                    )}
                    <div>{integration.repositories_count} repositórios</div>
                </div>
            )}
        </div>
    );
}
