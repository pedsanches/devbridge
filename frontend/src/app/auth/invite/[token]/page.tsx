"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { Loader2, CheckCircle, XCircle, Users, Building2 } from "lucide-react";
import { acceptInvitation } from "@/services/api";
import { useAuth } from "@/hooks/use-auth";

interface AcceptResult {
    organization_name: string;
    teams: string[];
}

export default function InviteAcceptPage() {
    const params = useParams();
    const token = params.token as string;

    const [status, setStatus] = useState<"loading" | "success" | "error">(
        token ? "loading" : "error"
    );
    const [error, setError] = useState(token ? "" : "Token não encontrado");
    const [result, setResult] = useState<AcceptResult | null>(null);
    const hasStartedRef = useRef(false);
    const router = useRouter();
    const { refreshUser } = useAuth();

    useEffect(() => {
        if (!token || hasStartedRef.current) return;

        hasStartedRef.current = true;

        const accept = async () => {
            try {
                const response = await acceptInvitation(token);
                await refreshUser();
                setResult({
                    organization_name: response.organization_name,
                    teams: response.teams,
                });
                setStatus("success");
                // Redirect to dashboard after brief success message
                setTimeout(() => {
                    router.push("/dashboard");
                }, 3000);
            } catch (err) {
                setStatus("error");
                setError(err instanceof Error ? err.message : "Falha ao aceitar convite");
            }
        };

        accept();
    }, [token, router, refreshUser]);

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 dark:bg-neutral-900">
            <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-lg dark:bg-neutral-800">
                {status === "loading" && (
                    <>
                        <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-primary" />
                        <h1 className="text-xl font-bold text-neutral-900 dark:text-white">
                            Aceitando convite...
                        </h1>
                        <p className="mt-2 text-neutral-600 dark:text-neutral-400">
                            Estamos configurando seu acesso.
                        </p>
                    </>
                )}

                {status === "success" && result && (
                    <>
                        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                            <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
                        </div>
                        <h1 className="mb-4 text-xl font-bold text-neutral-900 dark:text-white">
                            Bem-vindo(a)!
                        </h1>

                        <div className="mb-4 rounded-lg bg-neutral-50 p-4 dark:bg-neutral-700">
                            <div className="flex items-center justify-center gap-2 text-neutral-700 dark:text-neutral-300">
                                <Building2 className="h-5 w-5" />
                                <span className="font-medium">{result.organization_name}</span>
                            </div>

                            {result.teams.length > 0 && (
                                <div className="mt-3 flex items-center justify-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                                    <Users className="h-4 w-4" />
                                    <span>Times: {result.teams.join(", ")}</span>
                                </div>
                            )}
                        </div>

                        <p className="text-neutral-600 dark:text-neutral-400">
                            Redirecionando para o dashboard...
                        </p>
                    </>
                )}

                {status === "error" && (
                    <>
                        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900">
                            <XCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
                        </div>
                        <h1 className="mb-2 text-xl font-bold text-neutral-900 dark:text-white">
                            Erro no convite
                        </h1>
                        <p className="mb-4 text-neutral-600 dark:text-neutral-400">
                            {error}
                        </p>
                        <button
                            onClick={() => router.push("/login")}
                            className="rounded-lg bg-primary px-4 py-2 font-medium text-white hover:bg-primary-hover"
                        >
                            Ir para Login
                        </button>
                    </>
                )}
            </div>
        </div>
    );
}
