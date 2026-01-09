"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

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
        id: "chat-intro",
        targetSelector: "[data-onboarding='novo-chat']",
        title: "💬 Chat com IA",
        description: "Este é seu assistente inteligente. Pergunte sobre seus projetos, commits, PRs e mais.",
        position: "right",
    },
    {
        id: "metrics-intro",
        targetSelector: "[data-onboarding='metrics']",
        title: "📊 Métricas DORA",
        description: "Acompanhe a saúde do seu time com métricas de engenharia em tempo real.",
        position: "bottom",
    },
    {
        id: "reports-intro",
        targetSelector: "[data-onboarding='reports']",
        title: "📄 Relatórios",
        description: "Gere relatórios personalizados para diferentes stakeholders.",
        position: "right",
    },
];

interface OnboardingProviderProps {
    children: ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
    const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
    const [currentStepIndex, setCurrentStepIndex] = useState(-1);
    const [isOnboardingActive, setIsOnboardingActive] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);

    // Load completed steps from localStorage
    useEffect(() => {
        if (typeof window === "undefined") return;

        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                setCompletedSteps(new Set(parsed.completedSteps || []));
                if (parsed.skipped) {
                    setIsOnboardingActive(false);
                }
            }
        } catch (e) {
            console.error("Error loading onboarding state:", e);
        }
        setIsInitialized(true);
    }, []);

    // Save to localStorage when completedSteps changes
    useEffect(() => {
        if (!isInitialized || typeof window === "undefined") return;

        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                completedSteps: Array.from(completedSteps),
                skipped: !isOnboardingActive && completedSteps.size === 0,
            }));
        } catch (e) {
            console.error("Error saving onboarding state:", e);
        }
    }, [completedSteps, isOnboardingActive, isInitialized]);

    // Check if all steps are completed
    const allStepsCompleted = ONBOARDING_STEPS.every(step =>
        completedSteps.has(step.id)
    );

    // Auto-start onboarding for new users
    useEffect(() => {
        if (!isInitialized) return;
        if (completedSteps.size === 0 && !allStepsCompleted) {
            // This is a new user, could auto-start onboarding
            // For now, we'll let them start manually or via welcome modal
        }
    }, [isInitialized, completedSteps, allStepsCompleted]);

    const currentStep = isOnboardingActive && currentStepIndex >= 0 && currentStepIndex < ONBOARDING_STEPS.length
        ? ONBOARDING_STEPS[currentStepIndex]
        : null;

    const startOnboarding = () => {
        setCurrentStepIndex(0);
        setIsOnboardingActive(true);
    };

    const completeStep = (stepId: string) => {
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
    };

    const skipOnboarding = () => {
        setIsOnboardingActive(false);
        setCurrentStepIndex(-1);
    };

    const isStepCompleted = (stepId: string) => completedSteps.has(stepId);

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
