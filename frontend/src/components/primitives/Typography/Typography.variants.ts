import { cva, type VariantProps } from "class-variance-authority";

/**
 * Typography variants for consistent text styling
 */
export const headingVariants = cva(
    "font-heading tracking-tight text-foreground",
    {
        variants: {
            level: {
                h1: "text-4xl font-bold leading-tight",
                h2: "text-3xl font-semibold leading-tight",
                h3: "text-2xl font-semibold",
                h4: "text-xl font-medium",
                h5: "text-lg font-medium",
                h6: "text-base font-medium",
            },
        },
        defaultVariants: {
            level: "h2",
        },
    }
);

export const textVariants = cva("", {
    variants: {
        variant: {
            default: "text-foreground",
            muted: "text-muted-foreground",
            primary: "text-primary",
            success: "text-success",
            warning: "text-warning",
            error: "text-error",
        },
        size: {
            xs: "text-xs",
            sm: "text-sm",
            base: "text-base",
            lg: "text-lg",
            xl: "text-xl",
        },
        weight: {
            normal: "font-normal",
            medium: "font-medium",
            semibold: "font-semibold",
            bold: "font-bold",
        },
    },
    defaultVariants: {
        variant: "default",
        size: "base",
        weight: "normal",
    },
});

export type HeadingVariants = VariantProps<typeof headingVariants>;
export type TextVariants = VariantProps<typeof textVariants>;
