"use client";

import { useState } from "react";
import { Settings, Database, Users } from "lucide-react";
import Link from "next/link";
import { TeamsManager } from "@/components/teams";

type Tab = "teams" | "integrations";

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<Tab>("teams");

    return (
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
            {/* Header */}
            <header className="border-b border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
                <div className="container mx-auto max-w-6xl px-4 py-6">
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                            <Settings className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-neutral-900 dark:text-white">
                                Configurações
                            </h1>
                            <p className="text-sm text-neutral-500">
                                Gerencie times, integrações e fontes de dados
                            </p>
                        </div>
                    </div>

                    {/* Tabs */}
                    <nav className="mt-6 flex gap-1">
                        <button
                            onClick={() => setActiveTab("teams")}
                            className={`
                                flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors
                                ${activeTab === "teams"
                                    ? "bg-primary text-white"
                                    : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800"
                                }
                            `}
                        >
                            <Users className="h-4 w-4" />
                            Times
                        </button>
                        <Link
                            href="/settings/data-sources"
                            className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-neutral-600 transition-colors hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800"
                        >
                            <Database className="h-4 w-4" />
                            Fontes de Dados
                        </Link>
                    </nav>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto max-w-6xl px-4 py-8">
                {activeTab === "teams" && <TeamsManager />}
            </main>
        </div>
    );
}
