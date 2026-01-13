"use client";

import { useEffect, useState, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { verifyMagicLink } from "@/services/api";
import { useAuth } from "@/hooks/use-auth";


function VerifyContent() {
    const searchParams = useSearchParams();
    const token = searchParams.get("token");

    // Derive initial status from token presence
    const [status, setStatus] = useState<"loading" | "success" | "error">(
        token ? "loading" : "error"
    );
    const [error, setError] = useState(token ? "" : "Token não encontrado");
    const hasStartedRef = useRef(false);
    const router = useRouter();
    const { refreshUser } = useAuth();

    useEffect(() => {
        // Skip if no token or already started (use ref to avoid triggering lint)
        if (!token || hasStartedRef.current) return;

        hasStartedRef.current = true;

        const verify = async () => {
            try {
                await verifyMagicLink(token);
                await refreshUser(); // Update auth context
                setStatus("success");
                // Redirect to dashboard after brief success message
                setTimeout(() => {
                    router.push("/dashboard");
                }, 1500);
            } catch (err) {
                setStatus("error");
                setError(err instanceof Error ? err.message : "Falha na verificação");
            }
        };

        verify();
    }, [token, router, refreshUser]);

    return (
        <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-lg dark:bg-neutral-800">
            {status === "loading" && (
                <>
                    <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-primary" />
                    <h1 className="text-xl font-bold text-neutral-900 dark:text-white">
                        Verificando...
                    </h1>
                </>
            )}

            {status === "success" && (
                <>
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                        <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
                    </div>
                    <h1 className="mb-2 text-xl font-bold text-neutral-900 dark:text-white">
                        Login realizado!
                    </h1>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Redirecionando...
                    </p>
                </>
            )}

            {status === "error" && (
                <>
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900">
                        <XCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
                    </div>
                    <h1 className="mb-2 text-xl font-bold text-neutral-900 dark:text-white">
                        Erro na verificação
                    </h1>
                    <p className="mb-4 text-neutral-600 dark:text-neutral-400">
                        {error}
                    </p>
                    <button
                        onClick={() => router.push("/login")}
                        className="rounded-lg bg-primary px-4 py-2 font-medium text-white hover:bg-primary-hover"
                    >
                        Tentar novamente
                    </button>
                </>
            )}
        </div>
    );
}

function LoadingFallback() {
    return (
        <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-lg dark:bg-neutral-800">
            <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-primary" />
            <h1 className="text-xl font-bold text-neutral-900 dark:text-white">
                Carregando...
            </h1>
        </div>
    );
}

export default function VerifyPage() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 dark:bg-neutral-900">
            <Suspense fallback={<LoadingFallback />}>
                <VerifyContent />
            </Suspense>
        </div>
    );
}
