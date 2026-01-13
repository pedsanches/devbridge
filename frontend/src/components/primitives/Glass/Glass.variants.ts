import { cva, type VariantProps } from "class-variance-authority";

/**
 * Glass effect variants for glassmorphism UI elements
 *
 * Implements "Liquid Glass" design trend from 2025
 */
export const glassVariants = cva(
    [
        "backdrop-blur",
        "border rounded-lg",
        "transition-all duration-200",
    ],
    {
        variants: {
            intensity: {
                subtle: [
                    "bg-white/10 border-white/10 backdrop-blur-md", // Lighter
                    "dark:bg-[#0B0E14]/30 dark:border-white/5", // Very subtle in dark mode
                ],
                medium: [
                    "bg-white/20 border-white/20 backdrop-blur-lg",
                    "dark:bg-[#0B0E14]/50 dark:border-white/10", // Standard liquid feel
                ],
                strong: [
                    "bg-white/30 border-white/30 backdrop-blur-xl",
                    "dark:bg-[#0B0E14]/80 dark:border-white/15", // Deep glass
                ],
            },
            interactive: {
                true: "hover:bg-white/70 dark:hover:bg-black/60 cursor-pointer",
                false: "",
            },
            shadow: {
                none: "",
                sm: "shadow-sm",
                md: "shadow-md",
                lg: "shadow-lg",
                glow: "shadow-[0_0_20px_rgba(99,102,241,0.15)]",
            },
        },
        defaultVariants: {
            intensity: "medium",
            interactive: false,
            shadow: "sm",
        },
    }
);

export type GlassVariants = VariantProps<typeof glassVariants>;
