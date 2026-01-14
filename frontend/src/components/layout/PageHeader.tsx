"use client";

import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

const pageHeaderVariants = cva(
    "mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between",
    {
        variants: {
            spacing: {
                default: "mb-6",
                compact: "mb-4",
                spacious: "mb-8",
            },
        },
        defaultVariants: {
            spacing: "default",
        },
    }
);

export interface PageHeaderProps extends VariantProps<typeof pageHeaderVariants> {
    /** Page title - can be string or ReactNode for custom rendering */
    title: React.ReactNode;
    /** Optional subtitle describing the page */
    subtitle?: string | undefined;
    /** Optional Lucide icon to display before title */
    icon?: LucideIcon | undefined;
    /** Optional action element (buttons, selectors, etc.) */
    action?: React.ReactNode | undefined;
    /** Optional className for the container */
    className?: string | undefined;
}

/**
 * PageHeader - Unified header component for all pages.
 *
 * Provides consistent heading structure with:
 * - Icon + Title
 * - Subtitle
 * - Action slot for controls
 *
 * @example
 * ```tsx
 * <PageHeader
 *   title="Métricas"
 *   subtitle="Acompanhe a performance do seu time"
 *   icon={BarChart3}
 *   action={<TeamSelector />}
 * />
 * ```
 */
export function PageHeader({
    title,
    subtitle,
    icon: Icon,
    action,
    spacing,
    className,
    ...props
}: PageHeaderProps) {
    return (
        <div className={cn(pageHeaderVariants({ spacing }), className)} {...props}>
            <div>
                <h1 className="flex items-center gap-3 text-2xl font-semibold tracking-tight text-[var(--foreground)]">
                    {Icon && <Icon className="h-6 w-6" />}
                    {title}
                </h1>
                {subtitle && (
                    <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                        {subtitle}
                    </p>
                )}
            </div>
            {action && (
                <div className="flex items-center gap-3">
                    {action}
                </div>
            )}
        </div>
    );
}

export { pageHeaderVariants };
