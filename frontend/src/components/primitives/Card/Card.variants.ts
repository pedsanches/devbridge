import { cva, type VariantProps } from "class-variance-authority";

/**
 * Card Variants with modern 2025 styling
 */
export const cardVariants = cva(
    "rounded-xl border bg-card text-card-foreground shadow-sm transition-all duration-300",
    {
        variants: {
            variant: {
                default: "border-border/50",
                glass: "glass border-transparent",
                "glass-panel": "glass-panel border-transparent",
                subtle: "bg-muted/50 border-transparent",
                gradient: "bg-gradient-to-br from-card to-muted border-border/50",
            },
            hoverable: {
                true: "hover-lift cursor-pointer hover:border-primary/20",
                false: "",
            },
            padding: {
                none: "",
                sm: "p-4",
                md: "p-6",
                lg: "p-8",
            },
        },
        defaultVariants: {
            variant: "default",
            hoverable: false,
            padding: "none", // Default is none to let subcomponents handle padding or user add it
        },
    }
);

export type CardVariants = VariantProps<typeof cardVariants>;
