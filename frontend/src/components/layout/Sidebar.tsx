"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
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
    Users,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useSidebar } from "./SidebarContext";

interface NavItem {
    href:
    | "/dashboard"
    | "/teams"
    | "/metrics"
    | "/reports"
    | "/settings/data-sources";
    label: string;
    icon: React.ElementType;
    isHighlighted?: boolean | undefined;
}

const mainNavItems: NavItem[] = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/teams", label: "Times", icon: Users },
    { href: "/metrics", label: "Métricas", icon: BarChart3 },
    { href: "/reports", label: "Relatórios", icon: FileText },
];

const settingsNavItems: NavItem[] = [
    { href: "/settings/data-sources", label: "Configurações", icon: Settings },
];

// Custom hook to track pathname changes and auto-close sidebar
function useAutoCloseSidebar(pathname: string) {
    const [isMobileOpen, setIsMobileOpen] = useState(false);
    const [lastPathname, setLastPathname] = useState(pathname);

    // When pathname changes, close the sidebar
    if (pathname !== lastPathname) {
        setLastPathname(pathname);
        if (isMobileOpen) {
            setIsMobileOpen(false);
        }
    }

    return [isMobileOpen, setIsMobileOpen] as const;
}

export function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const { user, isAuthenticated, logout } = useAuth();
    const { isCollapsed, toggle } = useSidebar();
    const [isMobileOpen, setIsMobileOpen] = useAutoCloseSidebar(pathname);

    // Close mobile sidebar on escape key - this is a proper external subscription pattern
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") setIsMobileOpen(false);
        };
        document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, [setIsMobileOpen]);

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
            {/* Sidebar */}
            <aside
                className={`
                    fixed left-0 top-0 z-50 flex h-full flex-col
                    glass transition-all duration-300 ease-out
                    ${isCollapsed ? "w-16" : "w-64"}
                    ${isMobileOpen ? "translate-x-0" : "-translate-x-full"}
                    lg:translate-x-0
                `}
            >
                {/* Collapse/Expand Toggle (Desktop) - Floating */}
                <button
                    onClick={toggle}
                    className="hidden lg:flex absolute -right-3 top-6 z-50 h-6 w-6 items-center justify-center rounded-full border border-border bg-card shadow-md transition-colors hover:bg-accent hover:text-accent-foreground"
                    aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    {isCollapsed ? (
                        <ChevronRight className="h-3 w-3" />
                    ) : (
                        <ChevronLeft className="h-3 w-3" />
                    )}
                </button>

                {/* Header */}
                <div className="flex h-16 items-center px-4 border-b border-white/10 dark:border-white/5">
                    <Link
                        href="/dashboard"
                        className={`
                            flex items-center gap-3 transition-all duration-300
                            ${isCollapsed ? "justify-center w-full px-0" : ""}
                        `}
                    >
                        <div className={`
                            relative flex items-center justify-center rounded-xl overflow-hidden shadow-sm
                            ${isCollapsed ? "h-8 w-8" : "h-9 w-9"}
                            bg-white/90 ring-1 ring-white/20
                        `}>
                            <Image
                                src="/logo.png"
                                alt="DevBridge"
                                fill
                                className="object-cover object-top scale-125 translate-y-1"
                                priority
                            />
                        </div>

                        {!isCollapsed && (
                            <span className="font-heading text-[1.1rem] font-bold text-foreground tracking-tight whitespace-nowrap overflow-hidden animate-fade-in pl-1">
                                DevBridge
                            </span>
                        )}
                    </Link>

                    {/* Close button (Mobile) - Keep inline for mobile */}
                    <button
                        onClick={() => setIsMobileOpen(false)}
                        className="ml-auto rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:hidden"
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
    href:
    | "/chat"
    | "/dashboard"
    | "/teams"
    | "/metrics"
    | "/reports"
    | "/settings/data-sources";
    icon: React.ElementType;
    label: string;
    isActive: boolean;
    isCollapsed: boolean;
}

function NavLink({ href, icon: Icon, label, isActive, isCollapsed }: NavLinkProps) {
    return (
        <Link
            href={href}
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
