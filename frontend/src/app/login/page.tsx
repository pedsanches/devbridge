"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, ArrowRight, Loader2, CheckCircle } from "lucide-react";
import { requestMagicLink } from "@/services/api";


export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSent, setIsSent] = useState(false);
    const [error, setError] = useState("");
    // const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            await requestMagicLink(email);
            setIsSent(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to send magic link");
        } finally {
            setIsLoading(false);
        }
    };

    if (isSent) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 dark:bg-neutral-900">

                <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg dark:bg-neutral-800">
                    <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                        <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
                    </div>
                    <h1 className="mb-2 text-2xl font-bold text-neutral-900 dark:text-white">
                        Confira seu email
                    </h1>
                    <p className="mb-6 text-neutral-600 dark:text-neutral-400">
                        Enviamos um link mágico para <strong>{email}</strong>.
                        Clique no link para acessar sua conta.
                    </p>
                    <button
                        onClick={() => setIsSent(false)}
                        className="text-primary hover:underline"
                    >
                        Usar outro email
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 dark:bg-neutral-900">

            <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg dark:bg-neutral-800">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                    <Mail className="h-8 w-8 text-primary" />
                </div>
                <h1 className="mb-2 text-2xl font-bold text-neutral-900 dark:text-white">
                    Bem-vindo ao DevBridge
                </h1>
                <p className="mb-6 text-neutral-600 dark:text-neutral-400">
                    Digite seu email para receber um link de acesso.
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="email" className="mb-2 block text-sm font-medium text-neutral-700 dark:text-neutral-300">
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="seu@email.com"
                            required
                            className="w-full rounded-lg border border-neutral-200 bg-white px-4 py-3 text-neutral-900 placeholder:text-neutral-400 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 dark:border-neutral-700 dark:bg-neutral-900 dark:text-white"
                        />
                    </div>

                    {error && (
                        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading || !email}
                        className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 font-medium text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {isLoading ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                            <>
                                Continuar
                                <ArrowRight className="h-5 w-5" />
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
