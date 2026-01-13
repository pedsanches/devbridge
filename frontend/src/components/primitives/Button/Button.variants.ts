import { cva, type VariantProps } from "class-variance-authority";

/**
 * Button Variants using CVA for consistent styling
 *
 * Follows 2025 design patterns:
 * - Gradient variants for CTAs
 * - Glass variant for glassmorphism
 * - Glow effect on hover for modern feel
 */
export const buttonVariants = cva(
    // Base styles
    [
        "inline-flex items-center justify-center gap-2",
        "whitespace-nowrap rounded-md text-sm font-medium",
        "transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        "active:scale-[0.98]",
    ],
    {
        variants: {
            variant: {
                default: [
                    "bg-primary text-white shadow-sm",
                    "hover:bg-primary-hover hover:shadow-md",
                ],
                secondary: [
                    "bg-neutral-100 text-neutral-900 shadow-sm",
                    "hover:bg-neutral-200/80",
                    "dark:bg-neutral-800 dark:text-neutral-50 dark:hover:bg-neutral-700",
                ],
                destructive: [
                    "bg-error text-white shadow-sm",
                    "hover:bg-error/90",
                ],
                outline: [
                    "border border-neutral-200 bg-transparent",
                    "hover:bg-neutral-100 hover:text-neutral-900",
                    "dark:border-neutral-700 dark:text-neutral-50 dark:hover:bg-neutral-800",
                ],
                ghost: [
                    "bg-transparent",
                    "hover:bg-neutral-100 hover:text-neutral-900",
                    "dark:hover:bg-neutral-800 dark:hover:text-neutral-50",
                ],
                link: [
                    "text-primary underline-offset-4",
                    "hover:underline",
                ],
                // New 2025 variants
                gradient: [
                    "bg-gradient-to-r from-primary to-indigo-500 text-white shadow-md",
                    "hover:opacity-90 hover:shadow-lg",
                ],
                glass: [
                    "bg-white/10 backdrop-blur-md border border-white/20 text-foreground",
                    "hover:bg-white/20",
                    "dark:bg-black/20 dark:border-white/10 dark:hover:bg-black/30",
                ],
                glow: [
                    "bg-primary text-white shadow-sm",
                    "hover:shadow-[0_0_20px_rgba(0,113,227,0.4)]",
                ],
            },
            size: {
                sm: "h-8 px-3 text-xs rounded-md",
                default: "h-9 px-4 py-2",
                lg: "h-11 px-6 text-base rounded-lg",
                xl: "h-12 px-8 text-base rounded-lg",
                icon: "h-9 w-9 p-0",
                "icon-sm": "h-8 w-8 p-0",
                "icon-lg": "h-11 w-11 p-0",
            },
        },
        defaultVariants: {
            variant: "default",
            size: "default",
        },
    }
);

export type ButtonVariants = VariantProps<typeof buttonVariants>;
