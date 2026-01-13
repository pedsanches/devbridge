"use client";

import { useEffect, useState, useRef, useCallback, useSyncExternalStore } from "react";
import { X, ArrowRight, SkipForward } from "lucide-react";
import { useOnboarding } from "./OnboardingProvider";

interface TooltipPosition {
    top: number;
    left: number;
    arrowPosition: "top" | "bottom" | "left" | "right";
}

// Custom hook to subscribe to window resize
function useWindowSize() {
    const subscribe = useCallback((callback: () => void) => {
        window.addEventListener("resize", callback);
        return () => window.removeEventListener("resize", callback);
    }, []);

    const getSnapshot = useCallback(() => {
        return `${window.innerWidth}x${window.innerHeight}`;
    }, []);

    const getServerSnapshot = useCallback(() => "0x0", []);

    return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

export function OnboardingTooltip() {
    const { currentStep, completeStep, skipOnboarding, isOnboardingActive } = useOnboarding();
    const tooltipRef = useRef<HTMLDivElement>(null);
    const [position, setPosition] = useState<TooltipPosition | null>(null);
    const windowSize = useWindowSize();

    const calculatePosition = useCallback(() => {
        if (!currentStep || !tooltipRef.current) {
            return null;
        }

        const target = document.querySelector(currentStep.targetSelector);
        if (!target) return null;

        const targetRect = target.getBoundingClientRect();
        const tooltipRect = tooltipRef.current.getBoundingClientRect();
        const padding = 12;

        let top = 0;
        let left = 0;
        let arrowPosition: "top" | "bottom" | "left" | "right" = "top";

        switch (currentStep.position || "bottom") {
            case "top":
                top = targetRect.top - tooltipRect.height - padding;
                left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
                arrowPosition = "bottom";
                break;
            case "bottom":
                top = targetRect.bottom + padding;
                left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
                arrowPosition = "top";
                break;
            case "left":
                top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
                left = targetRect.left - tooltipRect.width - padding;
                arrowPosition = "right";
                break;
            case "right":
                top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
                left = targetRect.right + padding;
                arrowPosition = "left";
                break;
        }

        // Keep tooltip within viewport
        const viewportPadding = 16;
        left = Math.max(viewportPadding, Math.min(left, window.innerWidth - tooltipRect.width - viewportPadding));
        top = Math.max(viewportPadding, Math.min(top, window.innerHeight - tooltipRect.height - viewportPadding));

        return { top, left, arrowPosition };
    }, [currentStep]);

    // This effect syncs with external DOM state, which is allowed
    useEffect(() => {
        if (!currentStep || !isOnboardingActive) {
            if (position !== null) {
                setPosition(null);
            }
            return;
        }

        // Delay to ensure tooltip is rendered
        const timeoutId = setTimeout(() => {
            const newPosition = calculatePosition();
            if (newPosition) {
                setPosition(newPosition);
                // Highlight target element
                const target = document.querySelector(currentStep.targetSelector);
                target?.classList.add("onboarding-highlight");
            }
        }, 100);

        return () => {
            clearTimeout(timeoutId);
            // Remove highlight from previous target
            const target = document.querySelector(currentStep.targetSelector);
            target?.classList.remove("onboarding-highlight");
        };
        // position is intentionally not in deps to avoid infinite loop
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentStep, isOnboardingActive, calculatePosition]);

    // Recalculate on window resize
    useEffect(() => {
        if (currentStep && isOnboardingActive) {
            const newPosition = calculatePosition();
            if (newPosition) {
                setPosition(newPosition);
            }
        }
        // Only recalculate when window size changes
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [windowSize]);

    if (!currentStep || !isOnboardingActive) return null;

    const handleNext = () => {
        completeStep(currentStep.id);
    };

    const handleSkip = () => {
        skipOnboarding();
    };

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 z-[100] bg-black/20 backdrop-blur-[1px]"
                onClick={handleSkip}
            />

            {/* Tooltip */}
            <div
                ref={tooltipRef}
                className="fixed z-[101] w-80 rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 shadow-xl"
                style={{
                    top: position?.top ?? -9999,
                    left: position?.left ?? -9999,
                    opacity: position ? 1 : 0,
                    transition: "opacity 0.2s, top 0.3s, left 0.3s",
                }}
            >
                {/* Arrow */}
                <div
                    className={`
                        absolute h-3 w-3 rotate-45 border border-[var(--border)] bg-[var(--card)]
                        ${position?.arrowPosition === "top" ? "-top-1.5 left-1/2 -translate-x-1/2 border-r-0 border-b-0" : ""}
                        ${position?.arrowPosition === "bottom" ? "-bottom-1.5 left-1/2 -translate-x-1/2 border-l-0 border-t-0" : ""}
                        ${position?.arrowPosition === "left" ? "top-1/2 -left-1.5 -translate-y-1/2 border-t-0 border-r-0" : ""}
                        ${position?.arrowPosition === "right" ? "top-1/2 -right-1.5 -translate-y-1/2 border-b-0 border-l-0" : ""}
                    `}
                />

                {/* Close button */}
                <button
                    onClick={handleSkip}
                    className="absolute right-2 top-2 rounded-lg p-1 text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)] hover:text-[var(--foreground)]"
                    aria-label="Close"
                >
                    <X className="h-4 w-4" />
                </button>

                {/* Content */}
                <h3 className="pr-6 text-sm font-semibold text-[var(--foreground)]">
                    {currentStep.title}
                </h3>
                <p className="mt-2 text-sm text-[var(--muted-foreground)]">
                    {currentStep.description}
                </p>

                {/* Actions */}
                <div className="mt-4 flex items-center justify-between">
                    <button
                        onClick={handleSkip}
                        className="flex items-center gap-1 text-xs text-[var(--muted-foreground)] transition-colors hover:text-[var(--foreground)]"
                    >
                        <SkipForward className="h-3 w-3" />
                        Pular tour
                    </button>
                    <button
                        onClick={handleNext}
                        className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)]"
                    >
                        Próximo
                        <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                </div>
            </div>
        </>
    );
}
