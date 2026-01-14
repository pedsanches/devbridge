"use client";

import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";
import { PageHeader } from "./PageHeader";

const pageLayoutVariants = cva(
    "flex min-h-screen flex-col bg-[var(--background)]",
    {
        variants: {
            /** No variants for outer wrapper currently */
        },
    }
);

const pageContainerVariants = cva(
    "container mx-auto px-4",
    {
        variants: {
            maxWidth: {
                default: "max-w-6xl",
                wide: "max-w-7xl",
                full: "",
                narrow: "max-w-4xl",
            },
            padding: {
                default: "py-8",
                compact: "py-4",
                spacious: "py-12",
            },
        },
        defaultVariants: {
            maxWidth: "default",
            padding: "default",
        },
    }
);

export interface PageLayoutProps extends VariantProps<typeof pageContainerVariants> {
    /** Page title */
    title: React.ReactNode;
    /** Optional subtitle */
    subtitle?: string;
    /** Optional Lucide icon for header */
    icon?: LucideIcon;
    /** Optional action element for header (right side) */
    headerAction?: React.ReactNode;
    /** Page content */
    children: React.ReactNode;
    /** Additional className for the container */
    containerClassName?: string;
    /** Optional className for the outer wrapper */
    className?: string;
    /** Whether to show the header (default: true) */
    showHeader?: boolean;
}

/**
 * PageLayout - Unified page wrapper component.
 *
 * Provides consistent structure for all authenticated pages:
 * - Full-height background
 * - Constrained container with responsive padding
 * - Integrated PageHeader
 *
 * @example
 * ```tsx
 * <PageLayout
 *   title="Métricas"
 *   subtitle="Acompanhe a performance do seu time"
 *   icon={BarChart3}
 *   headerAction={<TeamSelector />}
 *   maxWidth="default"
 * >
 *   <MetricsContent />
 * </PageLayout>
 * ```
 */
export function PageLayout({
    title,
    subtitle,
    icon,
    headerAction,
    children,
    maxWidth,
    padding,
    className,
    containerClassName,
    showHeader = true,
}: PageLayoutProps) {
    return (
        <div className={cn(pageLayoutVariants(), className)}>
            <main className="flex-1">
                <div className={cn(pageContainerVariants({ maxWidth, padding }), containerClassName)}>
                    {showHeader && (
                        <PageHeader
                            title={title}
                            subtitle={subtitle}
                            icon={icon}
                            action={headerAction}
                        />
                    )}
                    {children}
                </div>
            </main>
        </div>
    );
}

export { pageLayoutVariants, pageContainerVariants };
