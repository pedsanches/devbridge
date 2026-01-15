"use client";

import Link, { type LinkProps } from "next/link";
import { useRouter } from "next/navigation";
import { MessageSquare, LayoutDashboard, LogOut, ChevronDown, User, ArrowLeft, Settings, FileText } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

interface HeaderProps {
    variant?: "default" | "minimal" | "auth" | undefined;
    backHref?: LinkProps["href"] | undefined;
    backLabel?: string | undefined;
}

export function Header({ variant = "default", backHref = "/", backLabel = "Voltar" }: HeaderProps) {
    const { user, isAuthenticated, isLoading, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);
    const router = useRouter();

    // Close menu when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleLogout = async () => {
        await logout();
        setIsMenuOpen(false);
        router.push("/");
    };

    // Auth variant: Just logo, centered or left-aligned
    if (variant === "auth") {
        return (
            <header className="sticky top-0 z-50 w-full border-b border-neutral-200 glass dark:border-neutral-800">
                <div className="container mx-auto flex h-16 items-center px-4">
                    <Link href="/" className="flex items-center gap-2 font-semibold">
                        <span className="text-xl text-primary">DevBridge</span>
                    </Link>
                </div>
            </header>
        );
    }

    // Unified Header (Default & Minimal combined)
    return (
        <header className="sticky top-0 z-50 w-full border-b border-neutral-200 glass dark:border-neutral-800">
            <div className="container mx-auto flex h-16 items-center justify-between px-4">
                <div className="flex items-center gap-4">
                    {/* Optional Back Button */}
                    {(variant === "minimal" || backHref !== "/") && (
                        <Link
                            href={backHref ?? "/"}
                            className="flex items-center gap-2 text-secondary hover:text-primary"
                        >
                            <ArrowLeft className="h-4 w-4" />
                            {variant === "minimal" && <span className="text-sm">{backLabel}</span>}
                        </Link>
                    )}

                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2 font-semibold">
                        <span className="text-xl text-primary">DevBridge</span>
                    </Link>
                </div>

                {/* Navigation & User Menu */}
                <nav className="flex items-center gap-4">
                    {isAuthenticated && (
                        <>
                            <Link
                                href="/dashboard"
                                className="flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-secondary transition-colors hover:bg-neutral-100 hover:text-primary dark:hover:bg-neutral-800"
                            >
                                <LayoutDashboard className="h-4 w-4" />
                                Dashboard
                            </Link>
                            <Link
                                href="/chat"
                                className="flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-secondary transition-colors hover:bg-neutral-100 hover:text-primary dark:hover:bg-neutral-800"
                            >
                                <MessageSquare className="h-4 w-4" />
                                Chat
                            </Link>
                            <Link
                                href="/reports"
                                className="flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-secondary transition-colors hover:bg-neutral-100 hover:text-primary dark:hover:bg-neutral-800"
                            >
                                <FileText className="h-4 w-4" />
                                Reports
                            </Link>
                        </>
                    )}

                    <ThemeToggle />

                    {/* Auth Section */}
                    {isLoading ? (
                        <div className="h-8 w-8 animate-pulse rounded-full bg-neutral-200 dark:bg-neutral-700" />
                    ) : isAuthenticated && user ? (
                        <div className="relative" ref={menuRef}>
                            <button
                                onClick={() => setIsMenuOpen(!isMenuOpen)}
                                className="flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-sm font-medium transition-colors hover:border-primary hover:bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-800 dark:hover:border-primary dark:hover:bg-neutral-700"
                            >
                                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-semibold text-white">
                                    {user.email?.charAt(0).toUpperCase() || "U"}
                                </div>
                                <span className="hidden max-w-[120px] truncate sm:block">
                                    {user.name || user.email?.split("@")[0] || "Usuário"}
                                </span>
                                <ChevronDown className={`h-4 w-4 transition-transform ${isMenuOpen ? "rotate-180" : ""}`} />
                            </button>

                            {/* Dropdown Menu */}
                            {isMenuOpen && (
                                <div className="absolute right-0 mt-2 w-56 rounded-lg border border-neutral-200 bg-white py-1 shadow-lg dark:border-neutral-700 dark:bg-neutral-800">
                                    <div className="border-b border-neutral-100 px-4 py-2 dark:border-neutral-700">
                                        <p className="text-sm font-medium text-neutral-900 dark:text-white">
                                            {user.name || "Usuário"}
                                        </p>
                                        <p className="truncate text-xs text-neutral-500">{user.email}</p>
                                    </div>
                                    <Link
                                        href="/settings/data-sources"
                                        onClick={() => setIsMenuOpen(false)}
                                        className="flex w-full items-center gap-2 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:bg-neutral-800"
                                    >
                                        <Settings className="h-4 w-4" />
                                        Data Sources
                                    </Link>
                                    <button
                                        onClick={handleLogout}
                                        className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                                    >
                                        <LogOut className="h-4 w-4" />
                                        Sair
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <Link
                            href="/login"
                            className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
                        >
                            <User className="h-4 w-4" />
                            Entrar
                        </Link>
                    )}
                </nav>
            </div>
        </header>
    );
}
