"use client";

import { useState, useSyncExternalStore } from "react";
import { X, Github, Users, MessageSquare, CheckCircle } from "lucide-react";
import { useOnboarding } from "./OnboardingProvider";

interface WelcomeModalProps {
    isGitHubConnected?: boolean;
    hasTeams?: boolean;
}

const STORAGE_KEY = "devbridge_welcome_shown";

// Helper functions for useSyncExternalStore
function subscribe(callback: () => void) {
    window.addEventListener("storage", callback);
    return () => window.removeEventListener("storage", callback);
}

function getSnapshot(): boolean {
    if (typeof window === "undefined") return true;
    return localStorage.getItem(STORAGE_KEY) === "true";
}

function getServerSnapshot(): boolean {
    return true; // Assume shown on server to prevent flash
}

export function WelcomeModal({ isGitHubConnected = false, hasTeams = false }: WelcomeModalProps) {
    const hasShownBefore = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

    // Only use local state for controlling visibility after user interaction
    const [dismissed, setDismissed] = useState(false);
    const { startOnboarding, isStepCompleted } = useOnboarding();

    // Determine if modal should be open based on external state
    const isOpen = !hasShownBefore && !isGitHubConnected && !dismissed;

    const handleClose = () => {
        setDismissed(true);
        if (typeof window !== "undefined") {
            localStorage.setItem(STORAGE_KEY, "true");
        }
    };

    const handleStartSetup = () => {
        handleClose();
        startOnboarding();
    };

    if (!isOpen) return null;

    const steps = [
        {
            icon: Github,
            title: "Conectar GitHub",
            description: "Importe seus repositórios automaticamente",
            completed: isGitHubConnected,
            action: "/settings/data-sources",
        },
        {
            icon: Users,
            title: "Organizar Times",
            description: "Agrupe repositórios por squad ou projeto",
            completed: hasTeams,
            action: "/settings",
        },
        {
            icon: MessageSquare,
            title: "Conversar com IA",
            description: "Pergunte sobre seu código e projetos",
            completed: isStepCompleted("chat-intro"),
        },
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="relative mx-4 w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-neutral-900">
                {/* Close button */}
                <button
                    onClick={handleClose}
                    className="absolute right-4 top-4 p-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
                >
                    <X className="h-5 w-5" />
                </button>

                {/* Header */}
                <div className="mb-6 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary to-purple-600">
                        <span className="text-3xl">🚀</span>
                    </div>
                    <h2 className="text-2xl font-bold text-neutral-900 dark:text-white">
                        Bem-vindo ao DevBridge!
                    </h2>
                    <p className="mt-2 text-neutral-600 dark:text-neutral-400">
                        Transforme trabalho técnico em impacto de negócio
                    </p>
                </div>

                {/* Steps */}
                <div className="mb-6 space-y-3">
                    {steps.map((step, index) => (
                        <div
                            key={index}
                            className={`flex items-center gap-4 rounded-xl border p-4 transition-colors ${step.completed
                                ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20"
                                : "border-neutral-200 dark:border-neutral-700"
                                }`}
                        >
                            <div
                                className={`flex h-10 w-10 items-center justify-center rounded-full ${step.completed
                                    ? "bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400"
                                    : "bg-neutral-100 text-neutral-500 dark:bg-neutral-800"
                                    }`}
                            >
                                {step.completed ? (
                                    <CheckCircle className="h-5 w-5" />
                                ) : (
                                    <step.icon className="h-5 w-5" />
                                )}
                            </div>
                            <div className="flex-1">
                                <div className="font-medium text-neutral-900 dark:text-white">
                                    {step.title}
                                </div>
                                <div className="text-sm text-neutral-500">
                                    {step.description}
                                </div>
                            </div>
                            {step.completed && (
                                <span className="text-xs font-medium text-green-600 dark:text-green-400">
                                    ✓ Concluído
                                </span>
                            )}
                        </div>
                    ))}
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                    <button
                        onClick={handleClose}
                        className="flex-1 rounded-xl border border-neutral-200 px-4 py-3 font-medium text-neutral-700 transition-colors hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                    >
                        Explorar sozinho
                    </button>
                    <button
                        onClick={handleStartSetup}
                        className="flex-1 rounded-xl bg-primary px-4 py-3 font-medium text-white transition-colors hover:bg-primary/90"
                    >
                        Começar configuração
                    </button>
                </div>
            </div>
        </div>
    );
}
