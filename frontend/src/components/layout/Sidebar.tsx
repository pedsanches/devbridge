"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
    MessageSquare,
    LayoutDashboard,
    BarChart3,
    FileText,
    Settings,
    ChevronLeft,
    ChevronRight,
    LogOut,
    X,
    Menu,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useSidebar } from "./SidebarContext";

interface NavItem {
    href: string;
    label: string;
    icon: React.ElementType;
    isHighlighted?: boolean;
}

const mainNavItems: NavItem[] = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/metrics", label: "Métricas", icon: BarChart3 },
    { href: "/reports", label: "Relatórios", icon: FileText },
];

const settingsNavItems: NavItem[] = [
    { href: "/settings/data-sources", label: "Configurações", icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const { user, isAuthenticated, logout } = useAuth();
    const { isCollapsed, toggle } = useSidebar();
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    // Close mobile sidebar on route change
    useEffect(() => {
        setIsMobileOpen(false);
    }, [pathname]);

    // Close mobile sidebar on escape key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") setIsMobileOpen(false);
        };
        document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, []);

    const handleLogout = async () => {
        await logout();
        router.push("/");
    };

    const handleNewChat = () => {
        router.push("/chat");
    };

    const isActive = (href: string) => {
        if (href === "/dashboard") return pathname === "/dashboard" || pathname === "/";
        return pathname.startsWith(href);
    };

    // Don't render sidebar on auth pages or landing page for non-authenticated users
    if (!isAuthenticated) return null;
    if (pathname === "/login" || pathname === "/auth/verify") return null;

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                onClick={() => setIsMobileOpen(true)}
                className="fixed left-4 top-4 z-40 rounded-lg border border-[var(--border)] bg-[var(--card)] p-2 shadow-md lg:hidden"
                aria-label="Open menu"
            >
                <Menu className="h-5 w-5 text-[var(--foreground)]" />
            </button>

            {/* Mobile Overlay */}
            {isMobileOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
                    onClick={() => setIsMobileOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
                    fixed left-0 top-0 z-50 flex h-full flex-col border-r border-[var(--border)] bg-[var(--card)]
                    transition-all duration-300 ease-out
                    ${isCollapsed ? "w-16" : "w-64"}
                    ${isMobileOpen ? "translate-x-0" : "-translate-x-full"}
                    lg:translate-x-0
                `}
            >
                {/* Header */}
                <div className="flex h-16 items-center justify-between border-b border-[var(--border)] px-4">
                    {!isCollapsed && (
                        <Link href="/dashboard" className="flex items-center gap-2">
                            <span className="text-xl font-semibold text-primary">DevBridge</span>
                        </Link>
                    )}

                    {/* Collapse/Expand Toggle (Desktop) */}
                    <button
                        onClick={toggle}
                        className="hidden rounded-lg p-1.5 text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)] hover:text-[var(--foreground)] lg:flex"
                        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {isCollapsed ? (
                            <ChevronRight className="h-4 w-4" />
                        ) : (
                            <ChevronLeft className="h-4 w-4" />
                        )}
                    </button>

                    {/* Close button (Mobile) */}
                    <button
                        onClick={() => setIsMobileOpen(false)}
                        className="rounded-lg p-1.5 text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)] hover:text-[var(--foreground)] lg:hidden"
                        aria-label="Close menu"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>

                {/* New Chat CTA */}
                <div className="p-3">
                    <button
                        onClick={handleNewChat}
                        data-onboarding="novo-chat"
                        className={`
                            flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 font-medium text-white
                            transition-all hover:bg-[var(--color-primary-hover)] hover:shadow-md
                            ${isCollapsed ? "px-2" : "px-4"}
                        `}
                    >
                        <MessageSquare className="h-4 w-4" />
                        {!isCollapsed && <span>Novo Chat</span>}
                    </button>
                </div>

                {/* Main Navigation */}
                <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
                    {/* Chat link */}
                    <NavLink
                        href="/chat"
                        icon={MessageSquare}
                        label="Chat"
                        isActive={isActive("/chat")}
                        isCollapsed={isCollapsed}
                    />

                    <div className="my-3 border-t border-[var(--border)]" />

                    {mainNavItems.map((item) => (
                        <NavLink
                            key={item.href}
                            href={item.href}
                            icon={item.icon}
                            label={item.label}
                            isActive={isActive(item.href)}
                            isCollapsed={isCollapsed}
                        />
                    ))}

                    <div className="my-3 border-t border-[var(--border)]" />

                    {settingsNavItems.map((item) => (
                        <NavLink
                            key={item.href}
                            href={item.href}
                            icon={item.icon}
                            label={item.label}
                            isActive={isActive(item.href)}
                            isCollapsed={isCollapsed}
                        />
                    ))}
                </nav>

                {/* User Section */}
                {user && (
                    <div className="border-t border-[var(--border)] p-3">
                        <div
                            className={`
                                flex items-center gap-3 rounded-lg p-2
                                ${isCollapsed ? "justify-center" : ""}
                            `}
                        >
                            {/* Avatar */}
                            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-white">
                                {user.email?.charAt(0).toUpperCase() || "U"}
                            </div>

                            {!isCollapsed && (
                                <div className="min-w-0 flex-1">
                                    <p className="truncate text-sm font-medium text-[var(--foreground)]">
                                        {user.name || user.email?.split("@")[0] || "Usuário"}
                                    </p>
                                    <p className="truncate text-xs text-[var(--muted-foreground)]">
                                        {user.email}
                                    </p>
                                </div>
                            )}
                        </div>

                        <button
                            onClick={handleLogout}
                            className={`
                                mt-2 flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-red-500
                                transition-colors hover:bg-red-50 dark:hover:bg-red-900/20
                                ${isCollapsed ? "justify-center" : ""}
                            `}
                        >
                            <LogOut className="h-4 w-4" />
                            {!isCollapsed && <span>Sair</span>}
                        </button>
                    </div>
                )}
            </aside>
        </>
    );
}

interface NavLinkProps {
    href: string;
    icon: React.ElementType;
    label: string;
    isActive: boolean;
    isCollapsed: boolean;
}

function NavLink({ href, icon: Icon, label, isActive, isCollapsed }: NavLinkProps) {
    return (
        <Link
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            href={href as any}
            className={`
                group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium
                transition-all duration-200
                ${isActive
                    ? "bg-primary/10 text-primary"
                    : "text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)]"
                }
                ${isCollapsed ? "justify-center px-2" : ""}
            `}
            title={isCollapsed ? label : undefined}
        >
            <Icon className={`h-4 w-4 flex-shrink-0 ${isActive ? "text-primary" : ""}`} />
            {!isCollapsed && <span>{label}</span>}

            {/* Active indicator */}
            {isActive && !isCollapsed && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
            )}
        </Link>
    );
}
