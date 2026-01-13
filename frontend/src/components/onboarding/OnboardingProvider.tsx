"use client";

import { createContext, useContext, useState, useEffect, ReactNode, useRef, useCallback } from "react";

interface OnboardingStep {
    id: string;
    targetSelector: string;
    title: string;
    description: string;
    position?: "top" | "bottom" | "left" | "right";
}

interface OnboardingContextType {
    currentStep: OnboardingStep | null;
    isOnboardingActive: boolean;
    completedSteps: Set<string>;
    startOnboarding: () => void;
    completeStep: (stepId: string) => void;
    skipOnboarding: () => void;
    isStepCompleted: (stepId: string) => boolean;
}

const OnboardingContext = createContext<OnboardingContextType | undefined>(undefined);

const STORAGE_KEY = "devbridge_onboarding";

// Define onboarding steps
const ONBOARDING_STEPS: OnboardingStep[] = [
    {
        id: "welcome",
        targetSelector: "[data-onboarding='dashboard']",
        title: "🎉 Bem-vindo ao DevBridge!",
        description: "Vamos configurar sua conta em poucos passos para você começar a usar.",
        position: "bottom",
    },
    {
        id: "github-connect",
        targetSelector: "[data-onboarding='data-sources']",
        title: "🔗 Conectar GitHub",
        description: "Primeiro, conecte sua conta GitHub para importar seus repositórios.",
        position: "right",
    },
    {
        id: "teams-setup",
        targetSelector: "[data-onboarding='settings']",
        title: "👥 Organize seus Times",
        description: "Agrupe repositórios em times para facilitar relatórios e análises.",
        position: "right",
    },
    {
        id: "chat-intro",
        targetSelector: "[data-onboarding='novo-chat']",
        title: "💬 Chat com IA",
        description: "Use o assistente para perguntar sobre seus projetos, commits e PRs.",
        position: "right",
    },
    {
        id: "metrics-intro",
        targetSelector: "[data-onboarding='metrics']",
        title: "📊 Métricas DORA",
        description: "Acompanhe a saúde do seu time com métricas de engenharia.",
        position: "bottom",
    },
    {
        id: "reports-intro",
        targetSelector: "[data-onboarding='reports']",
        title: "📄 Relatórios",
        description: "Gere relatórios personalizados para stakeholders.",
        position: "right",
    },
];

// Helper to load initial state from localStorage
function getInitialOnboardingState(): { completedSteps: Set<string>; skipped: boolean } {
    if (typeof window === "undefined") {
        return { completedSteps: new Set(), skipped: false };
    }
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            const parsed = JSON.parse(stored);
            return {
                completedSteps: new Set(parsed.completedSteps || []),
                skipped: parsed.skipped || false,
            };
        }
    } catch (e) {
        console.error("Error loading onboarding state:", e);
    }
    return { completedSteps: new Set(), skipped: false };
}

interface OnboardingProviderProps {
    children: ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
    // Use lazy initializer to avoid setState in useEffect
    const [completedSteps, setCompletedSteps] = useState<Set<string>>(() => {
        const initial = getInitialOnboardingState();
        return initial.completedSteps;
    });
    const [currentStepIndex, setCurrentStepIndex] = useState(-1);
    const [isOnboardingActive, setIsOnboardingActive] = useState(() => {
        const initial = getInitialOnboardingState();
        return !initial.skipped;
    });
    const isInitialized = useRef(false);

    // Mark as initialized after first render
    useEffect(() => {
        isInitialized.current = true;
    }, []);

    // Save to localStorage when completedSteps changes
    useEffect(() => {
        if (!isInitialized.current || typeof window === "undefined") return;

        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                completedSteps: Array.from(completedSteps),
                skipped: !isOnboardingActive && completedSteps.size === 0,
            }));
        } catch (e) {
            console.error("Error saving onboarding state:", e);
        }
    }, [completedSteps, isOnboardingActive]);


    const currentStep: OnboardingStep | null = isOnboardingActive && currentStepIndex >= 0 && currentStepIndex < ONBOARDING_STEPS.length
        ? ONBOARDING_STEPS[currentStepIndex] ?? null
        : null;

    const startOnboarding = useCallback(() => {
        setCurrentStepIndex(0);
        setIsOnboardingActive(true);
    }, []);

    const completeStep = useCallback((stepId: string) => {
        setCompletedSteps(prev => new Set([...prev, stepId]));

        // Move to next step
        const currentIndex = ONBOARDING_STEPS.findIndex(s => s.id === stepId);
        if (currentIndex >= 0 && currentIndex < ONBOARDING_STEPS.length - 1) {
            setCurrentStepIndex(currentIndex + 1);
        } else {
            // All steps completed
            setIsOnboardingActive(false);
            setCurrentStepIndex(-1);
        }
    }, []);

    const skipOnboarding = useCallback(() => {
        setIsOnboardingActive(false);
        setCurrentStepIndex(-1);
    }, []);

    const isStepCompleted = useCallback((stepId: string) => completedSteps.has(stepId), [completedSteps]);

    return (
        <OnboardingContext.Provider
            value={{
                currentStep,
                isOnboardingActive,
                completedSteps,
                startOnboarding,
                completeStep,
                skipOnboarding,
                isStepCompleted,
            }}
        >
            {children}
        </OnboardingContext.Provider>
    );
}

export function useOnboarding() {
    const context = useContext(OnboardingContext);
    if (context === undefined) {
        throw new Error("useOnboarding must be used within an OnboardingProvider");
    }
    return context;
}
