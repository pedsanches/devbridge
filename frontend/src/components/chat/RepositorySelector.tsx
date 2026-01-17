"use client";

import { Check, ChevronDown, Database } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { getDataSources, DataSource } from "@/services/api";

interface RepositorySelectorProps {
    selectedRepos: string[];
    onChange: (repos: string[]) => void;
    disabled?: boolean;
}

export function RepositorySelector({ selectedRepos, onChange, disabled }: RepositorySelectorProps) {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div className="relative" ref={containerRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                disabled={disabled}
                className={`flex items-center gap-1.5 rounded-md border text-xs font-medium transition-all px-3 py-1.5
                    ${selectedRepos.length > 0
                        ? "border-primary/20 bg-primary/5 text-primary hover:bg-primary/10 dark:bg-primary/10 dark:text-primary dark:border-primary/30"
                        : "border-neutral-200 bg-white text-neutral-500 hover:bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-800 dark:hover:bg-neutral-700"
                    }
                    disabled:opacity-50`}
            >
                <Database className="h-3.5 w-3.5" />
                {selectedRepos.length === 0 ? "Todas as fontes" : `${selectedRepos.length} fonte${selectedRepos.length > 1 ? 's' : ''}`}
                <ChevronDown className="h-3 w-3 opacity-50" />
            </button>

            {isOpen && (
                <div className="absolute bottom-full left-0 mb-2 w-72 rounded-lg border border-neutral-200 bg-white shadow-xl ring-1 ring-black/5 dark:border-neutral-700 dark:bg-neutral-900 dark:ring-white/10 z-50">
                    <RepositorySelectorContent selectedRepos={selectedRepos} onChange={onChange} />
                </div>
            )}
        </div>
    );
}

export function RepositorySelectorContent({ selectedRepos, onChange }: Omit<RepositorySelectorProps, "disabled">) {
    const [repos, setRepos] = useState<DataSource[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const load = async () => {
            setIsLoading(true);
            try {
                const data = await getDataSources();
                setRepos(data.sources.filter(s => s.is_active && s.activities_count > 0));
            } catch (e) {
                console.error("Failed to load sources", e);
            } finally {
                setIsLoading(false);
            }
        };
        load();
    }, []);

    const toggleRepo = (repoName: string) => {
        if (selectedRepos.includes(repoName)) {
            onChange(selectedRepos.filter(r => r !== repoName));
        } else {
            onChange([...selectedRepos, repoName]);
        }
    };

    return (
        <div className="p-3">
            <div className="mb-2 flex items-center justify-between px-1">
                <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                    Repositórios ({repos.length})
                </span>
                {selectedRepos.length > 0 && (
                    <button
                        onClick={() => onChange([])}
                        className="text-xs text-primary hover:underline"
                    >
                        Limpar
                    </button>
                )}
            </div>

            <div className="max-h-60 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                {isLoading ? (
                    <div className="px-2 py-4 text-center text-xs text-neutral-400">Carregando...</div>
                ) : repos.length === 0 ? (
                    <div className="px-2 py-4 text-center">
                        <p className="text-xs text-neutral-400 mb-2">Nenhum repositório conectado. Conecte o GitHub nas configurações.</p>
                        <a href="/settings" className="text-xs text-primary hover:underline">
                            Ir para Configurações →
                        </a>
                    </div>
                ) : (
                    repos.map(repo => (
                        <button
                            key={repo.id}
                            onClick={() => toggleRepo(repo.name)}
                            type="button"
                            className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm transition-colors
                                ${selectedRepos.includes(repo.name)
                                    ? "bg-primary/10 text-primary dark:bg-primary/20"
                                    : "hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300"
                                }`}
                        >
                            <span className="truncate pr-2" title={repo.name}>
                                {repo.name}
                            </span>
                            {selectedRepos.includes(repo.name) && (
                                <Check className="h-4 w-4 shrink-0" />
                            )}
                        </button>
                    ))
                )}
            </div>
        </div>
    );
}
