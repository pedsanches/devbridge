"use client";

import { useState, useEffect, useCallback } from "react";
import { Settings, Database, Zap } from "lucide-react";
import { IntegrationCard } from "@/components/settings/IntegrationCard";
import { SourcesTable } from "@/components/settings/SourcesTable";
import { ConnectGitHubModal } from "@/components/settings/ConnectGitHubModal";
import {
    getIntegrations,
    getDataSources,
    connectGitHub,
    disconnectGitHub,
    syncRepository,
    IntegrationsResponse,
    DataSourcesResponse,
} from "@/services/api";

export default function DataSourcesPage() {
    const [integrations, setIntegrations] = useState<IntegrationsResponse | null>(null);
    const [dataSources, setDataSources] = useState<DataSourcesResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isConnecting, setIsConnecting] = useState(false);
    const [showConnectModal, setShowConnectModal] = useState(false);
    const [syncingId, setSyncingId] = useState<string | null>(null);

    const loadData = useCallback(async () => {
        try {
            const [integrationsData, sourcesData] = await Promise.all([
                getIntegrations(),
                getDataSources(),
            ]);
            setIntegrations(integrationsData);
            setDataSources(sourcesData);
        } catch (error) {
            console.error("Failed to load data:", error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleConnect = async (token: string) => {
        setIsConnecting(true);
        try {
            await connectGitHub(token);
            await loadData();
        } finally {
            setIsConnecting(false);
        }
    };

    const handleDisconnect = async () => {
        setIsConnecting(true);
        try {
            await disconnectGitHub();
            await loadData();
        } finally {
            setIsConnecting(false);
        }
    };

    const handleSync = async (sourceId: string) => {
        setSyncingId(sourceId);
        try {
            const source = dataSources?.sources.find((s) => s.id === sourceId);
            if (source) {
                await syncRepository(source.name);
                await loadData();
            }
        } catch (error) {
            console.error("Sync failed:", error);
        } finally {
            setSyncingId(null);
        }
    };

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
            {/* Header */}
            <header className="border-b border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
                <div className="container mx-auto max-w-5xl px-4 py-6">
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                            <Settings className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-neutral-900 dark:text-white">
                                Data Sources
                            </h1>
                            <p className="text-sm text-neutral-500">
                                Gerencie as fontes de dados que alimentam a IA
                            </p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="container mx-auto max-w-5xl px-4 py-8">
                {/* Integrations Section */}
                <section className="mb-8">
                    <div className="mb-4 flex items-center gap-2">
                        <Zap className="h-4 w-4 text-primary" />
                        <h2 className="font-semibold text-neutral-800 dark:text-neutral-200">
                            Integrações
                        </h2>
                    </div>
                    <div className="grid gap-4 md:grid-cols-2">
                        {integrations && (
                            <IntegrationCard
                                integration={integrations.github}
                                onConnect={() => setShowConnectModal(true)}
                                onDisconnect={handleDisconnect}
                                isLoading={isConnecting}
                            />
                        )}
                        {/* Slack placeholder */}
                        <div className="flex items-center justify-center rounded-xl border-2 border-dashed border-neutral-200 bg-neutral-50 p-6 dark:border-neutral-700 dark:bg-neutral-900">
                            <div className="text-center text-neutral-400">
                                <p className="font-medium">Slack</p>
                                <p className="text-sm">Em breve</p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Data Sources Section */}
                <section>
                    <div className="mb-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Database className="h-4 w-4 text-primary" />
                            <h2 className="font-semibold text-neutral-800 dark:text-neutral-200">
                                Fontes Ativas
                            </h2>
                            {dataSources && (
                                <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
                                    {dataSources.total}
                                </span>
                            )}
                        </div>
                    </div>
                    {dataSources && (
                        <SourcesTable
                            sources={dataSources.sources}
                            onSync={handleSync}
                            isSyncing={syncingId}
                        />
                    )}
                </section>
            </main>

            {/* Connect Modal */}
            <ConnectGitHubModal
                isOpen={showConnectModal}
                onClose={() => setShowConnectModal(false)}
                onConnect={handleConnect}
            />
        </div>
    );
}
