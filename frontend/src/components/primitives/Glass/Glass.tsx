import * as React from "react";
import { cn } from "@/lib/utils";
import { glassVariants, type GlassVariants } from "./Glass.variants";

export interface GlassProps
    extends React.HTMLAttributes<HTMLDivElement>,
    GlassVariants { }

/**
 * Glass container component for glassmorphism effects
 *
 * @example
 * <Glass intensity="strong" shadow="glow">
 *   <p>Content with glass effect</p>
 * </Glass>
 */
const Glass = React.forwardRef<HTMLDivElement, GlassProps>(
    ({ className, intensity, interactive, shadow, children, ...props }, ref) => {
        return (
            <div
                ref={ref}
                className={cn(
                    glassVariants({ intensity, interactive, shadow }),
                    className
                )}
                {...props}
            >
                {children}
            </div>
        );
    }
);
Glass.displayName = "Glass";

export { Glass };
