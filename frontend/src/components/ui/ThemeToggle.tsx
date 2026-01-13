"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

// Subscribe to nothing - we just want to detect hydration
const emptySubscribe = () => () => { };
const getSnapshot = () => true;
const getServerSnapshot = () => false;

export function ThemeToggle() {
    const { setTheme, resolvedTheme } = useTheme();

    // Use useSyncExternalStore to handle hydration without triggering the lint rule
    const mounted = useSyncExternalStore(emptySubscribe, getSnapshot, getServerSnapshot);

    if (!mounted) {
        return (
            <button
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-neutral-200 bg-white text-neutral-600 transition-colors dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400"
                aria-label="Alternar tema"
            >
                <div className="h-4 w-4" />
            </button>
        );
    }

    const isDark = resolvedTheme === "dark";

    return (
        <button
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-neutral-200 bg-white text-neutral-600 transition-all hover:border-primary hover:text-primary dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400 dark:hover:border-primary dark:hover:text-primary"
            aria-label={isDark ? "Mudar para modo claro" : "Mudar para modo escuro"}
        >
            {isDark ? (
                <Sun className="h-4 w-4" />
            ) : (
                <Moon className="h-4 w-4" />
            )}
        </button>
    );
}
