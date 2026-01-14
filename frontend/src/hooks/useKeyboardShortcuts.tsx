"use client";

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

interface KeyboardShortcutOptions {
    onFocusInput?: () => void;
    onToggleSidebar?: () => void;
    onClearInput?: () => void;
}

/**
 * Hook for managing keyboard shortcuts in the Chat interface.
 *
 * Shortcuts:
 * - ⌘/Ctrl + K: Focus chat input
 * - ⌘/Ctrl + N: New conversation
 * - ⌘/Ctrl + B: Toggle sidebar
 * - Escape: Clear input / Close modals
 */
export function useKeyboardShortcuts(options: KeyboardShortcutOptions = {}) {
    const router = useRouter();
    const { onFocusInput, onToggleSidebar, onClearInput } = options;

    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            const isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
            const modKey = isMac ? event.metaKey : event.ctrlKey;

            // Ignore if typing in an input/textarea (except for Escape)
            const target = event.target as HTMLElement;
            const isTyping =
                target.tagName === "INPUT" ||
                target.tagName === "TEXTAREA" ||
                target.isContentEditable;

            // ⌘/Ctrl + K: Focus chat input
            if (modKey && event.key === "k") {
                event.preventDefault();
                onFocusInput?.();
            }

            // ⌘/Ctrl + N: New conversation
            if (modKey && event.key === "n") {
                event.preventDefault();
                router.push("/chat");
            }

            // ⌘/Ctrl + B: Toggle sidebar
            if (modKey && event.key === "b") {
                event.preventDefault();
                onToggleSidebar?.();
            }

            // Escape: Clear input or close modals
            if (event.key === "Escape") {
                if (isTyping) {
                    onClearInput?.();
                }
            }
        },
        [router, onFocusInput, onToggleSidebar, onClearInput]
    );

    useEffect(() => {
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [handleKeyDown]);
}

/**
 * Component to display keyboard shortcuts hint.
 */
export function KeyboardShortcutsHint() {
    const isMac = typeof navigator !== "undefined" && navigator.platform.toUpperCase().indexOf("MAC") >= 0;
    const modKeySymbol = isMac ? "⌘" : "Ctrl";

    return (
        <span className= "flex items-center gap-3 text-[10px] text-neutral-400 dark:text-neutral-500" >
        <span>
        <span className="rounded bg-neutral-200 px-1 py-0.5 font-mono dark:bg-neutral-700" >
            { modKeySymbol } + K
            </span>
    { " " } focar
        </span>
        < span >
        <span className="rounded bg-neutral-200 px-1 py-0.5 font-mono dark:bg-neutral-700" >
            { modKeySymbol } + N
            </span>
    { " " } nova
        </span>
        < span >
        <span className="rounded bg-neutral-200 px-1 py-0.5 font-mono dark:bg-neutral-700" >
            Enter
            </span>
    { " " } enviar
        </span>
        </span>
    );
}
