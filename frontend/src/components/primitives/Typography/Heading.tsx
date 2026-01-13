import * as React from "react";
import { cn } from "@/lib/utils";
import { headingVariants, type HeadingVariants } from "./Typography.variants";

type HeadingLevel = "h1" | "h2" | "h3" | "h4" | "h5" | "h6";

export interface HeadingProps
    extends React.HTMLAttributes<HTMLHeadingElement>,
    HeadingVariants {
    /** The heading level (h1-h6) - determines both semantic element and styling */
    as?: HeadingLevel | undefined;
}

/**
 * Heading component with semantic HTML and consistent styling
 *
 * @example
 * <Heading level="h1">Page Title</Heading>
 * <Heading level="h2" as="h3">Section Title (styled as h2)</Heading>
 */
const Heading = React.forwardRef<HTMLHeadingElement, HeadingProps>(
    ({ className, level = "h2", as, children, ...props }, ref) => {
        const Component = as ?? level ?? "h2";

        return React.createElement(
            Component,
            {
                ref,
                className: cn(headingVariants({ level }), className),
                ...props,
            },
            children
        );
    }
);
Heading.displayName = "Heading";

export { Heading };
