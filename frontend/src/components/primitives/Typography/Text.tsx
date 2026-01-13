import * as React from "react";
import { cn } from "@/lib/utils";
import { textVariants, type TextVariants } from "./Typography.variants";

export interface TextProps
    extends React.HTMLAttributes<HTMLSpanElement>,
    TextVariants {
    /** Render as different element */
    as?: "span" | "p" | "div" | "label" | undefined;
}

/**
 * Text component for body text with consistent styling
 *
 * @example
 * <Text variant="muted" size="sm">Secondary text</Text>
 * <Text as="p" weight="medium">Paragraph text</Text>
 */
const Text = React.forwardRef<HTMLSpanElement, TextProps>(
    (
        { className, variant, size, weight, as = "span", children, ...props },
        ref
    ) => {
        const Component = as;

        return React.createElement(
            Component,
            {
                ref,
                className: cn(textVariants({ variant, size, weight }), className),
                ...props,
            },
            children
        );
    }
);
Text.displayName = "Text";

export { Text };
