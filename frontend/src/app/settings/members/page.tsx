"use client";

import { Users } from "lucide-react";
import { MembersCard } from "@/components/settings/MembersCard";

export default function MembersPage() {
    return (
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
            {/* Header */}
            <header className="border-b border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
                <div className="container mx-auto max-w-5xl px-4 py-6">
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                            <Users className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-neutral-900 dark:text-white">
                                Membros
                            </h1>
                            <p className="text-sm text-neutral-500">
                                Gerencie os membros e convites da sua organização
                            </p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="container mx-auto max-w-5xl px-4 py-8">
                <MembersCard />
            </main>
        </div>
    );
}
