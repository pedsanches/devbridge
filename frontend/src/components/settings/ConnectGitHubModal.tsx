"use client";

import { useState } from "react";
import { Key, Eye, EyeOff, Loader2 } from "lucide-react";

interface ConnectGitHubModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConnect: (token: string) => Promise<void>;
}

export function ConnectGitHubModal({ isOpen, onClose, onConnect }: ConnectGitHubModalProps) {
    const [token, setToken] = useState("");
    const [showToken, setShowToken] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await onConnect(token);
            setToken("");
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao conectar");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-neutral-900">
                <div className="mb-4 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-neutral-100 dark:bg-neutral-800">
                        <Key className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                            Conectar GitHub
                        </h2>
                        <p className="text-sm text-neutral-500">
                            Use um Personal Access Token (PAT)
                        </p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="mb-1.5 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
                            GitHub Token
                        </label>
                        <div className="relative">
                            <input
                                type={showToken ? "text" : "password"}
                                value={token}
                                onChange={(e) => setToken(e.target.value)}
                                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                                className="w-full rounded-lg border border-neutral-300 bg-white px-4 py-2.5 pr-10 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
                                required
                                minLength={10}
                            />
                            <button
                                type="button"
                                onClick={() => setShowToken(!showToken)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
                            >
                                {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                        </div>
                        <p className="mt-1.5 text-xs text-neutral-500">
                            Crie um token com permissão <code className="rounded bg-neutral-100 px-1 dark:bg-neutral-800">repo</code> em{" "}
                            <a
                                href="https://github.com/settings/tokens/new"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline"
                            >
                                github.com/settings/tokens
                            </a>
                        </p>
                    </div>

                    {error && (
                        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
                            {error}
                        </div>
                    )}

                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={isLoading}
                            className="flex-1 rounded-lg border border-neutral-200 px-4 py-2.5 font-medium text-neutral-700 transition-colors hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || token.length < 10}
                            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 font-medium text-white transition-colors hover:bg-primary-hover disabled:opacity-50"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Conectando...
                                </>
                            ) : (
                                "Conectar"
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
