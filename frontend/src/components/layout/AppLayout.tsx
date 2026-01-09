"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { Sidebar } from "./Sidebar";
import { SidebarProvider, useSidebar } from "./SidebarContext";
import { Header } from "./Header";
import { OnboardingTooltip } from "@/components/onboarding";

interface AppLayoutProps {
    children: React.ReactNode;
}

/**
 * AppLayout handles the conditional rendering of navigation:
 * - Landing page (/): Shows old header for non-authenticated users
 * - Auth pages (/login, /auth/verify): Shows minimal header
 * - Authenticated app pages: Shows sidebar layout
 */
export function AppLayout({ children }: AppLayoutProps) {
    const pathname = usePathname();
    const { isAuthenticated } = useAuth();

    // Auth pages - minimal header only
    const isAuthPage = pathname === "/login" || pathname === "/auth/verify";
    if (isAuthPage) {
        return (
            <>
                <Header variant="auth" />
                {children}
            </>
        );
    }

    // Landing page for non-authenticated users - show classic header
    const isLandingPage = pathname === "/";
    if (isLandingPage && !isAuthenticated) {
        return (
            <>
                <Header variant="default" />
                {children}
            </>
        );
    }

    // Authenticated users - show sidebar layout with provider
    if (isAuthenticated) {
        return (
            <SidebarProvider>
                <AuthenticatedLayout>{children}</AuthenticatedLayout>
            </SidebarProvider>
        );
    }

    // Fallback for non-authenticated users on other pages
    return (
        <>
            <Header variant="default" />
            {children}
        </>
    );
}

/**
 * Inner layout component that has access to SidebarContext
 */
function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
    const { isCollapsed } = useSidebar();

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main
                className={`
                    flex-1 transition-all duration-300
                    ${isCollapsed ? "lg:ml-16" : "lg:ml-64"}
                `}
            >
                {children}
            </main>
            <OnboardingTooltip />
        </div>
    );
}
